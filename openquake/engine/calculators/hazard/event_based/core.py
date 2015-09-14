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
import logging
import operator
import itertools
import collections

import numpy.random

from openquake.hazardlib.calc import gmf
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import FilteredSiteCollection

from openquake.calculators.event_based import (
    sample_ruptures, build_ses_ruptures)

from openquake.engine import writer
from openquake.engine.calculators import calculators
from openquake.engine.calculators.hazard import general
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor

# NB: beware of large caches
inserter = writer.CacheInserter(models.GmfData, 1000)
source_inserter = writer.CacheInserter(models.SourceInfo, 100)


# NB (MS): the approach used here will not work for non-poissonian models
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
        Numpy array of PoEs (probabilities of exceedance).
    """
    # convert to numpy array and redimension so that it can be broadcast with
    # the gmvs for computing PoE values; there is a gmv for each rupture
    # here is an example: imls = [0.03, 0.04, 0.05], gmvs=[0.04750576]
    # => num_exceeding = [1, 1, 0] coming from 0.04750576 > [0.03, 0.04, 0.05]
    imls = numpy.array(imls).reshape((len(imls), 1))
    num_exceeding = numpy.sum(numpy.array(gmvs) >= imls, axis=1)
    poes = 1 - numpy.exp(- (invest_time / duration) * num_exceeding)
    return poes


@tasks.oqtask
def compute_ruptures(sources, sitecol, info, monitor):
    """
    Celery task for the stochastic event set calculator.

    Samples logic trees and calls the stochastic event set calculator.

    Once stochastic event sets are calculated, results will be saved to the
    database. See :class:`openquake.engine.db.models.SESCollection`.

    Optionally (specified in the job configuration using the
    `ground_motion_fields` parameter), GMFs can be computed from each rupture
    in each stochastic event set. GMFs are also saved to the database.

    :param sources:
        List of commonlib.source.Source tuples
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param info:
        a :class:`openquake.commonlib.source.CompositionInfo` instance
    :param monitor:
        monitor of the currently running job.
    :returns:
        a dictionary trt_model_id -> tot_ruptures
    """
    # NB: all realizations in gsims correspond to the same source model
    trt_model_id = sources[0].trt_model_id
    trt_model = models.TrtModel.objects.get(pk=trt_model_id)
    ses_coll = {sc.ordinal: sc for sc in models.SESCollection.objects.filter(
        trt_model=trt_model)}

    hc = models.oqparam(monitor.job_id)
    tot_ruptures = 0

    filter_sites_mon = monitor('filtering sites', measuremem=False)
    generate_ruptures_mon = monitor('generating ruptures', measuremem=False)
    filter_ruptures_mon = monitor('filtering ruptures', measuremem=False)
    save_ruptures_mon = monitor('saving ruptures', measuremem=False)

    # Compute and save stochastic event sets
    for src in sources:
        t0 = time.time()

        with filter_sites_mon:  # filtering sources
            s_sites = src.filter_sites_by_distance_to_source(
                hc.maximum_distance, sitecol)
            if s_sites is None:
                continue

        with generate_ruptures_mon:
            num_occ_by_rup = sample_ruptures(
                src, hc.ses_per_logic_tree_path, info)

        with filter_ruptures_mon:
            pairs = list(
                build_ses_ruptures(
                    src, num_occ_by_rup, s_sites, hc.maximum_distance, sitecol
                ))
        # saving ses_ruptures
        with save_ruptures_mon:
            for rup, rups in pairs:
                for col_id in set(r.col_id for r in rups):
                    prob_rup = models.ProbabilisticRupture.create(
                        rup, ses_coll[col_id], rups[0].indices)
                    for r in rups:
                        if r.col_id == col_id:
                            models.SESRupture.objects.create(
                                rupture=prob_rup, ses_id=r.ses_idx,
                                tag=r.tag, seed=r.seed)

        if num_occ_by_rup:
            num_ruptures = len(num_occ_by_rup)
            occ_ruptures = sum(num for rup in num_occ_by_rup
                               for num in num_occ_by_rup[rup].itervalues())
            tot_ruptures += occ_ruptures
        else:
            num_ruptures = 0
            occ_ruptures = 0

        # save SourceInfo
        source_inserter.add(
            models.SourceInfo(trt_model_id=trt_model_id,
                              source_id=src.source_id,
                              source_class=src.__class__.__name__,
                              num_sites=len(s_sites),
                              num_ruptures=num_ruptures,
                              occ_ruptures=occ_ruptures,
                              uniq_ruptures=num_ruptures,
                              calc_time=time.time() - t0))

    filter_sites_mon.flush()
    generate_ruptures_mon.flush()
    filter_ruptures_mon.flush()
    save_ruptures_mon.flush()
    source_inserter.flush()

    return {trt_model_id: tot_ruptures}


@tasks.oqtask
def compute_gmfs_and_curves(ses_ruptures, sitecol, rlzs_assoc, monitor):
    """
    :param ses_ruptures:
        a list of blocks of SESRuptures with homogeneous TrtModel
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param rlzs_assoc:
        a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary trt_model_id -> (curves_by_gsim, bounding_boxes)
        where the list of bounding boxes is empty
    """
    job = models.OqJob.objects.get(pk=monitor.job_id)
    hc = job.get_oqparam()
    imts = hc.imtls

    result = {}  # trt_model_id -> (curves_by_gsim, [])
    # NB: by construction each block is a non-empty list with
    # ruptures of homogeneous SESCollection
    ses_coll = ses_ruptures[0].rupture.ses_collection
    trt_model = ses_coll.trt_model
    gsims = rlzs_assoc.gsims_by_trt_id[trt_model.id]
    calc = GmfCalculator(
        sorted(imts), sorted(gsims), ses_coll,
        hc.truncation_level, models.get_correl_model(job))

    with monitor('computing gmfs', autoflush=True):
        for rupture, group in itertools.groupby(
                ses_ruptures, operator.attrgetter('rupture')):
            r_sites = sitecol if rupture.site_indices is None \
                else FilteredSiteCollection(rupture.site_indices, sitecol)
            calc.calc_gmfs(
                r_sites, rupture, [(r.id, r.seed) for r in group])

    if hc.hazard_curves_from_gmfs:
        duration = hc.investigation_time * hc.ses_per_logic_tree_path * (
            hc.number_of_logic_tree_samples or 1)
        with monitor('hazard curves from gmfs', autoflush=True):
            result[trt_model.id] = (calc.to_haz_curves(
                sitecol.sids, hc.imtls, hc.investigation_time, duration), [])
    else:
        result[trt_model.id] = ([], [])

    if hc.ground_motion_fields:
        with monitor('saving gmfs', autoflush=True):
            calc.save_gmfs(rlzs_assoc)

    return result


class GmfCalculator(object):
    """
    A class to store ruptures and then compute and save ground motion fields.
    """
    def __init__(self, sorted_imts, sorted_gsims, ses_coll,
                 truncation_level=None, correl_model=None):
        """
        :param sorted_imts:
            a sorted list of hazardlib intensity measure types
        :param sorted_gsims:
            a sorted list of hazardlib GSIM instances
        :param int trt_model_id:
            the ID of a TRTModel instance
        :param int truncation_level:
            the truncation level, or None
        :param str correl_model:
            the correlation model, or None
        """
        self.sorted_imts = sorted_imts
        self.sorted_gsims = sorted_gsims
        self.col_id = ses_coll.ordinal
        self.trt_model_id = ses_coll.trt_model.id
        self.truncation_level = truncation_level
        self.correl_model = correl_model
        # NB: I tried to use a single dictionary
        # {site_id: [(gmv, rupt_id),...]} but it took a lot more memory (MS)
        self.gmvs_per_site = collections.defaultdict(list)
        self.ruptures_per_site = collections.defaultdict(list)

    def calc_gmfs(self, r_sites, rupture, rupid_seed_pairs):
        """
        Compute the GMF generated by the given rupture on the given
        sites and collect the values in the dictionaries
        .gmvs_per_site and .ruptures_per_site.

        :param r_sites:
            a SiteCollection instance with the sites affected by the rupture
        :param rupture:
            a ProbabilisticRupture instance
        :param rupid_seed_pairs:
            a list of pairs (ses_rupture_id, ses_rupture_seed)
        """
        computer = gmf.GmfComputer(
            rupture, r_sites, self.sorted_imts, self.sorted_gsims,
            self.truncation_level, self.correl_model)
        gnames = map(str, computer.gsims)
        rupids, seeds = zip(*rupid_seed_pairs)
        for rupid, gmfa in zip(rupids, computer.compute(seeds)):
            for gname in gnames:
                gmf_by_imt = gmfa[gname]
                for imt in self.sorted_imts:
                    for site_id, gmv in zip(r_sites.sids, gmf_by_imt[imt]):
                        self.gmvs_per_site[
                            gname, imt, site_id].append(gmv)
                        self.ruptures_per_site[
                            gname, imt, site_id].append(rupid)

    def save_gmfs(self, rlzs_assoc):
        """
        Helper method to save the computed GMF data to the database.

        :param rlzs_assoc:
            a :class:`openquake.commonlib.source.RlzsAssoc` instance
        """
        samples = rlzs_assoc.csm_info.get_num_samples(self.trt_model_id)
        col_ids = rlzs_assoc.col_ids_by_rlz
        for gname, imt_str, site_id in self.gmvs_per_site:
            rlzs = rlzs_assoc[self.trt_model_id, gname]
            if samples > 1:
                # save only the data for the realization corresponding
                # to the current SESCollection
                rlzs = [rlz for rlz in rlzs if self.col_id in col_ids[rlz]]
            for rlz in rlzs:
                imt_name, sa_period, sa_damping = from_string(imt_str)
                inserter.add(models.GmfData(
                    gmf=models.Gmf.objects.get(lt_realization=rlz.id),
                    task_no=0,
                    imt=imt_name,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    site_id=site_id,
                    gmvs=self.gmvs_per_site[gname, imt_str, site_id],
                    rupture_ids=self.ruptures_per_site[gname, imt_str, site_id]
                ))
        inserter.flush()
        self.gmvs_per_site.clear()
        self.ruptures_per_site.clear()

    def to_haz_curves(self, sids, imtls, invest_time, duration):
        """
        Convert the gmf into hazard curves (by gsim and imt)

        :param sids: database ids of the given sites
        :param imtls: dictionary {IMT: intensity measure levels}
        :param invest_time: investigation time
        :param duration: effective duration (investigation time multiplied
                         by number of SES and number of samples)
        """
        gmf = collections.defaultdict(dict)  # (gsim, imt) > {site_id: poes}
        sorted_imts = map(str, self.sorted_imts)
        zeros = {imt: numpy.zeros(len(imtls[imt])) for imt in sorted_imts}
        for (gsim, imt, site_id), gmvs in self.gmvs_per_site.iteritems():
            gmf[gsim, imt][site_id] = gmvs_to_haz_curve(
                gmvs, imtls[imt], invest_time, duration)
        curves_by_gsim = []
        for gsim_obj in self.sorted_gsims:
            gsim = gsim_obj.__class__.__name__
            curves_by_imt = []
            for imt in sorted_imts:
                curves_by_imt.append(
                    numpy.array([gmf[gsim, imt].get(site_id, zeros[imt])
                                 for site_id in sids]))
            curves_by_gsim.append((gsim, curves_by_imt))
        return curves_by_gsim


@calculators.add('event_based')
class EventBasedHazardCalculator(general.BaseHazardCalculator):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """
    core_calc_task = compute_ruptures

    def initialize_ses_db_records(self, trt_model_id, ordinal):
        """
        Create :class:`~openquake.engine.db.models.Output` and
        :class:`openquake.engine.db.models.SESCollection` records for
        each tectonic region type.

        :param trt_model:
            :class:`openquake.engine.db.models.TrtModel` instance
        :param i:
            an ordinal number starting from 0
        :returns:
            a :class:`openquake.engine.db.models.SESCollection` instance
        """
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name='SES Collection %d' % ordinal,
            output_type='ses')

        trt_model = models.TrtModel.objects.get(pk=trt_model_id)
        ses_coll = models.SESCollection.objects.create(
            output=output, trt_model=trt_model, ordinal=ordinal)

        return ses_coll

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, generating the seeds for the sourcesand building
        SESCollection records for each TrtModel.
        """
        logging.warn('This calculator is deprecated, use oq-engine --lite')
        weights = super(EventBasedHazardCalculator, self).pre_execute()
        hc = self.oqparam
        rnd = random.Random(hc.random_seed)
        for src in self.composite_model.get_sources():
            src.seed = rnd.randint(0, models.MAX_SINT_32)
        info = self.composite_model.get_info()
        for trt_id, idx, col_id in info.get_triples():
            self.initialize_ses_db_records(trt_id, col_id)
        return weights

    def agg_curves(self, acc, result):
        """
        :param result:
            a dictionary {trt_model_id: num_ruptures}

        If the parameter `ground_motion_fields` is set, compute and save
        the GMFs from the ruptures generated by the given task.
        """
        return acc + result

    def post_execute(self, result=None):
        trt_models = models.TrtModel.objects.filter(
            lt_model__hazard_calculation=self.job)
        # save the right number of occurring ruptures
        for trt_model in trt_models:
            trt_model.num_ruptures = self.acc.get(trt_model.id, 0)
            trt_model.save()
        if (not self.oqparam.ground_motion_fields and
                not self.oqparam.hazard_curves_from_gmfs):
            return  # do nothing

        # create a Gmf output for each realization
        self.initialize_realizations()
        if self.oqparam.ground_motion_fields:
            for rlz in self._realizations:
                output = models.Output.objects.create(
                    oq_job=self.job,
                    display_name='GMF rlz-%s' % rlz.id,
                    output_type='gmf')
                models.Gmf.objects.create(output=output, lt_realization=rlz)

        self.acc = self.generate_gmfs_and_curves()
        # now save the curves, if any
        self.save_hazard_curves()

    @EnginePerformanceMonitor.monitor
    def generate_gmfs_and_curves(self):
        """
        Generate the GMFs and optionally the hazard curves too
        """
        sitecol = self.site_collection
        sesruptures = []  # collect the ruptures in a fixed order
        with self.monitor('reading ruptures'):
            for ses_coll in models.SESCollection.objects.filter(
                    trt_model__lt_model__hazard_calculation=self.job):
                for sr in models.SESRupture.objects.filter(
                        rupture__ses_collection=ses_coll):
                    # adding the annotation below saves a LOT of memory
                    # otherwise one would need as key in apply_reduce
                    # lambda sr: sr.rupture.ses_collection.ordinal which would
                    # read the world from the database
                    sr.col_id = ses_coll.ordinal
                    sesruptures.append(sr)
        base_agg = super(EventBasedHazardCalculator, self).agg_curves
        if self.oqparam.hazard_curves_from_gmfs:
            zeros = {key: self.zeros for key in self.rlzs_assoc}
        else:
            zeros = {}
        return tasks.apply_reduce(
            compute_gmfs_and_curves,
            (sesruptures, sitecol, self.rlzs_assoc, self.monitor),
            base_agg, zeros, key=lambda sr: sr.col_id,
            concurrent_tasks=self.concurrent_tasks)
