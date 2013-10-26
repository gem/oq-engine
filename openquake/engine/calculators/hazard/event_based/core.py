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

import copy
import math
import random
import collections

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

BLOCK_SIZE = 1000  # blocks of 1,000 sites each

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@tasks.oqtask
def compute_ses(job_id, src_ids, ses, src_seeds):
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
    :param int src_seeds:
        Values for seeding numpy/scipy in the computation of stochastic event
        sets and ground motion fields from the sources
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    # complete_logic_tree_ses flag
    cmplt_lt_ses = None
    if hc.complete_logic_tree_ses:
        cmplt_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=job_id,
            ordinal=None)

    ltp = logictree.LogicTreeProcessor(hc.id)
    lt_rlz = ses.ses_collection.lt_realization

    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)

    src_filter = filters.source_site_distance_filter(hc.maximum_distance)
    rup_filter = filters.rupture_site_distance_filter(hc.maximum_distance)

    with EnginePerformanceMonitor(
            'reading site collection', job_id, compute_ses):
        site_collection = hc.site_collection

    with EnginePerformanceMonitor(
            'reading sources', job_id, compute_ses):
        sources = list(haz_general.gen_sources(
            src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
            hc.width_of_mfd_bin, hc.area_source_discretization))

    # Compute and save stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    with EnginePerformanceMonitor('computing ses', job_id, compute_ses):
        ruptures = []
        for src_seed, src in zip(src_seeds, sources):
            # first set the seed for the specific source
            numpy.random.seed(src_seed)
            # then make copies of the hazardlib ruptures (which may contain
            # duplicates): the copy is needed to keep the tags distinct
            rupts = map(copy.copy, stochastic.stochastic_event_set_poissonian(
                        [src], hc.investigation_time, site_collection,
                        src_filter, rup_filter))
            # set the tag for each copy
            for i, r in enumerate(rupts):
                r.tag = 'rlz=%02d|ses=%04d|src=%s|i=%03d' % (
                    lt_rlz.ordinal, ses.ordinal, src.source_id, i)
            ruptures.extend(rupts)
        if not ruptures:
            return

    with EnginePerformanceMonitor('saving ses', job_id, compute_ses):
        _save_ses_ruptures(ses, ruptures, cmplt_lt_ses)

compute_ses.ignore_result = False  # essential


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
        for r in ruptures:
            models.SESRupture.objects.create(
                ses=ses, rupture=r, tag=r.tag)

        if complete_logic_tree_ses is not None:
            for rupture in ruptures:
                models.SESRupture.objects.create(
                    ses=complete_logic_tree_ses,
                    rupture=rupture)


@tasks.oqtask
def compute_gmf(job_id, imt, gsims, ses, site_coll, ruptures, rupture_seeds):
    """
    Compute and save the GMFs for all the ruptures in a SES.
    """
    hc = ses.ses_collection.output.oq_job.hazard_calculation
    imt = haz_general.imt_to_hazardlib(imt)
    with EnginePerformanceMonitor(
            'computing gmfs', job_id, compute_gmf):
        gmvs_per_site, ruptures_per_site = _compute_gmf(
            hc, imt, gsims, site_coll, ruptures, rupture_seeds)

    with EnginePerformanceMonitor('saving gmfs', job_id, compute_gmf):
        _save_gmfs(ses, imt, gmvs_per_site, ruptures_per_site, site_coll)

compute_gmf.ignore_result = False  # essential

# NB: I tried to return a single dictionary {site_id: [(gmv, rupt_id),...]}
# but it takes a lot more memory (MS)
def _compute_gmf(hc, imt, gsims, site_coll, ruptures, rupture_seeds):
    """
    Compute a ground motion field value for each rupture, for all the
    points affected by that rupture, for the given IMT. Returns a
    dictionary with the nonzero contributions to each site id, and a dictionary
    with the ids of the contributing ruptures for each site id.
    """
    assert len(ruptures) == len(rupture_seeds)
    correl_model = None
    if hc.ground_motion_correlation_model is not None:
        correl_model = haz_general.get_correl_model(hc)

    n_sites = len(site_coll)
    gmvs_per_site = collections.defaultdict(list)
    ruptures_per_site = collections.defaultdict(list)

    # Compute and save ground motion fields
    for i, rupture in enumerate(ruptures):
        gmf_calc_kwargs = {
            'rupture': rupture.rupture,
            'sites': site_coll,
            'imts': [imt],
            'gsim': gsims[rupture.rupture.tectonic_region_type],
            'truncation_level': hc.truncation_level,
            'realizations': DEFAULT_GMF_REALIZATIONS,
            'correlation_model': correl_model,
            'rupture_site_filter': filters.rupture_site_distance_filter(
                hc.maximum_distance),
        }
        numpy.random.seed(rupture_seeds[i])
        # there is a single imt => a single entry in the return dict
        [gmfs] = gmf.ground_motion_fields(**gmf_calc_kwargs).values()
        gmvs = gmfs.reshape(n_sites)
        for site, gmv in zip(site_coll, gmvs):
            if gmv:  # nonzero contribution to site
                gmvs_per_site[site.id].append(gmv)
                ruptures_per_site[site.id].append(rupture.id)
    return gmvs_per_site, ruptures_per_site


