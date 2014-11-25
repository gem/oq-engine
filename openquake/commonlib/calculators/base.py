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

import abc
import logging
import operator

import numpy

from openquake.hazardlib.geo import geodetic

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.parallel import apply_reduce, DummyMonitor

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('trt_model_id')
get_imt = operator.attrgetter('imt')


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""


class BaseCalculator(object):
    """
    Abstract base class for all calculators
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, oqparam, monitor=DummyMonitor()):
        self.oqparam = oqparam
        self.monitor = monitor

    def run(self):
        """
        Run the calculation and return the exported files
        """
        self.monitor.write('operation pid time_sec memory_mb'.split())
        self.pre_execute()
        result = self.execute()
        return self.post_execute(result)

    def core_func(*args):
        """
        Core routine running on the workers, usually set by the
        @core decorator.
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


class BaseHazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    def pre_execute(self):
        """
        Read the site collection and the sources.
        """
        if 'exposure' in self.oqparam.inputs:
            logging.info('Reading the exposure')
            exposure = readinput.get_exposure(self.oqparam)
            self.sitecol, _assets = readinput.get_sitecol_assets(
                self.oqparam, exposure)
        else:
            logging.info('Reading the site collection')
            self.sitecol = readinput.get_site_collection(self.oqparam)
        logging.info('Reading the effective source models')
        source_models = list(
            readinput.get_effective_source_models(self.oqparam, self.sitecol))
        self.all_sources = [src for src_model in source_models
                            for trt_model in src_model.trt_models
                            for src in trt_model]
        self.job_info = readinput.get_job_info(
            self.oqparam, source_models, self.sitecol)
        # we could manage limits here

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        return apply_reduce(
            self.core_func.__func__,
            (self.all_sources, self.site_collection, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight,
            key=get_trt)


class BaseRiskCalculator(BaseCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    def build_riskinputs(self, hazards_by_imt):
        """
        :param hazards_by_imt:
            a dictionary IMT -> array of length equal to the  number of sites
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
            for imt, hazards_by_site in hazards_by_imt.iteritems():
                ri = self.riskmodel.build_input(
                    imt, hazards_by_site[idx], self.assets_by_site[idx])
                if ri.weight > 0:
                    riskinputs.append(ri)
        logging.info('Built %d risk inputs', len(riskinputs))
        return sorted(riskinputs, key=get_imt)

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
            (self.riskinputs, self.riskmodel, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight,
            key=get_imt)
