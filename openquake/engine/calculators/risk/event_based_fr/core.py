#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
This is an experimental calculator. It is not intended for general use, it is
for experimentation purposes. It is expected to change heavily in the near
future. DO NOT USE IT.
"""

import operator
import itertools
import collections
import numpy

from django import db

from openquake.engine.calculators.hazard.event_based.core \
    import EventBasedHazardCalculator as EBHC

from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import FilteredSiteCollection
from openquake.hazardlib.calc.gmf import GmfComputer

from openquake.commonlib.general import split_in_blocks
from openquake.commonlib.logictree import SourceModelLogicTree, GSIM

from openquake.risklib import scientific

from openquake.engine import logs

from openquake.engine.calculators.risk.event_based_risk import core
from openquake.engine.calculators.risk import writers


class AssetSiteAssociationError(Exception):
    pass


def split_site_collection(sitecol, num_chunks):
    """
    Split the full site collection in several FilteredSiteCollections

    :param sitecol: full site collection
    :param num_chunks: hint for the number of blocks to generate
    """
    for indices in split_in_blocks(sitecol.indices, num_chunks):
        yield FilteredSiteCollection(indices, sitecol)


@tasks.oqtask
def event_based_fr(job_id, sites, rc, risk_models,
                   getter_builders, outputdict, params):
    """
    :param int job_id:
        ID of the currently running job
    :param rc:
        a :class:`openquake.engine.db.models.RiskCalculation` instance
    :param risk_models:
        a list of RiskModel instances corresponding to the taxonomy
    :param getter_builders:
        a list of GetterBuilder instances associated to the risk models
    :param outputdict:
        an instance of :class:`..writers.OutputDict` containing
        output container instances (e.g. a LossCurve)
    :param params:
        an instance of :class:`..base.CalcParams` used to compute
        derived outputs
    """
    hc = rc.hazard_calculation
    site_ids = set(sites.complete.sids)
    truncation_level = hc.truncation_level
    sorted_imts = sorted(map(from_string, hc.intensity_measure_types))

    # init the Epsilon Provider only once
    for builder in getter_builders:
        builder.init_epsilon_provider(asset_correlation=0)

    # TODO: the following monitors should be replaced by LightMonitors,
    # since they write a lot on the database, once per asset
    getdata_mon = EnginePerformanceMonitor(
        'getting hazard', job_id, event_based_fr)
    getters_mon = getdata_mon.copy('building getters')

    assocs = models.AssocLtRlzTrtModel.objects.filter(
        trt_model__lt_model__hazard_calculation=hc.oqjob).order_by('rlz')

    # mapping realization -> [(trt_model, gsim)]
    rlz2gsims = {
        rlz: [(a.trt_model, GSIM[a.gsim]()) for a in group]
        for rlz, group in itertools.groupby(
            assocs, operator.attrgetter('rlz'))}

    # building the getters, i.e. initialize .gmv_dict and .hid
    with getters_mon:
        for builder in getter_builders:
            builder.init_getters(sorted_imts, rlz2gsims)

    for builder in getter_builders:
        for getter in builder.getters:
            for gsim, trt_model in zip(getter.gsims, getter.trt_models):
                # read the ruptures from the db
                with getdata_mon.copy('reading ruptures'):
                    ses_ruptures = models.SESRupture.objects.filter(
                        rupture__trt_model=trt_model)

                with getdata_mon.copy('generating gmf'):
                    # NB: the ruptures are already ordered by tag
                    # and therefore by '.rupture'
                    for rupture, group in itertools.groupby(
                            ses_ruptures, operator.attrgetter('rupture')):
                        if rupture.site_indices is None:
                            r_sites = sites
                        else:
                            r_sites = FilteredSiteCollection(
                                rupture.site_indices, sites.complete)
                            if not site_ids.intersection(r_sites.sids):
                                continue  # skip ruptures not contributing

                        # populating the gmv_dicts for each getter
                        getter.build_data(
                            rupture, r_sites, [(r.id, r.seed) for r in group],
                            truncation_level)

        # computing risk
        elt = {}  # event loss table
        with db.transaction.commit_on_success(using='job_init'):
            for risk_model, builder in zip(risk_models, getter_builders):
                elt.update(
                    core.do_event_based(
                        risk_model, builder.getters,
                        outputdict, params, getdata_mon))
    return elt


class EventBasedFRRiskCalculator(core.EventBasedRiskCalculator):

    def pre_execute(self):
        """
        Inherited from core.EventBasedRiskCalculator.pre_execute.
        Enforces no correlation, both on GMFs and assets.
        """
        correl_model = models.get_correl_model(self.job)
        assert correl_model is None, correl_model
        assert not self.rc.asset_correlation, self.rc.asset_correlation
        core.EventBasedRiskCalculator.pre_execute(self)

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Method responsible for the distribution strategy. It divides
        the considered exposure into chunks of homogeneous assets
        (i.e. having the same taxonomy).
        """
        # create a Gmf output for each realization
        self.hcalc = EBHC(self.hc.oqjob)
        self.hcalc.source_model_lt = SourceModelLogicTree.from_hc(self.hc)
        with db.transaction.commit_on_success(using='job_init'):
            # TODO: think about how to remove the need for .delete()
            # one should retrieve only the latest realizations
            # for a given hazard calculation; alternatively, the
            # realizations should be associated to RiskCalculation,
            # not to HazardCalculation
            models.LtRealization.objects.filter(
                lt_model__hazard_calculation=self.job).delete()
            self.hcalc.initialize_realizations()
            for rlz in self.hcalc._get_realizations():
                output = models.Output.objects.create(
                    oq_job=self.job,
                    display_name='GMF rlz-%s' % rlz.id,
                    output_type='gmf')
                models.Gmf.objects.create(output=output, lt_realization=rlz)
        self.compute_risk()

    def compute_risk(self):
        """
        Generate the GMFs and optionally the hazard curves too, then
        compute the risk.
        """
        getter_builders = []
        risk_models = []
        with self.monitor('associating assets<->sites'):
            for risk_model in self.risk_models.itervalues():
                logs.LOG.info('associating assets<->sites for taxonomy %s',
                              risk_model.taxonomy)
                try:
                    with db.transaction.commit_on_success(using='job_init'):
                        gbuilder = GetterBuilder(self.rc, risk_model.taxonomy)
                        getter_builders.append(gbuilder)
                        risk_models.append(risk_model)
                except AssetSiteAssociationError as e:
                    logs.LOG.warn(str(e))
                    continue

        # notice that here the commit is really needed, since
        # combine_builders save the loss curve containers on the db
        with db.transaction.commit_on_success(using='job_init'):
            outputdict = writers.combine_builders(
                [ob(self) for ob in self.output_builders])

        args = []
        # compute the risk by splitting by sites
        for sites in split_site_collection(
                self.hc.site_collection, self.concurrent_tasks):
            args.append((self.job.id, sites, self.rc,
                         risk_models, getter_builders, outputdict,
                         self.calculator_parameters))
        self.acc = tasks.map_reduce(event_based_fr, args, self.agg_result, {})


