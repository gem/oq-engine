# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Core functionality of the Uniform Hazard Spectra calculator."""


import h5py
import numpy
import random

from celery.task import task
from django.db import transaction
from django.contrib.gis.geos.geometry import GEOSGeometry

from openquake import java
from openquake.input import logictree
from openquake.java import list_to_jdouble_array
from openquake.logs import LOG
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks
from openquake.calculators.base import Calculator
from openquake.db.models import Output
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.calculators.hazard.general import generate_erf
from openquake.calculators.hazard.general import generate_gmpe_map
from openquake.calculators.hazard.general import get_iml_list
from openquake.calculators.hazard.general import store_source_model
from openquake.calculators.hazard.general import store_gmpe_map
from openquake.calculators.hazard.general import set_gmpe_params


@task(ignore_result=True)
def touch_result_file(job_id, path, sites, realizations, n_periods):
    """Given a path (including the file name), create an empty HDF5 result file
    containing 1 empty data set for each site. Each dataset will be a matrix
    with the number of rows = number of samples and number of cols = number of
    UHS periods.

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param str path:
        Location (including a file name) on an NFS where the empty
        result file should be created.
    :param sites:
        List of :class:`openquake.shapes.Site` objects.
    :param int realizations:
        Number of logic tree samples (the y-dimension of each dataset).
    :param int n_periods:
        Number of UHS periods (the x-dimension of each dataset).
    """
    utils_tasks.get_running_calculation(job_id)
    # TODO: Generate the sites, instead of pumping them through rabbit?
    with h5py.File(path, 'w') as h5_file:
        for site in sites:
            ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
            ds_shape = (realizations, n_periods)
            h5_file.create_dataset(ds_name, dtype=numpy.float64,
                                   shape=ds_shape)


@task(ignore_results=True)
@stats.progress_indicator('h')
@java.unpack_exception
def compute_uhs_task(job_id, realization, site):
    """Compute Uniform Hazard Spectra for a given site of interest and 1 or
    more Probability of Exceedance values. The bulk of the computation will
    be done by utilizing the `UHSCalculator` class in the Java code.

    UHS results will be written directly to the database.

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param realization:
        Logic tree sample number (from 1 to N, where N is the
        NUMBER_OF_LOGIC_TREE_SAMPLES param defined in the job config.
    :param site:
        The site of interest (a :class:`openquake.shapes.Site` object).
    """
    calc_proxy = utils_tasks.get_running_calculation(job_id)

    log_msg = (
        "Computing UHS for job_id=%s, site=%s, realization=%s."
        " UHS results will be serialized to the database.")
    log_msg %= (calc_proxy.job_id, site, realization)
    LOG.info(log_msg)

    uhs_results = compute_uhs(calc_proxy, site)

    write_uhs_spectrum_data(calc_proxy, realization, site, uhs_results)


def compute_uhs(the_job, site):
    """Given a `CalculationProxy` and a site of interest, compute UHS. The Java
    `UHSCalculator` is called to do perform the core computation.

    :param the_job:
        :class:`openquake.engine.CalculationProxy` instance.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :returns:
        An `ArrayList` (Java object) of `UHSResult` objects, one per PoE.
    """

    periods = list_to_jdouble_array(the_job['UHS_PERIODS'])
    poes = list_to_jdouble_array(the_job['POES'])
    imls = get_iml_list(the_job['INTENSITY_MEASURE_LEVELS'],
                        the_job['INTENSITY_MEASURE_TYPE'])
    max_distance = the_job['MAXIMUM_DISTANCE']

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = generate_erf(the_job.job_id, cache)
    gmpe_map = generate_gmpe_map(the_job.job_id, cache)
    set_gmpe_params(gmpe_map, the_job.params)

    uhs_calc = java.jclass('UHSCalculator')(periods, poes, imls, erf, gmpe_map,
                                            max_distance)

    uhs_results = uhs_calc.computeUHS(
        site.latitude,
        site.longitude,
        the_job['VS30_TYPE'],
        the_job['REFERENCE_VS30_VALUE'],
        the_job['DEPTHTO1PT0KMPERSEC'],
        the_job['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM'])

    return uhs_results


