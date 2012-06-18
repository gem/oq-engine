# Copyright (c) 2010-2012, GEM Foundation.
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


"""Core functionality of the Uniform Hazard Spectra calculator."""


import os
import random

from celery.task import task
from django.db import transaction
from django.contrib.gis.geos.geometry import GEOSGeometry

from openquake import java
from openquake.calculators.hazard import general
from openquake.calculators.hazard.uhs.ath import completed_task_count
from openquake.calculators.hazard.uhs.ath import uhs_task_handler
from openquake.db.models import Output
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.export.uhs import export_uhs
from openquake.input import logictree
from openquake.java import list_to_jdouble_array
from openquake.logs import LOG
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks
from openquake.utils.general import block_splitter


# Disabling 'Too many local variables'
# pylint: disable=R0914
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
    job_ctxt = utils_tasks.get_running_job(job_id)

    log_msg = (
        "Computing UHS for job_id=%s, site=%s, realization=%s."
        " UHS results will be serialized to the database.")
    log_msg %= (job_ctxt.job_id, site, realization)
    LOG.info(log_msg)

    uhs_results = compute_uhs(job_ctxt, site)

    write_uhs_spectrum_data(job_ctxt, realization, site, uhs_results)


# Disabling 'Too many arguments'
# pylint: disable=R0913
def compute_uhs(the_job, site):
    """Given a `JobContext` and a site of interest, compute UHS. The Java
    `UHSCalculator` is called to do perform the core computation.

    :param the_job:
        :class:`openquake.engine.JobContext` instance.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :returns:
        An `ArrayList` (Java object) of `UHSResult` objects, one per PoE.
    """

    periods = list_to_jdouble_array(the_job['UHS_PERIODS'])
    poes = list_to_jdouble_array(the_job['POES'])
    imls = general.get_iml_list(the_job['INTENSITY_MEASURE_LEVELS'],
                                the_job['INTENSITY_MEASURE_TYPE'])
    max_distance = the_job['MAXIMUM_DISTANCE']

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = general.generate_erf(the_job.job_id, cache)
    gmpe_map = general.generate_gmpe_map(the_job.job_id, cache)
    general.set_gmpe_params(gmpe_map, the_job.params)

    uhs_calc = java.jclass('UHSCalculator')(periods, poes, imls, erf, gmpe_map,
                                            max_distance)

    site_model = general.get_site_model(the_job.oq_job.id)

    if site_model is not None:
        sm_data = general.get_closest_site_model_data(site_model, site)
        vs30_type = sm_data.vs30_type.capitalize()
        vs30 = sm_data.vs30
        z1pt0 = sm_data.z1pt0
        z2pt5 = sm_data.z2pt5
    else:
        jp = the_job.oq_job_profile

        vs30_type = jp.vs30_type.capitalize()
        vs30 = jp.reference_vs30_value
        z1pt0 = jp.depth_to_1pt_0km_per_sec
        z2pt5 = jp.reference_depth_to_2pt5km_per_sec_param

    uhs_results = _compute_uhs(
        uhs_calc, site.latitude, site.longitude, vs30_type, vs30, z1pt0, z2pt5
    )

    return uhs_results


def _compute_uhs(calc, lat, lon, vs30_type, vs30, z1pt0, z2pt5):
    """Helper function for executing `computeUHS` in the java calculator.

    As a separate function, this makes it easier to mock (since we can't really
    mock the java code).

    See also :function:`compute_uhs`.

    :param calc:
        jpype `org.gem.calc.UHSCalculator` object.
    :param float lat:
        Site latitude.
    :param float lon:
        Site longitude.
    :param vs30_type:
        'measured' or 'inferred'. Identifies if vs30 value has been measured or
        inferred.
    :param float vs30:
        Average shear wave velocity for top 30 m. Units m/s.
    :param float z1pt0:
        Depth to shear wave velocity of 1.0 km/s. Units m.
    :param float z2pt5:
        Depth to shear wave velocity of 2.5 km/s. Units km.

    :returns:
        jpype `java.util.List` of `org.gem.calc.UHSResult` objects, one for
        each PoE value (which is provided to the ``calc``).
    """
    return calc.computeUHS(lat, lon, vs30_type, vs30, z1pt0, z2pt5)