class GmfGetter(object):
    """
    Hazard getter for computing ground motion values and epsilons from ruptures
    """
    def __init__(self, builder, lt_rlz, gmv_dict, sorted_imts,
                 trt_models, gsims):
        self.builder = builder
        self.rlz = lt_rlz
        self.rupture_ids = []
        self.seeds = []
        self.gmv_dict = gmv_dict
        self.sorted_imts = sorted_imts
        self.trt_models = trt_models
        self.gsims = gsims
        self.hid = models.Gmf.objects.get(lt_realization=lt_rlz).output.id

    @property
    def weight(self):
        return self.rlz.weight

    @property
    def site_ids(self):
        return self.builder.site_ids

    @property
    def assets(self):
        return self.builder.assets

    def get_epsilons(self):
        """
        Build the needed epsilon matrix from the given assets and seeds,
        by using the underlying epsilon provider.
        """
        return self.builder.epsilon_provider.sample(self.seeds)

    def build_data(self, rupture, sitecol, rupid_seed_pairs,
                   truncation_level=None, correl_model=None):
        """
        :param rupture:
            a ProbabilisticRupture instance
        :param sitecol:
            the collections of sites where to compute the GMFs
        :param rupid_seed_pairs:
            [(r.id, r.seed), ...] for each SESRupture associated the rupture
        :param truncation_level:
            the truncation level (or None)
        :param correl_model:
            the correlation model (or None)
        """
        c = GmfComputer(rupture, sitecol, self.sorted_imts, self.gsims,
                        truncation_level, correl_model)
        for rupid, seed in rupid_seed_pairs:
            self.rupture_ids.append(rupid)
            self.seeds.append(seed)
            for (gsim_name, imt), gmvs in c.compute(seed):
                for site_id, gmv in zip(sitecol.sids, gmvs):
                    self.gmv_dict[imt][site_id][rupid] = gmv

    def get_data(self, imt):
        """
        Extracts the GMFs for the given `imt` from the .gmv_dict

        :param str imt: Intensity Measure Type
        :returns: a list of N arrays with R elements each.
        """
        gmv_dict = self.gmv_dict[imt]
        all_gmvs = []
        hits = 0  # how many sites are affected by the current ruptures
        for site_id in self.site_ids:
            gmv = gmv_dict[site_id]
            if gmv:
                hits += 1
            array = numpy.array([gmv.get(r, 0.) for r in self.rupture_ids])
            all_gmvs.append(array)
        if not hits:
            # the rupture will affect assets of another taxonomy
            logs.LOG.info('No assets affected by %r', self)
        return all_gmvs

    def __repr__(self):
        """
        A string representation of the GmfGetter display a few interesting
        attributes, such as the taxonomy, the ruptures, the realization and
        the number of GMVs it contains.
        """
        num_gmvs = 0
        for imt, gmv_dict in self.gmv_dict.iteritems():
            for site_id, gmv in gmv_dict.iteritems():
                num_gmvs += len(gmv)
        rupids = ', '.join(map(str, self.rupture_ids))
        return '<%s(taxonomy=%s, rupture=%s, rlz=%d) with %d nonzero ' \
            'elements>' % (self.__class__.__name__, self.builder.taxonomy,
                           rupids, self.rlz.id, num_gmvs)


