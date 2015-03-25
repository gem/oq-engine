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

import os
import abc
import logging
import operator
import collections
import cPickle

import numpy

from openquake.hazardlib.geo import geodetic

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.parallel import apply_reduce, DummyMonitor, executor
from openquake.risklib import riskinput

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('trt_model_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""


class BaseCalculator(object):
    """
    Abstract base class for all calculators.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, oqparam, monitor=DummyMonitor()):
        self.oqparam = oqparam
        self.monitor = monitor
        if not hasattr(oqparam, 'concurrent_tasks'):
            oqparam.concurrent_tasks = executor.num_tasks_hint
        if not hasattr(oqparam, 'usecache'):
            oqparam.usecache = False

    def run(self, **kw):
        """
        Run the calculation and return the saved output.
        """
        self.monitor.write('operation pid time_sec memory_mb'.split())
        vars(self.oqparam).update(kw)
        self.pre_execute()
        result = self.execute()
        exported = self.post_execute(result)
        for item in sorted(exported.iteritems()):
            logging.info('exported %s: %s', *item)
        return self.save_pik(result, exported=exported)

    def core_func(*args):
        """
        Core routine running on the workers.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def pre_execute(self):
        """
        Initialization phase.
        """

    @abc.abstractmethod
    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        function and return a dictionary with the results.
        """

    @abc.abstractmethod
    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code. It will return a dictionary
        of output files.
        """

    @abc.abstractmethod
    def save_pik(self, result, **kw):
        """
        Called after post_execute
        """


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    prefilter = True  # filter the sources before splitting them
    mean_curves = None  # to be overridden
    result_kind = None  # to be overridden

    def pre_execute(self):
        """
        Read the site collection and the sources.
        """
        if 'exposure' in self.oqparam.inputs:
            logging.info('Reading the exposure')
            exposure = readinput.get_exposure(self.oqparam)
            self.sitecol, self.assets_by_site = readinput.get_sitecol_assets(
                self.oqparam, exposure)
        else:
            logging.info('Reading the site collection')
            self.sitecol = readinput.get_site_collection(self.oqparam)
        if 'source' in self.oqparam.inputs:
            logging.info('Reading the composite source models')
            self.composite_source_model = readinput.get_composite_source_model(
                self.oqparam, self.sitecol, self.prefilter)
            self.job_info = readinput.get_job_info(
                self.oqparam, self.composite_source_model, self.sitecol)
            # we could manage limits here
            if self.prefilter:
                self.rlzs_assoc = self.composite_source_model.get_rlzs_assoc()
            else:
                self.rlzs_assoc = riskinput.FakeRlzsAssoc(0)
        else:  # calculators without sources, i.e. scenario
            self.gsims = readinput.get_gsims(self.oqparam)
            self.rlzs_assoc = riskinput.FakeRlzsAssoc(len(self.gsims))

    def save_pik(self, result, **kw):
        """
        Must be run at the end of post_execute. Returns a dictionary
        with the saved results.

        :param result: the output of the `execute` method
        :param kw: extras to add to the output dictionary
        :returns: a dictionary with the saved data
        """
        haz_out = dict(rlzs_assoc=self.rlzs_assoc,
                       sitecol=self.sitecol, oqparam=self.oqparam)
        haz_out[self.result_kind] = result
        haz_out.update(kw)
        cache = os.path.join(self.oqparam.export_dir, 'hazard.pik')
        logging.info('Saving hazard output on %s', cache)
        with open(cache, 'w') as f:
            cPickle.dump(haz_out, f)
        return haz_out


def get_hazard(calculator, exports=''):
    """
    Get the hazard from a calculator, possibly by using cached results

    :param calculator: a calculator with a .hazard_calculator attribute
    :returns: a pair (hazard output, hazard_calculator)
    """
    cache = os.path.join(calculator.oqparam.export_dir, 'hazard.pik')
    if calculator.oqparam.usecache:
        with open(cache) as f:
            haz_out = cPickle.load(f)
    else:
        hcalc = calculators[calculator.hazard_calculator](
            calculator.oqparam, calculator.monitor('hazard'))
        haz_out = hcalc.run(exports=exports)

    return haz_out, hcalc


class RiskCalculator(BaseCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    hazard_calculator = None  # to be ovverriden in subclasses
    rlzs_assoc = None  # to be ovverriden in subclasses

    def make_eps_dict(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        return riskinput.make_eps_dict(
            self.assets_by_site, num_ruptures,
            getattr(oq, 'master_seed', 0),  # for compatibility with the engine
            getattr(oq, 'asset_correlation', 0))

    def build_riskinputs(self, hazards_by_key, eps_dict):
        """
        :param hazards_by_key:
            a dictionary key -> IMT -> array of length num_sites
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        riskinputs = []
        idx_weight_pairs = [(i, len(assets))
                            for i, assets in enumerate(self.assets_by_site)]
        blocks = general.split_in_blocks(
            idx_weight_pairs,
            self.oqparam.concurrent_tasks or 1,
            weight=operator.itemgetter(1))
        for block in blocks:
            idx = numpy.array([idx for idx, _weight in block])
            reduced_assets = self.assets_by_site[idx]
            reduced_eps = {}  # for the assets belonging to the idx array
            if eps_dict:
                for assets in reduced_assets:
                    for asset in assets:
                        reduced_eps[asset.id] = eps_dict[asset.id]

            # collect the hazards by key into hazards by imt
            hdata = collections.defaultdict(lambda: [{} for _ in idx])
            for key, hazards_by_imt in hazards_by_key.iteritems():
                for imt, hazards_by_site in hazards_by_imt.iteritems():
                    for i, haz in enumerate(hazards_by_site[idx]):
                        hdata[imt][i][key] = haz

            # build the riskinputs
            for imt in hdata:
                ri = self.riskmodel.build_input(
                    imt, hdata[imt], reduced_assets, reduced_eps)
                if ri.weight > 0:
                    riskinputs.append(ri)
        logging.info('Built %d risk inputs', len(riskinputs))
        return sorted(riskinputs, key=self.riskinput_key)

    def riskinput_key(self, ri):
        """
        :param ri: riskinput object
        :returns: the IMT associated to it
        """
        return ri.imt

    def assoc_assets_sites(self, sitecol):
        """
        :param sitecol: a sequence of sites
        :returns: a pair (sitecollection, assets_by_site)

        The new site collection is different from the original one
        if some assets were discarded because of the maximum_distance
        or if there were missing assets for some sites.
        """
        maximum_distance = self.oqparam.maximum_distance

        def getlon(site):
            return site.location.longitude

        def getlat(site):
            return site.location.latitude

        siteobjects = geodetic.GeographicObjects(sitecol, getlon, getlat)
        assets_by_sid = general.AccumDict()
        for assets in self.assets_by_site:
            # assets is a non-empty list of assets on the same location
            lon, lat = assets[0].location
            site = siteobjects.get_closest(lon, lat, maximum_distance)
            if site:
                assets_by_sid += {site.id: assets}
        if not assets_by_sid:
            raise AssetSiteAssociationError(
                'Could not associate any site to any assets within the '
                'maximum distance of %s km' % maximum_distance)
        mask = numpy.array([sid in assets_by_sid for sid in sitecol.sids])
        assets_by_site = [assets_by_sid[sid] for sid in sitecol.sids
                          if sid in assets_by_sid]
        filteredcol = sitecol.filter(mask)
        return filteredcol, numpy.array(assets_by_site)

    def pre_execute(self):
        """
        Set the attributes .riskmodel, .sitecol, .assets_by_site
        """
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        self.exposure = readinput.get_exposure(self.oqparam)
        logging.info('Read an exposure with %d assets of %d taxonomies',
                     len(self.exposure.assets), len(self.exposure.taxonomies))
        missing = self.exposure.taxonomies - set(
            self.riskmodel.get_taxonomies())
        if missing:
            raise RuntimeError('The exposure contains the taxonomies %s '
                               'which are not in the risk model' % missing)
        self.sitecol, self.assets_by_site = readinput.get_sitecol_assets(
            self.oqparam, self.exposure)
        logging.info('Extracted %d unique sites from the exposure',
                     len(self.sitecol))

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_func` to be defined with signature
        (riskinputs, riskmodel, monitor).
        """
        monitor = self.monitor(self.core_func.__name__)
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight, key=self.riskinput_key)

    def save_pik(self, result, **kw):
        """Save the risk outputs"""
        risk_out = dict(oqparam=self.oqparam)
        risk_out[self.result_kind] = result
        risk_out.update(kw)
        cache = os.path.join(self.oqparam.export_dir, 'risk.pik')
        logging.info('Saving risk output on %s', cache)
        with open(cache, 'w') as f:
            cPickle.dump(risk_out, f)
        return risk_out