@transaction.commit_on_success(using='reslt_writer')
def write_uh_spectra(calc_proxy):
    """Write the top-level Uniform Hazard Spectra calculation results records
    to the database.

    In the workflow of the UHS calculator, this should be written prior to the
    execution of the main calculation. (See
    :method:`openquake.calculators.base.Calculator.pre_execute`.)

    This function writes:
    * 1 record to uiapi.output
    * 1 record to hzrdr.uh_spectra
    * 1 record to hzrdr.uh_spectrum, per PoE defined in the calculation config

    :param calc_proxy:
        :class:`openquake.engine.CalculationProxy` instance for the current
        UHS calculation.
    """
    oq_job_profile = calc_proxy.oq_job_profile
    oq_calculation = calc_proxy.oq_calculation

    output = Output(
        owner=oq_calculation.owner,
        oq_calculation=oq_calculation,
        display_name='UH Spectra for calculation id %s' % oq_calculation.id,
        db_backed=True,
        output_type='uh_spectra')
    output.save()

    uh_spectra = UhSpectra(
        output=output,
        timespan=oq_job_profile.investigation_time,
        realizations=oq_job_profile.realizations,
        periods=oq_job_profile.uhs_periods)
    uh_spectra.save()

    for poe in oq_job_profile.poes:
        uh_spectrum = UhSpectrum(uh_spectra=uh_spectra, poe=poe)
        uh_spectrum.save()


@transaction.commit_on_success(using='reslt_writer')
def write_uhs_spectrum_data(calc_proxy, realization, site, uhs_results):
    """Write UHS results for a single ``site`` and ``realization`` to the
    database.

    :param calc_proxy:
        :class:`openquake.engine.CalculationProxy` instance for a UHS
        calculation.
    :param int realization:
       The realization number (from 0 to N, where N is the number of logic tree
        samples defined in the calculation config) for which these results have
        been computed.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :param uhs_results:
        List of `UHSResult` jpype Java objects, one for each PoE defined in the
        calculation configuration.
    """
    # Get the top-level uh_spectra record for this calculation:
    oq_calculation = calc_proxy.oq_calculation
    uh_spectra = UhSpectra.objects.get(
        output__oq_calculation=oq_calculation.id)

    location = GEOSGeometry(site.point.to_wkt())

    for result in uhs_results:
        poe = result.getPoe()
        # Get the uh_spectrum record to which the current result belongs.
        # Remember, each uh_spectrum record is associated with a partiuclar
        # PoE.
        uh_spectrum = UhSpectrum.objects.get(uh_spectra=uh_spectra.id, poe=poe)

        # getUhs() yields a Java Double[] of SA (Spectral Acceleration) values
        sa_values = [x.value for x in result.getUhs()]

        uh_spectrum_data = UhSpectrumData(
            uh_spectrum=uh_spectrum, realization=realization,
            sa_values=sa_values, location=location)
        uh_spectrum_data.save()


def completed_task_count(job_id):
    """Given the ID of a currently running calculation, query the stats
    counters Redis to get the number of completed :function:`compute_uhs_task`
    task executions.

    Successful and failed executions are included in the count.

    :param int job_id:
        ID of the current calculation.
    :returns:
        Number of completed :function:`compute_uhs_task` task executions so
        far.
    """
    success_count = stats.get_counter(job_id, 'h', 'compute_uhs_task', 'i')
    fail_count = stats.get_counter(
        job_id, 'h', 'compute_uhs_task-failures', 'i')

    return (success_count or 0) + (fail_count or 0)