class GetterBuilder(object):
    """
    A class used to instantiate GmfGetter objects.
    """
    # instantiated on the controller node, initialized on the workers
    def __init__(self, rc, taxonomy):
        self.rc = rc
        self.taxonomy = taxonomy
        cursor = models.getcursor('job_init')
        query = '''\
    SELECT exp.id AS asset_id, hsite.id AS site_id
    FROM riski.exposure_data AS exp
    JOIN hzrdi.hazard_site AS hsite
    ON exp.site::TEXT=hsite.location::TEXT
    WHERE hsite.hazard_calculation_id = %s
    AND exposure_model_id = %s AND taxonomy=%s
    AND ST_COVERS(ST_GeographyFromText(%s), exp.site)'''
        args = (rc.hazard_calculation.oqjob.id, rc.exposure_model.id, taxonomy,
                rc.region_constraint.wkt)
        # print cursor.mogrify(query, args) useful when debugging
        cursor.execute(query, args)
        assets_sites = cursor.fetchall()
        if not assets_sites:
            raise AssetSiteAssociationError(
                'Could not associated any asset of taxonomy %s' % taxonomy)
        self.asset_ids, self.site_ids = zip(*assets_sites)
        self.assets = models.ExposureData.objects.get_asset_chunk(
            rc, taxonomy, asset_ids=self.asset_ids)

    def init_epsilon_provider(self, asset_correlation):
        """
        Initialize the underlying EpsilonProvider. If there is
        asset_correlation, a correlation matrix is instantiated.
        """
        self.epsilon_provider = scientific.EpsilonProvider(
            len(self.assets), asset_correlation)

    def init_getters(self, sorted_imts, rlz2gsims):
        """
        Build the getters for the given realizations by using the
        given rupid_seed_pairs and the parameters in the GetterBuilder.
        """
        self.getters = []
        for rlz, pairs in rlz2gsims.iteritems():
            gmv_dict = dict(
                (str(imt), collections.defaultdict(dict))
                for imt in sorted_imts)
            trt_models, gsims = zip(*sorted(pairs))
            self.getters.append(
                GmfGetter(self, rlz, gmv_dict, sorted_imts, trt_models, gsims))
