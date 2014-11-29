# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions for exporting risk artifacts from the database.
"""

import os
import csv

from openquake.engine.db import models
from openquake.engine.export import core
from openquake.engine.utils import FileWrapper
from openquake.commonlib import risk_writers

LOSS_CURVE_FILENAME_FMT = 'loss-curves-%(loss_curve_id)s.xml'
LOSS_MAP_FILENAME_FMT = 'loss-maps-%(loss_map_id)s.%(file_ext)s'
LOSS_FRACTION_FILENAME_FMT = 'loss-fractions-%(loss_fraction_id)s.xml'
AGGREGATE_LOSS_FILENAME_FMT = 'aggregate-loss-%s.csv'
BCR_FILENAME_FMT = 'bcr-distribution-%(bcr_distribution_id)s.xml'
EVENT_LOSS_FILENAME_FMT = 'event-loss-%s.csv'
EVENT_LOSS_ASSET_FILENAME_FMT = 'event-loss-asset-%s.csv'


DAMAGE = dict(
    collapse_map=models.DmgDistPerAsset,
    dmg_dist_per_asset=models.DmgDistPerAsset,
    dmg_dist_per_taxonomy=models.DmgDistPerTaxonomy,
    dmg_dist_total=models.DmgDistTotal)


def _get_result_export_dest(target, output, file_ext='xml'):
    """
    Get the full absolute path (including file name) for a given ``result``.

    As a side effect, intermediate directories are created such that the file
    can be created and written to immediately.

    :param target:
        Destination directory location for exported files OR a file-like
        object. If file-like, we just simply return it.
    :param output:
        :class:`~openquake.engine.db.models.Output`.
    :param file_ext:
        Desired file extension for the output file.
        Defaults to 'xml'.

    :returns:
        Full path (including filename) to the destination export file.
        If the ``target`` is a file-like, we don't do anything special
        and simply return it.
    """
    if not isinstance(target, basestring):
        # It's not a file path. In this case, we expect a file-like object.
        # Just return it.
        return target

    output_type = output.output_type

    filename = None

    if output_type in ('loss_curve', 'agg_loss_curve', 'event_loss_curve'):
        filename = LOSS_CURVE_FILENAME_FMT % dict(
            loss_curve_id=output.loss_curve.id,
        )
    elif output_type == 'loss_map':
        filename = LOSS_MAP_FILENAME_FMT % dict(
            loss_map_id=output.loss_map.id,
            file_ext=file_ext,
        )
    elif output_type == 'loss_fraction':
        filename = LOSS_FRACTION_FILENAME_FMT % dict(
            loss_fraction_id=output.loss_fraction.id,
        )
    elif output_type == 'bcr_distribution':
        filename = BCR_FILENAME_FMT % dict(
            bcr_distribution_id=output.bcr_distribution.id,
        )
    elif output_type == 'event_loss':
        filename = EVENT_LOSS_FILENAME_FMT % output.id
    elif output_type == 'event_loss_asset':
        filename = EVENT_LOSS_ASSET_FILENAME_FMT % output.id
    elif output_type == 'aggregate_loss':
        filename = AGGREGATE_LOSS_FILENAME_FMT % (output.aggregate_loss.id)
    elif output_type in ('dmg_dist_per_asset', 'dmg_dist_per_taxonomy',
                         'dmg_dist_total', 'collapse_map'):
        filename = '%(output_type)s-%(job_id)s.%(file_ext)s' % dict(
            output_type=output_type,
            job_id=output.oq_job.id,
            file_ext=file_ext,
        )

    return os.path.abspath(os.path.join(target, filename))


def _export_common(output, loss_type):
    """
    Returns a dict containing the output metadata which are serialized
    by nrml writers before actually writing the `output` data.
    """
    metadata = output.hazard_metadata
    if metadata.sm_path is not None:
        source_model_tree_path = core.LT_PATH_JOIN_TOKEN.join(
            metadata.sm_path)
    else:
        source_model_tree_path = None
    if metadata.gsim_path is not None:
        gsim_tree_path = core.LT_PATH_JOIN_TOKEN.join(metadata.gsim_path)
    else:
        gsim_tree_path = None

    return dict(investigation_time=metadata.investigation_time,
                statistics=metadata.statistics,
                quantile_value=metadata.quantile,
                source_model_tree_path=source_model_tree_path,
                gsim_tree_path=gsim_tree_path,
                unit=output.oq_job.risk_calculation.exposure_model.unit(
                    loss_type),
                loss_type=loss_type)


@core.export_output.add(('agg_loss_curve', 'xml'))
def export_agg_loss_curve_xml(key, output, target):
    """
    Export `output` to `target` by using a nrml loss curves
    serializers
    """
    args = _export_common(output, output.loss_curve.loss_type)
    dest = _get_result_export_dest(target, output)
    risk_writers.AggregateLossCurveXMLWriter(dest, **args).serialize(
        output.loss_curve.aggregatelosscurvedata)
    return dest


@core.export_output.add(('loss_curve', 'xml'), ('event_loss_curve', 'xml'))
def export_loss_curve_xml(key, output, target):
    """
    Export `output` to `target` by using a nrml loss curves
    serializer
    """
    args = _export_common(output, output.loss_curve.loss_type)
    dest = _get_result_export_dest(target, output)
    args['insured'] = output.loss_curve.insured

    data = output.loss_curve.losscurvedata_set.all().order_by('asset_ref')

    risk_writers.LossCurveXMLWriter(dest, **args).serialize(data)
    return dest


@core.export_output.add(('loss_map', 'xml'), ('loss_map', 'geojson'))
def export_loss_map(key, output, target):
    """
    General loss map export code.
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.loss_map.loss_type)
    dest = _get_result_export_dest(target, output, file_ext=key[1])
    args.update(dict(
        poe=output.loss_map.poe,
        loss_category=risk_calculation.exposure_model.category))

    writercls = (risk_writers.LossMapXMLWriter if key[1] == 'xml'
                 else risk_writers.LossMapGeoJSONWriter)
    writercls(dest, **args).serialize(
        models.order_by_location(
            output.loss_map.lossmapdata_set.all().order_by('asset_ref')))
    return dest


