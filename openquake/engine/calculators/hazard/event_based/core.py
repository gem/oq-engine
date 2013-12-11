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
import collections

import numpy.random

from django.db import transaction
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc import gmf
from openquake.hazardlib.calc import stochastic
from openquake.hazardlib.imt import from_string

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
def compute_ses(job_id, src_seeds, ses_coll, smlt):
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
        List of pairs (source, seed)
    :param ses_coll:
       A :class:`openquake.engine.db.models.SESCollection` instance
    :param smlt:
        A :class:`openquake.engine.input.SourceModelLogicTree` instance
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    apply_uncertainties = smlt.make_apply_uncertainties(ses_coll.sm_lt_path)
    rnd = random.Random()
    all_ses = models.SES.objects.filter(
        ses_collection=ses_coll).order_by('ordinal')

    # Compute and save stochastic event sets
    with EnginePerformanceMonitor('computing ses', job_id, compute_ses):
        ruptures = []
        for source, seed in src_seeds:
            src = apply_uncertainties(source)
            rnd.seed(seed)
            for ses in all_ses:
                numpy.random.seed(rnd.randint(0, models.MAX_SINT_32))
                rupts = stochastic.stochastic_event_set_poissonian(
                    [src], hc.investigation_time)
                for i, r in enumerate(rupts):
                    rup = models.SESRupture(
                        ses=ses,
                        rupture=r,
                        tag='smlt=%s|ses=%04d|src=%s|i=%03d' % (
                            '_'.join(ses_coll.sm_lt_path), ses.ordinal,
                            src.source_id, i),
                        hypocenter=r.hypocenter.wkt2d,
                        magnitude=r.mag,
                    )
                    ruptures.append(rup)
        if not ruptures:
            return

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
def compute_gmvs(job_id, params, imt, gsims, ses_id, gmf, site_coll,
                 rupture_ids, rupture_seeds):
    """
    Compute and save the GMFs for all the ruptures in a SES.
    See the docstring in _compute_gmvs which is doing the real work.
    """
    imt = from_string(imt)
    with EnginePerformanceMonitor(
            'reading ruptures', job_id, compute_gmvs):
        ruptures = list(models.SESRupture.objects.filter(pk__in=rupture_ids))
    with EnginePerformanceMonitor(
            'computing gmvs', job_id, compute_gmvs):
        gmvs_per_site, ruptures_per_site = _compute_gmvs(
            params, imt, gsims, site_coll, ruptures, rupture_seeds)

    with EnginePerformanceMonitor('saving gmvs', job_id, compute_gmvs):
        _save_gmvs(
            gmf, ses_id, imt, gmvs_per_site, ruptures_per_site, site_coll)


