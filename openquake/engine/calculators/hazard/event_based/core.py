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

BLOCK_SIZE = 5000  # TODO: put this in openquake.cfg

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@tasks.oqtask
def compute_ses(job_id, src_ses_seeds, lt_rlz, ltp):
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
    :param src_ses_seeds:
        List of triples (src_id, ses, seed)
        Stochastic Event Set object
    :param lt_rlz:
        Logic Tree realization object
    :param ltp:
        A :class:`openquake.engine.input.LogicTreeProcessor` instance
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)
    if hc.maximum_distance:
        src_filter = filters.source_site_distance_filter(hc.maximum_distance)
    else:
        src_filter = filters.source_site_noop_filter

    source = {}
    with EnginePerformanceMonitor(
            'filtering sources', job_id, compute_ses):
        for src, ses, seed in src_ses_seeds:
            if src.source_id not in source:
                if list(src_filter([(src, hc.site_collection)])):
                    source[src.source_id] = apply_uncertainties(src)

    # Compute and save stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    with EnginePerformanceMonitor('computing ses', job_id, compute_ses):
        ruptures = []
        for src, ses, seed in src_ses_seeds:
            numpy.random.seed(seed)
            rupts = stochastic.stochastic_event_set_poissonian(
                [source[src.source_id]], hc.investigation_time)
            for i, r in enumerate(rupts):
                rup = models.SESRupture(
                    ses=ses,
                    rupture=r,
                    tag='rlz=%02d|ses=%04d|src=%s|i=%03d' % (
                        lt_rlz.ordinal, ses.ordinal, src.source_id, i),
                    hypocenter=r.hypocenter.wkt2d,
                    magnitude=r.mag,
                )
                ruptures.append(rup)
        if not ruptures:
            return
        source.clear()  # save a little memory

    with EnginePerformanceMonitor('saving ses', job_id, compute_ses):
        _save_ses_ruptures(ruptures)


def _save_ses_ruptures(ruptures):
    """
    Helper function for saving stochastic event set ruptures to the database.
    :param ruptures:
        A list of :class:`openquake.engine.db.models.SESRupture` instances.
    """
    # TODO: Possible future optimization:
    # Refactor this to do bulk insertion of ruptures
    with transaction.commit_on_success(using='job_init'):
        for r in ruptures:
            r.save()


@tasks.oqtask
def compute_gmf(job_id, params, imt, gsims, ses, site_coll,
                rupture_ids, rupture_seeds):
    """
    Compute and save the GMFs for all the ruptures in a SES.
    """
    imt = haz_general.imt_to_hazardlib(imt)
    with EnginePerformanceMonitor(
            'reading ruptures', job_id, compute_gmf):
        ruptures = list(models.SESRupture.objects.filter(pk__in=rupture_ids))
    with EnginePerformanceMonitor(
            'computing gmfs', job_id, compute_gmf):
        gmvs_per_site, ruptures_per_site = _compute_gmf(
            params, imt, gsims, site_coll, ruptures, rupture_seeds)

    with EnginePerformanceMonitor('saving gmfs', job_id, compute_gmf):
        _save_gmfs(ses, imt, gmvs_per_site, ruptures_per_site, site_coll)


# NB: I tried to return a single dictionary {site_id: [(gmv, rupt_id),...]}
# but it takes a lot more memory (MS)
def _compute_gmf(params, imt, gsims, site_coll, ruptures, rupture_seeds):
    """
    Compute a ground motion field value for each rupture, for all the
    points affected by that rupture, for the given IMT. Returns a
    dictionary with the nonzero contributions to each site id, and a dictionary
    with the ids of the contributing ruptures for each site id.
    assert len(ruptures) == len(rupture_seeds)

    :param params:
        a dictionary containing the keys
        correl_model, truncation_level, maximum_distance
    :param imt:
        a hazardlib IMT instance
    :param gsims:
        a dictionary {tectonic region type -> GSIM instance}
    :param site_coll:
        a SiteCollection instance
    :param ruptures:
        a list of SESRupture objects
    :param rupture_seeds:
        a list with the seeds associated to the ruptures
    """
    gmvs_per_site = collections.defaultdict(list)
    ruptures_per_site = collections.defaultdict(list)

    # Compute and save ground motion fields
    for i, rupture in enumerate(ruptures):
        gmf_calc_kwargs = {
            'rupture': rupture.rupture,
            'sites': site_coll,
            'imts': [imt],
            'gsim': gsims[rupture.rupture.tectonic_region_type],
            'truncation_level': params['truncation_level'],
            'realizations': DEFAULT_GMF_REALIZATIONS,
            'correlation_model': params['correl_model'],
            'rupture_site_filter': filters.rupture_site_distance_filter(
                params['maximum_distance']),
        }
        numpy.random.seed(rupture_seeds[i])
        # there is a single imt => a single entry in the return dict
        [gmf_1_realiz] = gmf.ground_motion_fields(**gmf_calc_kwargs).values()
        # since DEFAULT_GMF_REALIZATIONS is 1, gmf_1_realiz is a matrix
        # with n_sites rows and 1 column
        for site, gmv in zip(site_coll, gmf_1_realiz):
            gmv = float(gmv)  # convert a 1x1 matrix into a float
            if gmv:  # nonzero contribution to site
                gmvs_per_site[site.id].append(gmv)
                ruptures_per_site[site.id].append(rupture.id)
    return gmvs_per_site, ruptures_per_site


