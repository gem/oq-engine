# Copyright (c) 2012, GEM Foundation.
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

import numpy

from openquake.db import models
from openquake.utils import config
from openquake.utils import tasks as utils_tasks
from openquake.utils.general import block_splitter


def gmf_post_process_arg_gen(job):
    hc = job.hazard_calculation
    points = hc.points_to_compute()

    lt_realizations = models.LtRealization.objects.filter(
        hazard_calculation=hc.id)

    invest_time = hc.investigation_time
    duration = hc.ses_per_logic_tree_path * invest_time

    for imt, imls in hc.intensity_measure_types_and_levels.iteritems():
        imt, sa_period, sa_damping = models.parse_imt(imt)

        for lt_rlz in lt_realizations:  # TODO:

            hc_output = models.Output.objects.create_output(
                job, 'disp_name', 'hazard_curve')  # TODO: not a fake disp name

            # create the hazard curve collection
            hc_coll = models.HazardCurve.objects.create(
                output=hc_output,
                lt_realization=lt_rlz,
                imt=imt,
                sa_period=sa_period,
                sa_damping=sa_damping)

            for point in points:
                # yield args for tasks
                yield (job.id, point, lt_rlz.id, imt, sa_period, sa_damping,
                       imls, hc_coll.id, invest_time, duration)


@utils_tasks.oqtask
def gmf_to_hazard_curve_task(job_id, point, lt_rlz_id, imt, sa_period,
                             sa_damping, imls, hc_coll_id, invest_time,
                             duration):

    gmfs = models.Gmf.objects.filter(
        gmf_set__gmf_collection__lt_realization=lt_rlz_id,
        imt=imt,
        sa_period=sa_period,
        sa_damping=sa_damping,
        location=point.wkt2d)

    gmvs = itertools.chain(*(g.gmvs for g in gmfs))
    hc_poes = gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
    # TODO: save the curve to the DB.


def do_post_process(job):
    logs.LOG.debug('> Post-processing - GMFs to Hazard Curves')
    block_size = config.get('hazard', 'concurrent_tasks')
    block_gen = block_splitter(gmf_post_process_arg_gen(job), block_size)

    total_blocks = math.ceil((n_imts * n_sites * n_rlzs) / block_size)

    for i, block in enumerate(block_gen):
        logs.LOG.debug('> GMF post-processing block, %s of %s'
                       % (i + 1, total_blocks))
        tasks = []
        for args in block:
            tasks.append(gmf_to_hazard_curve_task.subtask(*args))
        results = TaskSet(tasks=tasks).apply_async()

        # Check for Exceptions in the results and raise
        utils_tasks._check_exception(results)

        logs.LOG.debug('> Done GMF post-processing block, %s of %s'
                       % (i + 1, total_blocks))
    logs.LOG.debug('< Done post-processing - GMFs to Hazard Curves')


def gmvs_to_haz_curve(gmvs, imls, invest_time, duration):
    """
    :returns:
        List of PoEs (probabilities of exceedence).
    """
    gmvs = numpy.array(gmvs)
    # convert to numpy arrary and redimension so that it can be broadcast with
    # the gmvs for computing PoE values
    imls = numpy.array(imls).reshape((len(imls), 1))

    num_exceeding = numpy.sum(gmvs >= imls, axis=1)

    poes = 1 - numpy.exp(- (invest_time / duration) * num_exceeding)

    return poes
