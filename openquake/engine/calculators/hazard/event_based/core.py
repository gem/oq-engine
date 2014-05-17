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

import time
import random
import collections

import numpy.random

from django.db import transaction
from openquake.hazardlib.calc import gmf, filters
from openquake.hazardlib.imt import from_string

from openquake.engine import logs, writer
from openquake.engine.calculators.hazard import general
from openquake.engine.calculators.hazard.classical import (
    post_processing as cls_post_proc)
from openquake.engine.calculators.hazard.event_based import post_processing
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor

#: Always 1 for the computation of ground motion fields in the event-based
#: hazard calculator.
DEFAULT_GMF_REALIZATIONS = 1

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)


@tasks.oqtask
def compute_ses_and_gmfs(
        job_id, sitecol, src_seeds, trt_model_id, gsims, task_no):
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
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param src_seeds:
        List of pairs (source, seed)
    :params gsims:
        list of distinct GSIM instances
    :param task_no:
        an ordinal so that GMV can be collected in a reproducible order
    """
    # NB: all realizations in gsims correspond to the same source model
    trt_model = models.TrtModel.objects.get(pk=trt_model_id)
    ses_coll = models.SESCollection.objects.get(lt_model=trt_model.lt_model)

    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    all_ses = list(ses_coll)
    imts = map(from_string, hc.intensity_measure_types)
    params = dict(
        correl_model=general.get_correl_model(hc),
        truncation_level=hc.truncation_level,
        maximum_distance=hc.maximum_distance)

    gmfcollector = GmfCollector(
        params, imts, gsims, trt_model.get_rlzs_by_gsim())

    filter_sites_mon = LightMonitor(
        'filtering sites', job_id, compute_ses_and_gmfs)
    generate_ruptures_mon = LightMonitor(
        'generating ruptures', job_id, compute_ses_and_gmfs)
    filter_ruptures_mon = LightMonitor(
        'filtering ruptures', job_id, compute_ses_and_gmfs)
    save_ruptures_mon = LightMonitor(
        'saving ses', job_id, compute_ses_and_gmfs)
    compute_gmfs_mon = LightMonitor(
        'computing gmfs', job_id, compute_ses_and_gmfs)

    # Compute and save stochastic event sets
    rnd = random.Random()
    num_distinct_ruptures = 0
    total_ruptures = 0

    for src, seed in src_seeds:
        t0 = time.time()
        rnd.seed(seed)

        with filter_sites_mon:  # filtering sources
            s_sites = src.filter_sites_by_distance_to_source(
                hc.maximum_distance, sitecol
            ) if hc.maximum_distance else sitecol
            if s_sites is None:
                continue

        # the dictionary `ses_num_occ` contains [(ses, num_occurrences)]
        # for each occurring rupture for each ses in the ses collection
        ses_num_occ = collections.defaultdict(list)
        with generate_ruptures_mon:  # generating ruptures for the given source
            for rup_no, rup in enumerate(src.iter_ruptures(), 1):
                rup.rup_no = rup_no
                for ses in all_ses:
                    numpy.random.seed(rnd.randint(0, models.MAX_SINT_32))
                    num_occurrences = rup.sample_number_of_occurrences()
                    if num_occurrences:
                        ses_num_occ[rup].append((ses, num_occurrences))
                        total_ruptures += num_occurrences

        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_number_of_occurrences() *before* the filtering
        for rup in ses_num_occ.keys():
            with filter_ruptures_mon:  # filtering ruptures
                r_sites = filters.filter_sites_by_distance_to_rupture(
                    rup, hc.maximum_distance, s_sites
                    ) if hc.maximum_distance else s_sites
                if r_sites is None:
                    # ignore ruptures which are far away
                    del ses_num_occ[rup]  # save memory
                    continue

            ses_ruptures = []
            with save_ruptures_mon:  # saving ses_ruptures
                # using a django transaction make the saving faster
                with transaction.commit_on_success(using='job_init'):
                    prob_rup = models.ProbabilisticRupture.create(
                        rup, ses_coll)
                    for ses, num_occurrences in ses_num_occ[rup]:
                        for occ_no in range(1, num_occurrences + 1):
                            rup_seed = rnd.randint(0, models.MAX_SINT_32)
                            ses_rup = models.SESRupture.create(
                                prob_rup, ses, src.source_id,
                                rup.rup_no, occ_no, rup_seed)
                            ses_ruptures.append(ses_rup)

            with compute_gmfs_mon:  # computing GMFs
                if hc.ground_motion_fields:
                    for ses_rup in ses_ruptures:
                        gmfcollector.calc_gmf(
                            r_sites, rup, ses_rup.id, ses_rup.seed)

        # log calc_time per distinct rupture
        if ses_num_occ:
            num_ruptures = len(ses_num_occ)
            tot_ruptures = sum(num for rup in ses_num_occ
                               for ses, num in ses_num_occ[rup])
            logs.LOG.info(
                'job=%d, src=%s:%s, num_ruptures=%d, tot_ruptures=%d, '
                'num_sites=%d, calc_time=%fs', job_id, src.source_id,
                src.__class__.__name__, num_ruptures, tot_ruptures,
                len(s_sites), time.time() - t0)
            num_distinct_ruptures += num_ruptures

    if num_distinct_ruptures:
        logs.LOG.info('job=%d, task %d generated %d/%d ruptures',
                      job_id, task_no, num_distinct_ruptures, total_ruptures)
    filter_sites_mon.flush()
    generate_ruptures_mon.flush()
    filter_ruptures_mon.flush()
    save_ruptures_mon.flush()
    compute_gmfs_mon.flush()

    if hc.ground_motion_fields:
        with EnginePerformanceMonitor(
                'saving gmfs', job_id, compute_ses_and_gmfs):
            gmfcollector.save_gmfs(task_no)


class GmfCollector(object):
    """
    A class to compute and save ground motion fields.
    """
    def __init__(self, params, imts, gsims, rlzs):
        """
        :param params:
            a dictionary of parameters with keys
            correl_model, truncation_level, maximum_distance
        :param imts:
            a list of hazardlib intensity measure types
        :param gsims:
            a list of distinct GSIM instances
        :param rlzs:
            a dictionary returning the realizations per GSIM string
        """
        self.params = params
        self.imts = imts
        self.gsims = gsims
        self.rlzs = rlzs
        # NB: I tried to use a single dictionary
        # {site_id: [(gmv, rupt_id),...]} but it took a lot more memory (MS)
        self.gmvs_per_site = collections.defaultdict(list)
        self.ruptures_per_site = collections.defaultdict(list)

    def calc_gmf(self, r_sites, rupture, rupture_id, rupture_seed):
        """
        Compute the GMF generated by the given rupture on the given
        sites and collect the values in the dictionaries
        .gmvs_per_site and .ruptures_per_site.

        :param r_sites:
            the collection of sites affected by the rupture
        :param rupture:
            an `openquake.hazardlib.source.rupture.
                ParametricProbabilisticRupture` instance
        :param id:
            the id of an `openquake.engine.db.models.SESRupture` instance
        :param seed:
            an integer to be used as stochastic seed
        """
        for gsim in self.gsims:
            gmf_calc_kwargs = {
                'rupture': rupture,
                'sites': r_sites,
                'imts': self.imts,
                'gsim': gsim,
                'truncation_level': self.params['truncation_level'],
                'realizations': DEFAULT_GMF_REALIZATIONS,
                'correlation_model': self.params['correl_model'],
            }
            numpy.random.seed(rupture_seed)
            gmf_dict = gmf.ground_motion_fields(**gmf_calc_kwargs)
            for imt, gmf_1_realiz in gmf_dict.iteritems():
                # since DEFAULT_GMF_REALIZATIONS is 1, gmf_1_realiz is a matrix
                # with n_sites rows and 1 column
                for site_id, gmv in zip(r_sites.sids, gmf_1_realiz):
                    # convert a 1x1 matrix into a float
                    gmv = float(gmv)
                    if gmv:
                        for rlz in self.rlzs[gsim.__class__.__name__]:
                            self.gmvs_per_site[
                                rlz.id, imt, site_id].append(gmv)
                            self.ruptures_per_site[
                                rlz.id, imt, site_id].append(rupture_id)

    @transaction.commit_on_success(using='job_init')
    def save_gmfs(self, task_no):
        """
        Helper method to save the computed GMF data to the database.

        :param task_no:
            The ordinal of the task which generated the current GMFs to save
        """
        for rlz_id, imt, site_id in self.gmvs_per_site:
            rlz = models.LtRealization.objects.get(pk=rlz_id)
            imt_name, sa_period, sa_damping = imt
            inserter.add(models.GmfData(
                gmf=models.Gmf.objects.get(lt_realization=rlz),
                task_no=task_no,
                imt=imt_name,
                sa_period=sa_period,
                sa_damping=sa_damping,
                site_id=site_id,
                gmvs=self.gmvs_per_site[rlz_id, imt, site_id],
                rupture_ids=self.ruptures_per_site[rlz_id, imt, site_id]))
        inserter.flush()
        self.gmvs_per_site.clear()
        self.ruptures_per_site.clear()


class EventBasedHazardCalculator(general.BaseHazardCalculator):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """
    core_calc_task = compute_ses_and_gmfs

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
        for job_id, sitecol, block, lt_model, gsims, task_no in \
                super(EventBasedHazardCalculator, self).task_arg_gen():
            ss = [(src, rnd.randint(0, models.MAX_SINT_32))
                  for src in block]  # source, seed pairs
            yield job_id, sitecol, ss, lt_model, gsims, task_no

        # now the source_blocks_per_ltpath dictionary can be cleared
        self.source_blocks_per_ltpath.clear()

    def initialize_ses_db_records(self, lt_model):
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
            display_name='SES Collection smlt-%d' % lt_model.ordinal,
            output_type='ses')

        ses_coll = models.SESCollection.objects.create(
            output=output, lt_model=lt_model, ordinal=lt_model.ordinal)

        for rlz in lt_model:
            if self.job.hazard_calculation.ground_motion_fields:
                output = models.Output.objects.create(
                    oq_job=self.job,
                    display_name='GMF rlz-%s' % rlz.id,
                    output_type='gmf')
                models.Gmf.objects.create(output=output, lt_realization=rlz)

        return ses_coll

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """
        super(EventBasedHazardCalculator, self).pre_execute()
        for lt_model in models.LtSourceModel.objects.filter(
                hazard_calculation=self.hc):
            self.initialize_ses_db_records(lt_model)

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