# NB: I tried to return a single dictionary {site_id: [(gmv, rupt_id),...]}
# but it takes a lot more memory (MS)
def _compute_gmvs(params, imt, gsims, site_coll, ruptures, rupture_seeds):
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
def _save_gmvs(gmf, ses_id, imt, gmvs_per_site, ruptures_per_site, sites):
    """
    Helper method to save computed GMF data to the database.

    :param gmf:
        A :class:`openquake.engine.db.models.Gmf` instance
    :param int ses_id:
        The id of a :class:`openquake.engine.db.models.SES` record
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
    imt_name, sa_period, sa_damping = imt
    for site_id in gmvs_per_site:
        inserter.add(models.GmfData(
            gmf=gmf,
            ses_id=ses_id,
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

    def filtered_sites(self, src):
        """
        Return the sites within maximum_distance from the source or None
        """
        if self.hc.maximum_distance is None:
            return self.hc.site_collection  # do not filter
        return src.filter_sites_by_distance_to_source(
            self.hc.maximum_distance, self.hc.site_collection)

    def initialize_ses_records(self):
        """
        Create :class:`~openquake.engine.db.models.Output`,
        :class:`~openquake.engine.db.models.SES` and
        :class:`~openquake.engine.db.models.SESCollection`
        "container" records for all source models in the logic tree.
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        smwp = self.smlt.get_sm_weight_paths(
            self.hc.number_of_logic_tree_samples, rnd)
        n = 0
        for sm_path, weight, sm_lt_path in smwp:
            output = models.Output.objects.create(
                oq_job=self.job,
                display_name='SES Collection %s' % '_'.join(sm_lt_path),
                output_type='ses')

            ses_coll = models.SESCollection.objects.create(
                output=output, sm_path=sm_path,
                sm_lt_path=sm_lt_path,
                weight=weight)

            the_ses = [
                models.SES(
                    ses_collection=ses_coll,
                    investigation_time=self.hc.investigation_time,
                    ordinal=i,
                ) for i in xrange(1, self.hc.ses_per_logic_tree_path + 1)]
            writer.CacheInserter.saveall(the_ses)
            n += self.hc.ses_per_logic_tree_path
        logs.LOG.info('Created %d SES', n)

    def initialize_gmf_records(self, lt_rlz):
        """
        Create :class:`~openquake.engine.db.models.Output` and
        :class:`~openquake.engine.db.models.Gmf` "container" records for
        a single realization.
        """
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name='GMF rlz-%s' % lt_rlz.id,
            output_type='gmf')
        models.Gmf.objects.create(output=output, lt_realization=lt_rlz)

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """
        self.parse_risk_models()
        self.initialize_site_model()
        self.initialize_sources()
        self.initialize_ses_records()

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
        for ses_coll in models.SESCollection.objects.filter(
                output__oq_job=self.job):
            sm = ses_coll.sm_path
            sources = (self.sources_per_model[sm, 'point'] +
                       self.sources_per_model[sm, 'other'])
            preferred_block_size = int(
                math.ceil(float(len(sources)) / self.concurrent_tasks()))
            logs.LOG.info('Using block size %d', preferred_block_size)

            ss = [(src, rnd.randint(0, models.MAX_SINT_32))
                  for src in sources]  # source, seed pairs
            for block in block_splitter(ss, preferred_block_size):
                yield self.job.id, block, ses_coll, self.smlt

        # now the dictionary can be cleared to save memory
        self.sources_per_model.clear()

    def compute_gmvs_arg_gen(self):
        """
        Argument generator for the task compute_gmvs. For each SES yields a
        tuple of the form (job_id, params, imt, gsims, ses, gmf, site_coll,
        rupture_ids, rupture_seeds).
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        site_coll = self.hc.site_collection
        params = dict(
            correl_model=haz_general.get_correl_model(self.hc),
            truncation_level=self.hc.truncation_level,
            maximum_distance=self.hc.maximum_distance)

        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
        n_ruptures = 0

        for ses_coll in models.SESCollection.objects.filter(
                output__oq_job=self.job):
            for gmf in models.Gmf.objects.filter(
                    output__oq_job=self.job,
                    lt_realization__sm_lt_path=ses_coll.sm_lt_path):
                lt_rlz = gmf.lt_realization
                gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
                for ses in ses_coll:
                    # count the ruptures in the given SES
                    rup_ids = models.SESRupture.objects.filter(
                        ses=ses).values_list('id', flat=True)
                    if not rup_ids:
                        continue
                    n_ruptures += len(rup_ids)

                    # compute the associated seeds
                    rup_seeds = [rnd.randint(0, models.MAX_SINT_32)
                                 for _ in range(len(rup_ids))]
                    # splitting on IMTs to generate more tasks and save memory
                    for imt in self.hc.intensity_measure_types:
                        if self.hc.ground_motion_correlation_model is None:
                            # we split on sites to avoid running out of memory
                            for sites in block_splitter(site_coll, BLOCK_SIZE):
                                yield (self.job.id, params, imt, gsims, ses.id,
                                       gmf, models.SiteCollection(sites),
                                       rup_ids, rup_seeds)
                        else:
                            # we split on ruptures
                            rupt_iter = block_splitter(rup_ids, BLOCK_SIZE)
                            seed_iter = block_splitter(rup_seeds, BLOCK_SIZE)
                            for rupts, seeds in zip(rupt_iter, seed_iter):
                                yield (self.job.id, params, imt, gsims, ses.id,
                                       gmf, site_coll, rupts, seeds)
        logs.LOG.info('Considering %d ruptures', n_ruptures)

    def post_execute(self):
        """
        Optionally compute_gmvs in parallel.
        """
        if self.hc.ground_motion_fields:
            self.initialize_realizations([self.initialize_gmf_records])
            self.parallelize(compute_gmvs, self.compute_gmvs_arg_gen(),
                             self.log_percent)

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
                    post_processing.gmf_to_hazard_curve_arg_gen(self.job),
                    self.log_percent)

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
                            self.job),
                        self.log_percent)