@transaction.commit_on_success(using='reslt_writer')
def write_uh_spectra(job_ctxt):
    """Write the top-level Uniform Hazard Spectra calculation results records
    to the database.

    In the workflow of the UHS calculator, this should be written prior to the
    execution of the main job. (See
    :method:`openquake.calculators.base.Calculator.pre_execute`.)

    This function writes:
    * 1 record to uiapi.output
    * 1 record to hzrdr.uh_spectra
    * 1 record to hzrdr.uh_spectrum, per PoE defined in the calculation config

    :param job_ctxt:
        :class:`openquake.engine.JobContext` instance for the current
        UHS job.
    """
    oq_job_profile = job_ctxt.oq_job_profile
    oq_job = job_ctxt.oq_job

    output = Output(
        owner=oq_job.owner,
        oq_job=oq_job,
        display_name='UH Spectra for calculation id %s' % oq_job.id,
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
def write_uhs_spectrum_data(job_ctxt, realization, site, uhs_results):
    """Write UHS results for a single ``site`` and ``realization`` to the
    database.

    :param job_ctxt:
        :class:`openquake.engine.JobContext` instance for a UHS
        job.
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
    oq_job = job_ctxt.oq_job
    uh_spectra = UhSpectra.objects.get(
        output__oq_job=oq_job.id)

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


class UHSCalculator(general.BaseHazardCalculator):
    """Uniform Hazard Spectra calculator"""

    # LogicTreeProcessor for sampling the source model and gmpe logic trees.
    lt_processor = None

    def initialize(self):
        """Set the task total counter."""
        super(UHSCalculator, self).initialize()
        task_total = (self.job_ctxt.oq_job_profile.realizations
                      * len(self.job_ctxt.sites_to_compute()))
        stats.set_total(self.job_ctxt.job_id, 'h', 'uhs:tasks', task_total)

    def pre_execute(self):
        """Performs the following pre-execution tasks:

        - write initial DB 'container' records for the calculation results
        - instantiate a :class:`openquake.input.logictree.LogicTreeProcessor`
          for sampling source model and gmpe logic trees
        """
        write_uh_spectra(self.job_ctxt)

        source_model_lt = self.job_ctxt.params.get(
            'SOURCE_MODEL_LOGIC_TREE_FILE_PATH')
        gmpe_lt = self.job_ctxt.params.get('GMPE_LOGIC_TREE_FILE_PATH')
        basepath = self.job_ctxt.params.get('BASE_PATH')
        self.lt_processor = logictree.LogicTreeProcessor(
            basepath, source_model_lt, gmpe_lt)

    def execute(self):
        """Loop over realizations (logic tree samples), split the geometry of
        interest into blocks of sites, and distribute Celery tasks to carry out
        the UHS computation.
        """
        job_ctxt = self.job_ctxt
        all_sites = job_ctxt.sites_to_compute()
        site_block_size = config.hazard_block_size()
        job_profile = job_ctxt.oq_job_profile

        src_model_rnd = random.Random(job_profile.source_model_lt_random_seed)
        gmpe_rnd = random.Random(job_profile.gmpe_lt_random_seed)

        for rlz in xrange(job_ctxt.oq_job_profile.realizations):

            # Sample the gmpe and source models:
            general.store_source_model(
                job_ctxt.job_id, src_model_rnd.getrandbits(32),
                job_ctxt.params, self.lt_processor)
            general.store_gmpe_map(
                job_ctxt.job_id, gmpe_rnd.getrandbits(32), self.lt_processor)

            for site_block in block_splitter(all_sites, site_block_size):

                tf_args = dict(job_id=job_ctxt.job_id, realization=rlz)

                num_tasks_completed = completed_task_count(job_ctxt.job_id)

                ath_args = dict(job_id=job_ctxt.job_id,
                                num_tasks=len(site_block),
                                start_count=num_tasks_completed)

                utils_tasks.distribute(
                    compute_uhs_task, ('site', site_block), tf_args=tf_args,
                    ath=uhs_task_handler, ath_args=ath_args)

    def post_execute(self):
        """Clean up stats counters and create XML output artifacts (if
        requested).
        """
        # TODO: export these counters to the database before deleting them
        # See bug https://bugs.launchpad.net/openquake/+bug/925946.
        stats.delete_job_counters(self.job_ctxt.job_id)

        if 'xml' in self.job_ctxt.serialize_results_to:
            [uhs_output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type='uh_spectra')

            target_dir = os.path.join(self.job_ctxt.params.get('BASE_PATH'),
                                      self.job_ctxt.params.get('OUTPUT_DIR'))

            export_uhs(uhs_output, target_dir)
