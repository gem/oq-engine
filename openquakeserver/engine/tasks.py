# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013, GEM Foundation.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/agpl.html>.

import sys
import traceback
import logging
import collections
import shutil
import tempfile
import psycopg2
import urllib
import urllib2

from celery.task import task

from openquake.engine import engine
from openquake.engine.db import models as oqe_models

from openquakeserver.dbsettings import PLATFORM_DATABASES as DATABASES


DEFAULT_LOG_LEVEL = 'progress'


# FIXME. Configure logging by using the configuration stored in settings
logger = logging.getLogger(__name__)


@task(ignore_result=True)
def run_calc(calc_type, calc_id, calc_dir,
             callback_url=None, foreign_calc_id=None,
             dbname="platform"):
    """
    Run a calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute.

    :param calc_type: 'hazard' or 'risk'
    """
    job = oqe_models.OqJob.objects.get(hazard_calculation=calc_id)

    update_calculation(callback_url, status="started", engine_id=calc_id)
    exports = []
    # TODO: Log to file somewhere. But where?
    log_file = None

    def progress_handler(status, calculation):
        update_calculation(
            callback_url,
            status=status,
            description=calculation.description)

    try:
        engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, exports, calc_type,
                        progress_handler=progress_handler)
    except:
        exctype, exc, tb = sys.exc_info()
        einfo = '%s: %s\n%s' % (exctype.__name__, exc,
                                ''.join(traceback.format_tb(tb)))
        update_calculation(callback_url, status="failed", einfo=einfo)
        return

    shutil.rmtree(calc_dir)

    # If requested to, signal job completion and trigger a migration of
    # results.
    if not None in (callback_url, foreign_calc_id):
        _trigger_migration(job, callback_url, foreign_calc_id, dbname)


def _trigger_migration(job, callback_url, foreign_calc_id, dbname="platform"):
    """
    Helper function to initiate a post-calculation migration of results.

    :param OqJob job:
        The job with which the calculation has been run
    :param str callback_url:
        A URL to POST a request to for pulling results out of the
        oq-engine-server.
    :param str foreign_calc_id:
        The id of the foreign calculation
    :param str dbname:
        a key to extract database connection settings from settings.DATABASES
        in order to get a cursor from the platform database
    """

    update_calculation(
        callback_url,
        description=job.calculation.description,
        status="transfering outputs")

    platform_connection = psycopg2.connect(
        host=DATABASES[dbname]['HOST'],
        database=DATABASES[dbname]['NAME'],
        user=DATABASES[dbname]['USER'],
        password=DATABASES[dbname]['PASSWORD'],
        port=DATABASES[dbname]['PORT'])

    for output in job.output_set.all():
        copy_output(platform_connection, output, foreign_calc_id)
    update_calculation(callback_url, status="creating layers")
    platform_connection.close()


def update_calculation(callback_url=None, **query):
    """
    Update a foreign calculation by POSTing `query` data to
    `callback_url`.
    """

    if callback_url is None:
        return

    if query:
        data = urllib.urlencode(query)
    else:
        data = ""

    try:
        # post to an external service, asking it to finalize
        # calculation results
        url = urllib2.urlopen(callback_url, data=data)
    except urllib2.HTTPError as e:
        # TODO: better logging/signalling of such an error?
        print e.code, e.reason
        raise
    else:
        url.close()


#: Simple structure that holds all the query components needed to
#transfer calculation outputs from the engine database to the platform
#one
DbInterface = collections.namedtuple(
    'DbInterface',
    'export_query target_table fields import_query')


