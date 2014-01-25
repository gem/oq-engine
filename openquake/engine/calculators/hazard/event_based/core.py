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

import random
import collections

import numpy.random

from django.db import transaction
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc import gmf
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.imt import from_string

from openquake.engine import writer
from openquake.engine.calculators.hazard import general
from openquake.engine.calculators.hazard.classical import (
    post_processing as cls_post_proc)
from openquake.engine.calculators.hazard.event_based import post_processing
from openquake.engine.db import models
from openquake.engine.input import logictree
from openquake.engine.utils import tasks
from openquake.engine.utils.general import WeightedSequence
from openquake.engine.performance import EnginePerformanceMonitor


#: Always 1 for the computation of ground motion fields in the event-based
#: hazard calculator.
DEFAULT_GMF_REALIZATIONS = 1

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@tasks.oqtask
def compute_ses(job_id, src_seeds, ses_coll):
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
    :param src_seeds:
        List of pairs (source, seed)
    :param ses_coll:
        an instance of :class:`openquake.engine.db.models.SESCollection`
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    rnd = random.Random()
    all_ses = models.SES.objects.filter(ses_collection=ses_coll)
    tom = PoissonTOM(hc.investigation_time)
    ruptures = []

    # Compute and save stochastic event sets
    with EnginePerformanceMonitor('computing ses', job_id, compute_ses):
        for src, seed in src_seeds:
            rnd.seed(seed)
            rupts = list(src.iter_ruptures(tom))
            for ses in all_ses:
                numpy.random.seed(rnd.randint(0, models.MAX_SINT_32))
                for r in rupts:
                    for i in xrange(r.sample_number_of_occurrences()):
                        rup = models.SESRupture(
                            ses=ses,
                            rupture=r,
                            tag='rlz=%02d|ses=%04d|src=%s|i=%03d' % (
                                ses_coll.lt_realization.ordinal, ses.ordinal,
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
def compute_gmf(job_id, gmf_coll, gsims, rupt_seed_pairs, task_no):
    """
    Compute and save the GMFs for all the ruptures in the given block.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    imts = map(from_string, hc.intensity_measure_types)
    params = dict(
        correl_model=general.get_correl_model(hc),
        truncation_level=hc.truncation_level,
        maximum_distance=hc.maximum_distance)
    rupture_ids, rupture_seeds = zip(*rupt_seed_pairs)

    with EnginePerformanceMonitor(
            'reading ruptures', job_id, compute_gmf):
        ruptures = list(models.SESRupture.objects.filter(pk__in=rupture_ids))

    with EnginePerformanceMonitor(
            'computing gmfs', job_id, compute_gmf):
        gmvs_per_site, ruptures_per_site = _compute_gmf(
            params, imts, gsims, hc.site_collection, ruptures, rupture_seeds)

    with EnginePerformanceMonitor('saving gmfs', job_id, compute_gmf):
        _save_gmfs(gmf_coll, gmvs_per_site, ruptures_per_site,
                   hc.site_collection, task_no)


# NB: I tried to return a single dictionary {site_id: [(gmv, rupt_id),...]}
# but it takes a lot more memory (MS)
def _compute_gmf(params, imts, gsims, site_coll, ruptures, rupture_seeds):
    """
    Compute a ground motion field value for each rupture, for all the
    points affected by that rupture, for the given IMT. Returns a
    dictionary with the nonzero contributions to each site id, and a dictionary
    with the ids of the contributing ruptures for each site id.
    assert len(ruptures) == len(rupture_seeds)

    :param params:
        a dictionary containing the keys
        correl_model, truncation_level, maximum_distance
    :param imts:
        a list of hazardlib intensity measure types
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
            'imts': imts,
            'gsim': gsims[rupture.rupture.tectonic_region_type],
            'truncation_level': params['truncation_level'],
            'realizations': DEFAULT_GMF_REALIZATIONS,
            'correlation_model': params['correl_model'],
            'rupture_site_filter': filters.rupture_site_distance_filter(
                params['maximum_distance']),
        }
        numpy.random.seed(rupture_seeds[i])
        gmf_dict = gmf.ground_motion_fields(**gmf_calc_kwargs)
        for imt, gmf_1_realiz in gmf_dict.iteritems():
            # since DEFAULT_GMF_REALIZATIONS is 1, gmf_1_realiz is a matrix
            # with n_sites rows and 1 column
            for site, gmv in zip(site_coll, gmf_1_realiz):
                gmv = float(gmv)  # convert a 1x1 matrix into a float
                if gmv:  # nonzero contribution to site
                    gmvs_per_site[imt, site.id].append(gmv)
                    ruptures_per_site[imt, site.id].append(rupture.id)
    return gmvs_per_site, ruptures_per_site


@transaction.commit_on_success(using='job_init')
def _save_gmfs(gmf, gmvs_per_site, ruptures_per_site, sites, task_no):
    """
    Helper method to save computed GMF data to the database.

    :param gmf:
        The Gmf instance where to save
    :param gmf_per_site:
        The GMFs per rupture
    :param rupture_per_site:
        The associated rupture ids
    :param sites:
        An :class:`openquake.hazardlib.site.SiteCollection` object,
        representing the sites of interest for a calculation.
    :param task_no:
        The ordinal of the task which generated the current GMFs to save
    """
    for imt, site_id in gmvs_per_site:
        imt_name, sa_period, sa_damping = imt
        inserter.add(models.GmfData(
            gmf=gmf,
            task_no=task_no,
            imt=imt_name,
            sa_period=sa_period,
            sa_damping=sa_damping,
            site_id=site_id,
            gmvs=gmvs_per_site[imt, site_id],
            rupture_ids=ruptures_per_site[imt, site_id]))
    inserter.flush()


class EventBasedHazardCalculator(general.BaseHazardCalculator):
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
        for lt_rlz in self._get_realizations():
            path = tuple(lt_rlz.sm_lt_path)
            sources = WeightedSequence.chain(
                self.source_blocks_per_ltpath[path])
            ses_coll = models.SESCollection.objects.get(lt_realization=lt_rlz)
            ss = [(src, rnd.randint(0, models.MAX_SINT_32))
                  for src in sources]  # source, seed pairs
            for block in self.block_split(ss):
                yield self.job.id, block, ses_coll

        # now the source_blocks_per_ltpath dictionary can be cleared
        self.source_blocks_per_ltpath.clear()

    def compute_gmf_arg_gen(self):
        """
        Argument generator for the task compute_gmf. For each SES yields a
        tuple of the form (job_id, gmf_coll, gsims, rupture_ids, rupture_seeds,
        task_no).
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        for lt_rlz in self._get_realizations():
            ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
            gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
            ses_coll = models.SESCollection.objects.get(lt_realization=lt_rlz)
            gmf_coll = models.Gmf.objects.get(
                lt_realization=ses_coll.lt_realization)
            rupture_ids = models.SESRupture.objects.filter(
                ses__ses_collection=ses_coll).values_list('id', flat=True)
            if not rupture_ids:
                continue
            # compute the associated seeds
            rupture_seed_pairs = [(rid, rnd.randint(0, models.MAX_SINT_32))
                                  for rid in rupture_ids]

            # we split on ruptures to avoid running out of memory
            for i, rs_pairs in enumerate(self.block_split(rupture_seed_pairs)):
                yield self.job.id, gmf_coll, gsims, rs_pairs, i

    def post_execute(self):
        """
        Optionally compute_gmf in parallel.
        """
        if self.hc.ground_motion_fields:
            self.parallelize(compute_gmf,
                             self.compute_gmf_arg_gen(),
                             self.log_percent)

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
        super(EventBasedHazardCalculator, self).pre_execute()
        for rlz in self._get_realizations():
            self.initialize_ses_db_records(rlz)

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