def remaining_tasks_in_block(job_id, num_tasks, start_count):
    """Figures out the numbers of remaining tasks in the current block. This
    should only be called during an active calculation.

    Given the ID of a currently running calculation, query the stats
    counters in Redis and determine when N :function:`compute_uhs_task` tasks
    have been completed (where N is ``num_tasks``).

    The count includes successful task executions as well as failures.

    This function is implemented as a generator which yields the remainging
    number of tasks to be execute in this block. When the target number of
    tasks is reached, a :exception:`StopIteration` is raised.

    :param int job_id:
        ID of the current calculation.
    :param int num_tasks:
        Number of :function:`compute_uhs_task` tasks in this block.
    :param int start_count:
        The starting total of :function:`compute_uhs_task` tasks completed.

        At the beginning of the calculation, this will be 0 of course. At the
        beginning of subsequent blocks, it needs to be computed _before_
        starting both the block calculation and the async task handler (to
        avoid a possible race condition with the task counters).
    :yields:
        The remaining number of tasks to be executed in this block.
    :raises:
        :exception:`StopIteration` when all block tasks are complete
        (successful or not).
    """
    running_total = lambda: completed_task_count(job_id) or 0

    target = start_count + num_tasks
    while running_total() < target:
        yield target - running_total()  # remaining


def uhs_task_handler(job_id, num_tasks):
    """Async task handler for counting calculation results and determining when
    a batch of tasks is complete."""
    remaining_gen = remaining_tasks_in_block(job_id, num_tasks)

    while True:
        import time
        time.sleep(0.5)
        try:
            remaining_gen.next()
        except StopIteration:
            # No more tasks remaining in this batch.
            break


class UHSCalculator(Calculator):
    """Uniform Hazard Spectra calculator"""

    # LogicTreeProcessor for sampling the source model and gmpe logic trees.
    lt_processor = None

    def analyze(self):
        """Set the task total counter."""
        task_total = (self.calc_proxy.oq_job_profile.realizations
                      * len(self.calc_proxy.sites_to_compute()))
        stats.set_total(self.calc_proxy.job_id, 'h', 'uhs:tasks', task_total)

    def pre_execute(self):
        """Performs the following pre-execution tasks:

        - write initial DB 'container' records for the calculation results
        - instantiate a :class:`openquake.input.logictree.LogicTreeProcessor`
          for sampling source model and gmpe logic trees
        """
        write_uh_spectra(self.calc_proxy)

        source_model_lt = self.calc_proxy.params.get(
            'SOURCE_MODEL_LOGIC_TREE_FILE')
        gmpe_lt = self.calc_proxy.params.get('GMPE_LOGIC_TREE_FILE')
        basepath = self.calc_proxy.params.get('BASE_PATH')
        self.lt_processor = logictree.LogicTreeProcessor(
            basepath, source_model_lt, gmpe_lt)

    def execute(self):

        calc_proxy = self.calc_proxy
        job_profile = calc_proxy.oq_job_profile

        src_model_rnd = random.Random(job_profile.source_model_lt_random_seed)
        gmpe_rnd = random.Random(job_profile.gmpe_lt_random_seed)

        for rlz in xrange(calc_proxy.oq_job_profile.realizations):

            # Sample the gmpe and source models:
            store_source_model(
                calc_proxy.job_id, src_model_rnd.getrandbits(32),
                calc_proxy.params, self.lt_processor)
            store_gmpe_map(
                calc_proxy.job_id, gmpe_rnd.getrandbits(32), self.lt_processor)

            tf_args = dict(job_id=calc_proxy.job_id, realization=rlz)

            distribute(
                compute_uhs_task, ('site', calc_proxy.sites_to_compute()),
                tf_args=tf_args, ath=lambda x: x, ath_args=dict())
            # Notes: the async task handler could probably just operate by
            # checking counters.

    def post_execute(self):
        stats.delete_job_counters(self.calc_proxy.job_id)