@core.export_output.add(('loss_fraction', 'xml'))
def export_loss_fraction_xml(key, output, target):
    """
    Export `output` to `target` by using a nrml loss fractions
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.loss_fraction.loss_type)
    hazard_metadata = models.Output.HazardMetadata(
        investigation_time=args['investigation_time'],
        statistics=args['statistics'],
        quantile=args.get('quantile_value'),
        sm_path=args['source_model_tree_path'],
        gsim_path=args['gsim_tree_path'])
    dest = _get_result_export_dest(target, output)
    poe = output.loss_fraction.poe
    variable = output.loss_fraction.variable
    loss_category = risk_calculation.exposure_model.category
    risk_writers.LossFractionsWriter(
        dest, variable, args['unit'], args['loss_type'],
        loss_category, hazard_metadata, poe).serialize(
        output.loss_fraction.total_fractions(),
        output.loss_fraction)
    return dest


@core.export_output.add(('bcr_distribution', 'xml'))
def export_bcr_distribution_xml(key, output, target):
    """
    Export `output` to `target` by using a nrml bcr distribution
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.bcr_distribution.loss_type)

    dest = _get_result_export_dest(target, output)
    args.update(
        dict(interest_rate=risk_calculation.interest_rate,
             asset_life_expectancy=risk_calculation.asset_life_expectancy))
    del args['investigation_time']

    risk_writers.BCRMapXMLWriter(dest, **args).serialize(
        output.bcr_distribution.bcrdistributiondata_set.all().order_by(
            'asset_ref'))
    return dest


# clearly this is not a good approach for large exposures
@core.export_output.add(('collapse_map', 'xml'),
                        ('dmg_dist_per_taxonomy', 'xml'),
                        ('dmg_dist_per_asset', 'xml'),
                        ('dmg_dist_total', 'xml'))
def export_dmg_dist(key, output, target):
    """
    Export the damage distribution identified
    by the given output to the `target`.

    :param output:
        DB output record which identifies the distribution. A
        :class:`openquake.engine.db.models.Output` object.
    :param target:
        Destination directory of the exported file, or a file-like object
    """
    job = output.oq_job
    dest = _get_result_export_dest(target, output)
    damage_states = list(models.DmgState.objects.filter(
        risk_calculation__id=job.id).order_by('lsi'))
    writer = risk_writers.DamageWriter(damage_states)
    damagecls = DAMAGE[key[0]]
    if key[0] == 'collapse_map':
        data = damagecls.objects.filter(dmg_state=damage_states[-1])
    else:
        data = damagecls.objects.filter(dmg_state__risk_calculation__id=job.id)
    writer.to_nrml(key[0], data, dest)
    return dest


@core.export_output.add(('aggregate_loss', 'csv'))
def export_aggregate_loss_csv(key, output, target):
    """
    Export aggregate losses in CSV
    """
    dest = _get_result_export_dest(target, output)

    with FileWrapper(dest, mode='wb') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['Mean', 'Standard Deviation'])
        writer.writerow([output.aggregate_loss.mean,
                        output.aggregate_loss.std_dev])
    return dest


@core.export_output.add(('event_loss', 'csv'))
def export_event_loss_csv(key, output, target):
    """
    Export Event Loss Table in CSV format
    """

    dest = _get_result_export_dest(target, output)

    with FileWrapper(dest, mode='wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Rupture', 'Magnitude', 'Aggregate Loss'])

        for event_loss in models.EventLossData.objects.filter(
                event_loss__output=output).select_related().order_by(
                '-aggregate_loss'):
            writer.writerow([event_loss.rupture.tag,
                             "%.07f" % event_loss.rupture.rupture.magnitude,
                             "%.07f" % event_loss.aggregate_loss])
    return dest


@core.export_output.add(('event_loss_asset', 'csv'))
def export_event_loss_asset_csv(key, output, target):
    """
    Export Event Loss Per Asset in CSV format
    """
    dest = _get_result_export_dest(target, output)

    with FileWrapper(dest, mode='wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Rupture', 'Asset', 'Magnitude', 'Loss'])

        for event_loss in models.EventLossAsset.objects.filter(
                event_loss__output=output).select_related().order_by(
                '-loss'):
            writer.writerow([event_loss.rupture.tag,
                             event_loss.asset.asset_ref,
                             "%.07f" % event_loss.rupture.rupture.magnitude,
                             "%.07f" % event_loss.loss])
    return dest
