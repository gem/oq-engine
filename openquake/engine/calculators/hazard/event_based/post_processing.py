# Copyright (c) 2013, GEM Foundation.
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
GMFs to Hazard Curves

For each IMT, logic tree path, and point of interest, the number of GMF records
will be equal to the `ses_per_logic_tree_path`. The data contained in these
records can include ground motion values from many ruptures, stored in
variable length arrays; the quantity is random.

For post-processing, we will need to perform P * R * M queries to the database,
where P is the number of points in a given calculation, R is the total number
of tree paths, and M is the number of intensity measure levels defined for the
hazard curve processing. Each of these queries will give us all of the data we
need to compute a single hazard curve.

Typical values for P can go from 1 to a few 100,000s. *
Typical values for R can from 1 few 1,000s. *
Typical values for M are about 10.

* Considering maximum for both P and R is an extreme case.

P * R * M = 100,000 * 1,000 * 10 = 1 Billion queries, in the extreme case

This could be the target for future optimizations.
"""

import itertools
import math
import numpy

from django import db

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.utils import tasks
from openquake.engine.utils.general import block_splitter

HAZ_CURVE_DISP_NAME_FMT = 'hazard-curve-rlz-%(rlz)s-%(imt)s'


def gmf_post_process_arg_gen(job):
    """
    Generate a sequence of args for the GMF to hazard curve post-processing job
    for a given ``job``. These are task args.

    Yielded arguments are as follows:

    * job ID
    * point geometry
    * logic tree realization ID
    * IMT
    * IMLs
    * hazard curve "collection" ID
    * investigation time
    * duration
    * SA period
    * SA damping

    See :func:`gmf_to_hazard_curve_task` for more information about these
    arguments.

    As a side effect, :class:`openquake.engine.db.models.HazardCurve`
    records are
    created for each :class:`openquake.engine.db.models.LtRealization` and IMT.

    :param job:
        :class:`openquake.engine.db.models.OqJob` instance.
    """
    hc = job.hazard_calculation
    points = hc.points_to_compute()

    lt_realizations = models.LtRealization.objects.filter(
        hazard_calculation=hc.id)

    invest_time = hc.investigation_time
    duration = hc.ses_per_logic_tree_path * invest_time

    for raw_imt, imls in hc.intensity_measure_types_and_levels.iteritems():
        imt, sa_period, sa_damping = models.parse_imt(raw_imt)

        for lt_rlz in lt_realizations:
            hc_output = models.Output.objects.create_output(
                job,
                HAZ_CURVE_DISP_NAME_FMT % dict(imt=raw_imt, rlz=lt_rlz.id),
                'hazard_curve')

            # Create the hazard curve "collection":
            hc_coll = models.HazardCurve.objects.create(
                output=hc_output,
                lt_realization=lt_rlz,
                investigation_time=invest_time,
                imt=imt,
                imls=imls,
                sa_period=sa_period,
                sa_damping=sa_damping)

            for point in points:
                yield (job.id, point, lt_rlz.id, imt, imls, hc_coll.id,
                       invest_time, duration, sa_period, sa_damping)


# Disabling "Unused argument 'job_id'" (this parameter is required by @oqtask):
# pylint: disable=W0613
@tasks.oqtask
def gmf_to_hazard_curve_task(job_id, point, lt_rlz_id, imt, imls, hc_coll_id,
                             invest_time, duration, sa_period=None,
                             sa_damping=None):
    """
    For a given job, point, realization, and IMT, compute a hazard curve and
    save it to the database. The hazard curve will be computed from all
    available ground motion data for the specified point and realization.

    :param int job_id:
        ID of a currently running :class:`openquake.engine.db.models.OqJob`.
    :param point:
        A :class:`openquake.hazardlib.geo.point.Point` instance.
    :param int lt_rlz_id:
        ID of a :class:`openquake.engine.db.models.LtRealization` for the
        current calculation.
    :param str imt:
        Intensity Measure Type (PGA, SA, PGV, etc.)
    :param imls:
        List of Intensity Measure Levels. These will serve as the abscissae for
        the computed hazard curve.
    :param int hc_coll_id:
        ID of a :class:`openquake.engine.db.models.HazardCurve`, which will be
        the 'container' for the computed hazard curve.
    :param float invest_time:
        Investigation time, in years. It is with this time span that we compute
        probabilities of exceedance.

        Another way to put it is the following. When computing a hazard curve,
        we want to answer the question: What is the probability of ground
        motion meeting or exceeding the specified levels (``imls``) in a given
        time span (``invest_time``).
    :param float duration:
        Time window during which GMFs occur. Another was to say it is, the
        period of time over which we simulate ground motion occurrences.

        NOTE: Duration is computed as the calculation investigation time
        multiplied by the number of stochastic event sets.
    :param float sa_period:
        Spectral Acceleration period. Used only with ``imt`` of 'SA'.
    :param float sa_damping:
        Spectral Acceleration damping. Used only with ``imt`` of 'SA'.
    """
    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)
    gmfs = models.GmfAgg.objects.filter(
        gmf_collection__lt_realization=lt_rlz_id,
        imt=imt,
        sa_period=sa_period,
        sa_damping=sa_damping).extra(where=[
            "location::geometry ~= 'SRID=4326;%s'::geometry" % point.wkt2d])
    gmvs = list(itertools.chain(*(g.gmvs for g in gmfs)))

    # Compute the hazard curve PoEs:
    hc_poes = gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
    # Save:
    models.HazardCurveData.objects.create(
        hazard_curve_id=hc_coll_id, poes=hc_poes, location=point.wkt2d,
        weight=lt_rlz.weight)
gmf_to_hazard_curve_task.ignore_result = False  # essential


@tasks.oqtask  # the parameter job_id is required by the decorator
def insert_into_gmf_agg(_job_id, rlz, chunk_id, nchunks):
    """
    Aggregate the GMVs from the tables gmf and gmf_set in chunks.

    :param int _job_id: used for logging purposes
    :param rlz: a realization object
    :param int chunk_id: an integer from 0 to nchunks
    :param int nchunks: the number of chunks
    """
    coll = models.GmfCollection.objects.get(lt_realization=rlz)

    # IMPORTANT: in PostGIS 1.5 GROUP BY location does not work properly
    # if location is of geography type, hence the need to cast it to geometry
    insert_query = '''-- running
    INSERT INTO hzrdr.gmf_agg (gmf_collection_id, imt, sa_damping, sa_period,
                               location, gmvs, rupture_ids)
    SELECT gmf_collection_id, imt, sa_damping, sa_period, location::geometry,
       array_concat(gmvs ORDER BY gmf_set_id, result_grp_ordinal),
       array_concat(rupture_ids ORDER BY gmf_set_id, result_grp_ordinal)
    FROM hzrdr.gmf AS a, hzrdr.gmf_set AS b
    WHERE a.gmf_set_id=b.id AND gmf_collection_id={} AND a.id % {} = {}
    GROUP BY gmf_collection_id, imt, sa_damping, sa_period, location::geometry;
    '''.format(coll.id, nchunks, chunk_id)

    curs = db.connections['reslt_writer'].cursor()
    with db.transaction.commit_on_success(using='reslt_writer'):
        curs.execute(insert_query)
        logs.LOG.debug(insert_query)
        # TODO: delete the copied rows from gmf; this can be done
        # only after changing the export procedure to read from gmf_agg
    curs.close()
insert_into_gmf_agg.ignore_result = False  # essential


def populate_gmf_agg(job):
    """
    Populate the table gmf_agg from gmf and gmf_set.

    :param job:
        A :class:`openquake.engine.db.models.OqJob` instance.
    """
    hc = job.hazard_calculation
    rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
    nchunks = 16  # makes 16 chunks for each realization
    for rlz in rlzs:
        allargs = [(job.id, rlz, chunk_id, nchunks)
                   for chunk_id in range(nchunks)]
        # parallelizing the insert is effective because all the time is spent
        # in the aggregration query, not in the insert.
        tasks.parallelize(insert_into_gmf_agg, allargs)


def do_post_process(job):
    """
    Run the GMF to hazard curve post-processing tasks for the given ``job``.

    :param job:
        A :class:`openquake.engine.db.models.OqJob` instance.
    """
    block_size = int(config.get('hazard', 'concurrent_tasks'))
    block_gen = block_splitter(gmf_post_process_arg_gen(job), block_size)

    hc = job.hazard_calculation

    # Stats for debug logging:
    n_imts = len(hc.intensity_measure_types_and_levels)
    n_sites = len(hc.points_to_compute())
    n_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc).count()

    total_blocks = int(math.ceil(
        (n_imts * n_sites * n_rlzs) / float(block_size)))

    for i, block in enumerate(block_gen):
        logs.LOG.debug('> GMF post-processing block, %s of %s',
                       i + 1, total_blocks)

        tasks.parallelize(gmf_to_hazard_curve_task, block)

        logs.LOG.debug('< Done GMF post-processing block, %s of %s',
                       i + 1, total_blocks)


def gmvs_to_haz_curve(gmvs, imls, invest_time, duration):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        A list of ground motion values, as floats.
    :param imls:
        A list of intensity measure levels, as floats.
    :param float invest_time:
        Investigation time, in years. It is with this time span that we compute
        probabilities of exceedance.

        Another way to put it is the following. When computing a hazard curve,
        we want to answer the question: What is the probability of ground
        motion meeting or exceeding the specified levels (``imls``) in a given
        time span (``invest_time``).
    :param float duration:
        Time window during which GMFs occur. Another was to say it is, the
        period of time over which we simulate ground motion occurrences.

        NOTE: Duration is computed as the calculation investigation time
        multiplied by the number of stochastic event sets.

    :returns:
        Numpy array of PoEs (probabilities of exceedence).
    """
    gmvs = numpy.array(gmvs)
    # convert to numpy arrary and redimension so that it can be broadcast with
    # the gmvs for computing PoE values
    imls = numpy.array(imls).reshape((len(imls), 1))

    num_exceeding = numpy.sum(gmvs >= imls, axis=1)

    poes = 1 - numpy.exp(- (invest_time / duration) * num_exceeding)

    return poes