DBINTERFACE = {
    'hazard_curve': DbInterface(
        """SELECT ST_AsText(location) as location, imls, poes
            FROM hzrdr.hazard_curve_data
            JOIN hzrdr.hazard_curve hc ON hc.id = hazard_curve_id
            JOIN uiapi.output o ON o.id = hc.output_id
            WHERE o.id = %(output_id)d""",
        "icebox_hazardcurve",
        "location varchar, imls float[], poes float[]",
        """INSERT INTO
           icebox_hazardcurve(output_layer_id, location, imls, poes)
           SELECT %s, ST_GeomFromText(location, 4326), imls, poes
           FROM temp_icebox_hazardcurve"""),
    'hazard_map': DbInterface(
        """SELECT unnest(lons) as longitude, unnest(lats) as latitude,
                  unnest(imls)
           FROM hzrdr.hazard_map
           JOIN uiapi.output o ON o.id = output_id
            WHERE o.id = %(output_id)d""",
        "icebox_hazardmap",
        "longitude float, latitude float, iml float",
        """INSERT INTO
           icebox_hazardmap(output_layer_id, iml, location)
           SELECT %s, iml, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
           FROM temp_icebox_hazardmap"""),
    'ses': DbInterface(
        """SELECT tag, magnitude, St_AsText(hypocenter)
           FROM hzrdr.ses_rupture r
           JOIN hzrdr.ses ses ON ses.id = r.ses_id
           JOIN hzrdr.ses_collection sc ON ses.ses_collection_id = sc.id
           JOIN uiapi.output o ON o.id = sc.output_id
           WHERE o.id = %(output_id)d""",
        "icebox_ses",
        "tag varchar, magnitude float, hypocenter varchar",
        """INSERT INTO
           icebox_ses(output_layer_id, hypocenter, rupture_tag, magnitude)
           SELECT %s, St_GeomFromText(hypocenter, 4326), tag, magnitude
           FROM temp_icebox_ses"""),
    # TODO: instead of the region_constraint, we should specify the convex
    # hull of the exposure
    'aggregate_loss': DbInterface(
        """SELECT St_AsText(region_constraint), mean, std_dev
           FROM riskr.aggregate_loss al
           JOIN uiapi.output o ON o.id = al.output_id
           JOIN uiapi.risk_calculation rc ON rc.id = %(calculation_id)d
           WHERE o.id = %(output_id)d""",
        "icebox_aggregateloss",
        "region varchar, mean_loss float, stddev_loss float",
        """INSERT INTO
           icebox_aggregateloss(
               output_layer_id, region, mean_loss, stddev_loss)
           SELECT %s, St_GeomFromText(region, 4326), mean_loss, stddev_loss
           FROM temp_icebox_aggregateloss"""),
    'agg_loss_curve': DbInterface(
        """SELECT ST_AsText(region_constraint) as region, losses, poes,
                  average_loss, stddev_loss
           FROM riskr.aggregate_loss_curve_data
           JOIN riskr.loss_curve lc ON lc.id = loss_curve_id
           JOIN uiapi.output o ON o.id = lc.output_id
           JOIN uiapi.risk_calculation rc ON rc.id = %(calculation_id)d
           WHERE o.id = %(output_id)d""",
        "icebox_aggregatelosscurve",
        ("region varchar, losses float[], poes float[], "
         "average_loss float, stddev_loss float"),
        """INSERT INTO icebox_aggregatelosscurve(
               output_layer_id, region, losses, poes, mean_loss, stddev_loss)
           SELECT %s, St_GeomFromText(region, 4326),
                  losses, poes, average_loss, stddev_loss
           FROM temp_icebox_aggregatelosscurve"""),
    'loss_curve': DbInterface(
        """SELECT ST_AsText(location) as location,
                  loss_ratios, poes, average_loss_ratio, stddev_loss_ratio,
                  asset_ref
           FROM riskr.loss_curve_data
           JOIN riskr.loss_curve lc ON lc.id = loss_curve_id
           JOIN uiapi.output o ON o.id = lc.output_id
           WHERE o.id = %(output_id)d""",
        "icebox_losscurve",
        ("location varchar, losses float[], poes float[], "
         "average_loss float, stddev_loss float, asset_ref varchar"),
        """INSERT INTO icebox_losscurve(
               output_layer_id, location, losses, poes,
               average_loss, stddev_loss, asset_ref)
           SELECT %s, St_GeomFromText(location, 4326),
                  losses, poes, average_loss, stddev_loss, asset_ref
           FROM temp_icebox_losscurve"""),
    'loss_map': DbInterface(
        """SELECT ST_AsText(location) as location,
                  value, std_dev, asset_ref
           FROM riskr.loss_map_data
           JOIN riskr.loss_map lm ON lm.id = loss_map_id
           JOIN uiapi.output o ON o.id = lm.output_id
           WHERE o.id = %(output_id)d""",
        "icebox_lossmap",
        "location varchar, loss float, stddev_loss float, asset_ref varchar",
        """INSERT INTO icebox_lossmap(
               output_layer_id, location, loss, stddev_loss, asset_ref)
           SELECT %s, St_GeomFromText(location, 4326),
                  loss, stddev_loss, asset_ref
           FROM temp_icebox_lossmap"""),
    'bcr_distribution': DbInterface(
        """SELECT ST_AsText(location) as location,
                  average_annual_loss_original,
                  average_annual_loss_retrofitted,
                  bcr,
                  asset_ref
           FROM riskr.bcr_distribution_data
           JOIN riskr.bcr_distribution bd ON bd.id = bcr_distribution_id
           JOIN uiapi.output o ON o.id = bd.output_id
           WHERE o.id = %(output_id)d""",
        "icebox_bcrdistribution",
        ("location varchar, average_annual_loss_original float, "
         "average_annual_loss_retrofitted float, bcr float, "
         "asset_ref varchar"),
        """INSERT INTO icebox_bcrdistribution(
               output_layer_id, location,
               average_annual_loss_original,
               average_annual_loss_retrofitted, bcr, asset_ref)
           SELECT %s, St_GeomFromText(location, 4326),
                  average_annual_loss_original,
                  average_annual_loss_retrofitted, bcr, asset_ref
           FROM temp_icebox_bcrdistribution"""),
}