@transaction.commit_on_success(using='job_init')
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

    def task_arg_gen(self, _block_size=None):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.
        Yielded results are tuples of the form job_id, sources, ses, seeds
        (seeds will be used to seed numpy for temporal occurence sampling).
        """
        hc = self.hc
        rnd = random.Random()
        rnd.seed(hc.random_seed)
        realizations = self._get_realizations()

        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
        for lt_rlz in realizations:
            sm = self.rlz_to_sm[lt_rlz]
            sources = (self.sources_per_model[sm, 'point'] +
                       self.sources_per_model[sm, 'other'])

            all_ses = list(models.SES.objects.filter(
                           ses_collection__lt_realization=lt_rlz,
                           ordinal__isnull=False).order_by('ordinal'))

            # source, ses, seed triples
            sss = [(src, ses, rnd.randint(0, models.MAX_SINT_32))
                   for src, ses in itertools.product(sources, all_ses)]
            preferred_block_size = int(
                math.ceil(float(len(sources) * len(all_ses)) /
                          self.concurrent_tasks()))
            logs.LOG.info('Using block size %d', preferred_block_size)
            for block in block_splitter(sss, preferred_block_size):
                yield self.job.id, block, lt_rlz, ltp

    def compute_gmf_arg_gen(self):
        """
        Argument generator for the task compute_gmf. For each SES yields a
        tuple of the form (job_id, params, imt, gsims, ses, site_coll,
        rupture_ids, rupture_seeds).
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        site_coll = self.hc.site_collection
        params = dict(
            correl_model=haz_general.get_correl_model(self.hc),
            truncation_level=self.hc.truncation_level,
            maximum_distance=self.hc.maximum_distance)
        for lt_rlz in self._get_realizations():
            ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
            gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
            all_ses = models.SES.objects.filter(
                ses_collection__lt_realization=lt_rlz,
                ordinal__isnull=False).order_by('ordinal')
            for ses in all_ses:
                # count the ruptures in the given SES
                rupture_ids = models.SESRupture.objects.filter(
                    ses=ses).values_list('id', flat=True)
                if not rupture_ids:
                    continue
                # compute the associated seeds
                rupture_seeds = [rnd.randint(0, models.MAX_SINT_32)
                                 for _ in range(len(rupture_ids))]
                # splitting on IMTs to generate more tasks and save memory
                for imt in self.hc.intensity_measure_types:
                    if self.hc.ground_motion_correlation_model is None:
                        # we split on sites to avoid running out of memory
                        # on the workers for computations like the full Japan
                        for sites in block_splitter(site_coll, BLOCK_SIZE):
                            yield (self.job.id, params, imt, gsims, ses,
                                   models.SiteCollection(sites),
                                   rupture_ids, rupture_seeds)
                    else:
                        # we split on ruptures to avoid running out of memory
                        rupt_iter = block_splitter(rupture_ids, BLOCK_SIZE)
                        seed_iter = block_splitter(rupture_seeds, BLOCK_SIZE)
                        for rupts, seeds in zip(rupt_iter, seed_iter):
                            yield (self.job.id, params, imt, gsims, ses,
                                   site_coll, rupts, seeds)

    def post_execute(self):
        """
        Optionally compute_gmf in parallel.
        """
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
            oq_job=self.job,
            display_name='SES Collection rlz-%s' % lt_rlz.id,
            output_type='ses')

        ses_coll = models.SESCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        if self.job.hazard_calculation.ground_motion_fields:
            output = models.Output.objects.create(
                oq_job=self.job,
                display_name='GMF rlz-%s' % lt_rlz.id,
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

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        rlz_callbacks = [self.initialize_ses_db_records]

        self.initialize_realizations(rlz_callbacks=rlz_callbacks)

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