@transaction.commit_on_success(using='reslt_writer')
def _save_gmfs(ses, imt, gmvs_per_site, ruptures_per_site, sites):
    """
    Helper method to save computed GMF data to the database.
    :param ses:
        A :class:`openquake.engine.db.models.SES` instance
    :param imt:
        An intensity measure type instance
    :param gmf_per_site:
        The GMFs per rupture
    :param rupture_per_site:
        The associated rupture ids
    :param sites:
        An :class:`openquake.hazardlib.site.SiteCollection` object,
        representing the sites of interest for a calculation.
    """
    gmf_coll = models.Gmf.objects.get(
        lt_realization=ses.ses_collection.lt_realization)

    sa_period = None
    sa_damping = None
    if isinstance(imt, openquake.hazardlib.imt.SA):
        sa_period = imt.period
        sa_damping = imt.damping
    imt_name = imt.__class__.__name__

    for site_id in gmvs_per_site:
        inserter.add(models.GmfData(
            gmf=gmf_coll,
            ses_id=ses.id,
            imt=imt_name,
            sa_period=sa_period,
            sa_damping=sa_damping,
            site_id=site_id,
            gmvs=gmvs_per_site[site_id],
            rupture_ids=ruptures_per_site[site_id]))
    inserter.flush()


class EventBasedHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """
    core_calc_task = compute_ses

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
        logs.LOG.warn('Using block size: %d', self.preferred_block_size)

        num_tasks = [math.ceil(float(n) / self.preferred_block_size) * num_ses
                     for n in num_sources]

        return int(sum(num_tasks))

    def task_arg_gen(self):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.
        Yielded results are tuples of the form job_id, src_ids, ses, seeds
        (seeds will be used to seed numpy for temporal occurence sampling).
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
                    # compute seeds for the sources
                    src_seeds = [rnd.randint(0, models.MAX_SINT_32)
                                 for _ in src_ids]
                    yield self.job.id, src_ids, ses, src_seeds

    def compute_gmf_arg_gen(self):
        """
        Argument generator for the task compute_gmf. For each SES yields a
        tuple of the form
        (job_id, imt, gsims, ses, site_coll, ruptures, rupture_seeds).
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        site_coll = self.hc.site_collection
        for lt_rlz in self._get_realizations():
            ltp = logictree.LogicTreeProcessor(self.hc.id)
            gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
            all_ses = models.SES.objects.filter(
                ses_collection__lt_realization=lt_rlz,
                ordinal__isnull=False).order_by('ordinal')
            for ses in all_ses:
                # count the ruptures in the given SES
                ruptures = list(models.SESRupture.objects.filter(ses=ses))
                if not ruptures:
                    continue
                # compute the associated seeds
                rupture_seeds = [rnd.randint(0, models.MAX_SINT_32)
                                 for _ in range(len(ruptures))]
                # splitting on IMTs to generate more tasks and save memory
                for imt in self.hc.intensity_measure_types:
                    if self.hc.ground_motion_correlation_model is None:
                        # we are splitting on sites to avoid running out of mem
                        # on the workers for computations like the full Japan
                        for sites in block_splitter(site_coll, BLOCK_SIZE):
                            yield (self.job.id, imt, gsims, ses,
                                   models.SiteCollection(sites),
                                   ruptures, rupture_seeds)
                    else:
                        # do not split on sites
                        yield (self.job.id, imt, gsims, ses, site_coll,
                               ruptures, rupture_seeds)

    def execute(self):
        """
        Run compute_ses and optionally compute_gmf in parallel.
        """
        self.parallelize(self.core_calc_task, self.task_arg_gen())
        if self.hc.ground_motion_fields:
            self.parallelize(compute_gmf, self.compute_gmf_arg_gen())

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