def copy_output(platform_connection, output, foreign_calculation_id):
    """
    Copy `output` data from the engine database to the platform one.

    :param platform_connection: a psycopg2 connection handler
    :param output: a :class:`openquake.engine.db.models.Output` object
    :param foreign_calculation_id: the id of the foreign (platform) calculation
    """

    # the workflow is the following:
    # 1) Insert a pointer to the output into the output_layer table
    # 2) Create a temporary table on the platform
    # 3) Copy data from the engine to a temporary file
    # 4) Copy data to the temporary table from the temporary file
    # 5) Move data from the temporary table to the persistent one
    #    by considering foreign key issues
    engine_cursor = oqe_models.getcursor('admin')
    platform_cursor = platform_connection.cursor()

    with tempfile.TemporaryFile() as temporary_file:
        try:
            platform_cursor.execute(
                """INSERT INTO
                   icebox_outputlayer(display_name, calculation_id, engine_id)
                   VALUES(%s, %s, %s) RETURNING id""",
                (output.display_name, foreign_calculation_id, output.id))

            [[output_layer_id]] = platform_cursor.fetchall()

            iface = DBINTERFACE.get(output.output_type)

            if iface is None:
                # FIXME. Implement proper logging
                print "Output type %s not supported" % output.output_type
                return

            # FIXME() in a celery task I can not spawn threads. How
            # can i build a pipe?
            logger.info("Copying to temporary stream")
            engine_cursor.copy_expert(
                """COPY (%s) TO STDOUT
                   WITH (FORMAT 'csv', HEADER true,
                         ENCODING 'utf8', DELIMITER '|')""" % (
                iface.export_query % {
                    'output_id': output.id,
                    'calculation_id': output.oq_job.calculation.id}),
                temporary_file)

            temporary_file.seek(0)

            temp_table = "temp_%s" % iface.target_table
            platform_cursor.execute("DROP TABLE IF EXISTS %s" % temp_table)
            platform_cursor.execute("CREATE TABLE %s(%s)" % (
                temp_table, iface.fields))

            import_query = """COPY %s FROM STDIN
                              WITH (FORMAT 'csv',
                                    HEADER true,
                                    ENCODING 'utf8',
                                    DELIMITER '|')""" % temp_table
            logger.info("Copying from temporary stream")
            platform_cursor.copy_expert(import_query, temporary_file)

            platform_cursor.execute(iface.import_query % output_layer_id)
            platform_cursor.execute("DROP TABLE IF EXISTS %s" % temp_table)
        except Exception as e:
            # FIXME. Implement proper logging
            print str(e)
            platform_connection.rollback()
            raise
        else:
            platform_connection.commit()
