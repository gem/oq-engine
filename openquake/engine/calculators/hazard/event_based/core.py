# Copyright (c) 2010-2013, GEM Foundation.
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
Core calculator functionality for computing stochastic event sets and ground
motion fields using the 'event-based' method.

Stochastic events sets (which can be thought of as collections of ruptures) are
computed iven a set of seismic sources and investigation time span (in years).

For more information on computing stochastic event sets, see
:mod:`openquake.hazardlib.calc.stochastic`.

One can optionally compute a ground motion field (GMF) given a rupture, a site
collection (which is a collection of geographical points with associated soil
parameters), and a ground shaking intensity model (GSIM).

For more information on computing ground motion fields, see
:mod:`openquake.hazardlib.calc.gmf`.
"""

import math
import random
import itertools

import openquake.hazardlib.imt
import numpy.random

from django.db import transaction
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc import gmf
from openquake.hazardlib.calc import stochastic

from openquake.engine import writer, logs
from openquake.engine.utils.general import block_splitter
from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators.hazard.classical import (
    post_processing as cls_post_proc)
from openquake.engine.calculators.hazard.event_based import post_processing
from openquake.engine.db import models
from openquake.engine.input import logictree
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor


#: Always 1 for the computation of ground motion fields in the event-based
#: hazard calculator.
DEFAULT_GMF_REALIZATIONS = 1

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@tasks.oqtask
def ses_and_gmfs(job_id, src_ids, ses, task_seed):
    """
    Celery task for the stochastic event set calculator.

    Samples logic trees and calls the stochastic event set calculator.

    Once stochastic event sets are calculated, results will be saved to the
    database. See :class:`openquake.engine.db.models.SESCollection`.

    Optionally (specified in the job configuration using the
    `ground_motion_fields` parameter), GMFs can be computed from each rupture
    in each stochastic event set. GMFs are also saved to the database.

    :param int job_id:
        ID of the currently running job.
    :param src_ids:
        List of ids of parsed source models from which we will generate
        stochastic event sets/ruptures.
    :param ses:
        Stochastic Event Set object
    :param int task_seed:
        Value for seeding numpy/scipy in the computation of stochastic event
        sets and ground motion fields.
    """
    numpy.random.seed(task_seed)

    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    # complete_logic_tree_ses flag
    cmplt_lt_ses = None
    if hc.complete_logic_tree_ses:
        cmplt_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=job_id,
            ordinal=None)

    # preparing sources

    ltp = logictree.LogicTreeProcessor(hc.id)
    lt_rlz = ses.ses_collection.lt_realization

    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)

    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

    source_iter = haz_general.gen_sources(
        src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
        hc.width_of_mfd_bin, hc.area_source_discretization)

    src_filter = filters.source_site_distance_filter(hc.maximum_distance)
    rup_filter = filters.rupture_site_distance_filter(hc.maximum_distance)

    with EnginePerformanceMonitor(
            'reading site collection', job_id, ses_and_gmfs):
        site_collection = hc.site_collection

    # Compute and save stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    with EnginePerformanceMonitor('computing ses', job_id, ses_and_gmfs):
        ruptures = list(stochastic.stochastic_event_set_poissonian(
                        source_iter, hc.investigation_time, site_collection,
                        src_filter, rup_filter))
        if not ruptures:
            return

        # set the tag for each generated source:
        # the same rupture can be repeated several times, therefore
        # the tags are not unique; this is not a problem since ruptures
        # with the same tag are actually the same rupture
        for source_id, rupts in itertools.groupby(
                ruptures, lambda r: r.source.source_id):
            for i, r in enumerate(rupts):
                r.tag = 'rlz=%02d,ses=%04d,src=%s,i=%d' % (
                    lt_rlz.ordinal, ses.ordinal, source_id, i)

    with EnginePerformanceMonitor('saving ses', job_id, ses_and_gmfs):
        rupture_ids = _save_ses_ruptures(ses, ruptures, cmplt_lt_ses)

    if hc.ground_motion_fields:
        with EnginePerformanceMonitor(
                'computing gmfs', job_id, ses_and_gmfs):
            gmf_cache = compute_gmf_cache(
                hc, gsims, ruptures, rupture_ids)

        with EnginePerformanceMonitor('saving gmfs', job_id, ses_and_gmfs):
            _save_gmfs(ses, gmf_cache, site_collection)

ses_and_gmfs.ignore_result = False  # essential


def compute_gmf_cache(hc, gsims, ruptures, rupture_ids):
    """
    Compute a ground motion field value for each rupture, for all the
    points affected by that rupture, for all IMTs.
    """
    imts = [haz_general.imt_to_hazardlib(x)
            for x in hc.intensity_measure_types]
    correl_model = None
    if hc.ground_motion_correlation_model is not None:
        correl_model = haz_general.get_correl_model(hc)

    n_points = len(hc.site_collection)

    # initialize gmf_cache, a dict imt -> {gmvs, rupture_ids}
    gmf_cache = dict((imt, dict(gmvs=numpy.empty((n_points, 0)),
                                rupture_ids=[]))
                     for imt in imts)

    for rupture, rupture_id in zip(ruptures, rupture_ids):

        # Compute and save ground motion fields
        gmf_calc_kwargs = {
            'rupture': rupture,
            'sites': hc.site_collection,
            'imts': imts,
            'gsim': gsims[rupture.tectonic_region_type],
            'truncation_level': hc.truncation_level,
            'realizations': DEFAULT_GMF_REALIZATIONS,
            'correlation_model': correl_model,
            'rupture_site_filter': filters.rupture_site_distance_filter(
                hc.maximum_distance),
        }
        gmf_dict = gmf.ground_motion_fields(**gmf_calc_kwargs)

        # update the gmf cache:
        for imt_key, v in gmf_dict.iteritems():
            gmf_cache[imt_key]['gmvs'] = numpy.append(
                gmf_cache[imt_key]['gmvs'], v, axis=1)
            gmf_cache[imt_key]['rupture_ids'].append(rupture_id)

    return gmf_cache


def _save_ses_ruptures(ses, ruptures, complete_logic_tree_ses):
    """
    Helper function for saving stochastic event set ruptures to the database.

    :param ses:
        A :class:`openquake.engine.db.models.SES` instance. This will be DB
        'container' for the new rupture record.
    :param rupture:
        A :class:`openquake.hazardlib.source.rupture.Rupture` instance.
    :param complete_logic_tree_ses:
        :class:`openquake.engine.db.models.SES` representing the `complete
        logic tree` stochastic event set.
        If not None, save a copy of the input `rupture` to this SES.
    """

    # TODO: Possible future optimiztion:
    # Refactor this to do bulk insertion of ruptures
    with transaction.commit_on_success(using='reslt_writer'):
        rupture_ids = [models.SESRupture.objects.create(
            ses=ses, rupture=r, tag=r.tag).id
            for r in ruptures]

        if complete_logic_tree_ses is not None:
            for rupture in ruptures:
                models.SESRupture.objects.create(
                    ses=complete_logic_tree_ses,
                    rupture=rupture)

    return rupture_ids


@transaction.commit_on_success(using='reslt_writer')
def _save_gmfs(ses, gmf_dict, sites):
    """
    Helper method to save computed GMF data to the database.
    :param ses:
        A :class:`openquake.engine.db.models.SES` instance
    :param dict gmf_dict:
        The dict used to cache/buffer up GMF results during the calculation.
    :param sites:
        An :class:`openquake.hazardlib.site.SiteCollection` object,
        representing the sites of interest for a calculation.
    """
    gmf_coll = models.Gmf.objects.get(
        lt_realization=ses.ses_collection.lt_realization)

    for imt, gmf_data in gmf_dict.iteritems():

        gmfs = gmf_data['gmvs']
        # ``gmfs`` and ``rupture_ids`` come in as a numpy.matrix and
        # a list. we want them as an array; it handles subscripting in
        # the way that we want
        gmfs = numpy.array(gmfs)
        rupture_ids = numpy.array(gmf_data['rupture_ids'])

        sa_period = None
        sa_damping = None
        if isinstance(imt, openquake.hazardlib.imt.SA):
            sa_period = imt.period
            sa_damping = imt.damping
        imt_name = imt.__class__.__name__

        for all_gmvs, site in zip(gmfs, sites):
            # take only the nonzero ground motion values and the
            # corresponding rupture ids
            nonzero_gmvs_idxs = numpy.where(all_gmvs != 0)
            gmvs = all_gmvs[nonzero_gmvs_idxs].tolist()
            relevant_rupture_ids = rupture_ids[nonzero_gmvs_idxs].tolist()
            if gmvs:
                inserter.add(models.GmfData(
                    gmf=gmf_coll,
                    ses_id=ses.id,
                    imt=imt_name,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    site_id=site.id,
                    gmvs=gmvs,
                    rupture_ids=relevant_rupture_ids))
    inserter.flush()


class EventBasedHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """
    core_calc_task = ses_and_gmfs

    preferred_block_size = 1  # will be overridden in calc_num_tasks

    def calc_num_tasks(self):
        """
        The number of tasks is inferred from the configuration parameter
        concurrent_tasks (c), from the number of sources per realization
        (n) and from the number of stochastic event sets (s) by using
        the formula::

                     N * n
         num_tasks = ----- * s
                       b

        where N is the number of realizations and b is the block_size,
        defined as::

             N * n * s
         b = ---------
              10 * c

        The divisions are intended rounded to the closest upper integer
        (ceil). The mechanism is intended to generate a number of tasks
        close to 10 * c independently on the number of sources and SES.
        For instance, with c = 512, you should expect the engine to
        generate at most 5120 tasks; they could be much less in case
        of few sources and few SES; the minimum number of tasks generated
        is::

          num_tasks_min = N * n * s

        To have good concurrency the number of tasks must be bigger than
        the number of the cores (which is essentially c) but not too big,
        otherwise all the time would be wasted in passing arguments.
        Generating 10 times more tasks than cores gives a nice progress
        percentage. There is no more motivation than that.
        """
        preferred_num_tasks = self.concurrent_tasks() * 10
        num_ses = self.hc.ses_per_logic_tree_path

        num_sources = []  # number of sources per realization
        for lt_rlz in self._get_realizations():
            n = models.SourceProgress.objects.filter(
                lt_realization=lt_rlz).count()
            num_sources.append(n)
            logs.LOG.info('Found %d sources for realization %d',
                          n, lt_rlz.id)
        total_sources = sum(num_sources)

        if len(num_sources) > 1:
            logs.LOG.info('Total number of sources: %d', total_sources)

        self.preferred_block_size = int(
            math.ceil(float(total_sources * num_ses) / preferred_num_tasks))
        logs.LOG.info('Using block size: %d', self.preferred_block_size)

        num_tasks = [math.ceil(float(n) / self.preferred_block_size) * num_ses
                     for n in num_sources]

        return int(sum(num_tasks))

    def task_arg_gen(self):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.
        Yielded results are tuples of the form job_id, src_ids, ses, task_seed
        (task_seed will be used to seed numpy for temporal occurence sampling).
        """
        hc = self.hc
        rnd = random.Random()
        rnd.seed(hc.random_seed)
        realizations = self._get_realizations()

        for lt_rlz in realizations:
            sources = models.SourceProgress.objects\
                .filter(is_complete=False, lt_realization=lt_rlz)\
                .order_by('id')\
                .values_list('parsed_source_id', flat=True)

            all_ses = list(models.SES.objects.filter(
                           ses_collection__lt_realization=lt_rlz,
                           ordinal__isnull=False).order_by('ordinal'))

            for src_ids in block_splitter(sources, self.preferred_block_size):
                for ses in all_ses:
                    task_seed = rnd.randint(0, models.MAX_SINT_32)
                    task_args = (self.job.id, src_ids, ses, task_seed)
                    yield task_args

    def execute(self):
        """
        Run ses_and_gmfs in parallel.
        """
        self.parallelize(self.core_calc_task, self.task_arg_gen())

    def initialize_ses_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.engine.db.models.Output`,
        :class:`~openquake.engine.db.models.SESCollection` and
        :class:`~openquake.engine.db.models.SES` "container" records for
        a single realization.

        Stochastic event set ruptures computed for this realization will be
        associated to these containers.

        NOTE: Many tasks can contribute ruptures to the same SES.
        """
        output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='ses-coll-rlz-%s' % lt_rlz.id,
            output_type='ses')

        ses_coll = models.SESCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        if self.job.hazard_calculation.ground_motion_fields:
            output = models.Output.objects.create(
                owner=self.job.owner,
                oq_job=self.job,
                display_name='gmf-rlz-%s' % lt_rlz.id,
                output_type='gmf')

            models.Gmf.objects.create(
                output=output, lt_realization=lt_rlz)

        all_ses = []
        for i in xrange(1, self.hc.ses_per_logic_tree_path + 1):
            all_ses.append(
                models.SES.objects.create(
                    ses_collection=ses_coll,
                    investigation_time=self.hc.investigation_time,
                    ordinal=i))
        return all_ses

    def initialize_complete_lt_ses_db_records(self):
        """
        Optional; if the user has requested to collect a `complete logic tree`
        stochastic event set (containing all ruptures from all realizations),
        initialize DB records for those results here.

        Throughout the course of the calculation, computed ruptures will be
        copied into this collection. See :func:`_save_ses_ruptures` for more
        info.
        """
        # `complete logic tree` SES
        clt_ses_output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='complete logic tree SES',
            output_type='complete_lt_ses')

        clt_ses_coll = models.SESCollection.objects.create(
            output=clt_ses_output)

        models.SES.objects.create(
            ses_collection=clt_ses_coll,
            investigation_time=self.hc.total_investigation_time())

        if self.hc.complete_logic_tree_gmf:
            clt_gmf_output = models.Output.objects.create(
                owner=self.job.owner,
                oq_job=self.job,
                display_name='complete logic tree GMF',
                output_type='complete_lt_gmf')
            models.Gmf.objects.create(output=clt_gmf_output)

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """
        # Parse risk models.
        self.parse_risk_models()

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        rlz_callbacks = [self.initialize_ses_db_records]

        self.initialize_realizations(rlz_callbacks=rlz_callbacks)

        if self.job.hazard_calculation.complete_logic_tree_ses:
            self.initialize_complete_lt_ses_db_records()

        self.record_init_stats()

        num_sources = models.SourceProgress.objects.filter(
            is_complete=False,
            lt_realization__hazard_calculation=self.hc).count()
        self.progress['total'] = num_sources

        self.initialize_pr_data()

    def post_process(self):
        """
        If requested, perform additional processing of GMFs to produce hazard
        curves.
        """
        if self.hc.hazard_curves_from_gmfs:
            with EnginePerformanceMonitor('generating hazard curves',
                                          self.job.id):
                self.parallelize(
                    post_processing.gmf_to_hazard_curve_task,
                    post_processing.gmf_to_hazard_curve_arg_gen(self.job))

            # If `mean_hazard_curves` is True and/or `quantile_hazard_curves`
            # has some value (not an empty list), do this additional
            # post-processing.
            if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
                with EnginePerformanceMonitor(
                        'generating mean/quantile curves', self.job.id):
                    self.do_aggregate_post_proc()

            if self.hc.hazard_maps:
                with EnginePerformanceMonitor(
                        'generating hazard maps', self.job.id):
                    self.parallelize(
                        cls_post_proc.hazard_curves_to_hazard_map_task,
                        cls_post_proc.hazard_curves_to_hazard_map_task_arg_gen(
                            self.job))
