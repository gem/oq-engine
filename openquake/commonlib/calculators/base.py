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
import itertools
import logging
import operator

import numpy

from openquake.hazardlib.geo import geodetic
from openquake.risklib.workflows import RiskInput

from openquake.commonlib import readinput, general
from openquake.commonlib.parallel import apply_reduce

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_imt = operator.attrgetter('imt')


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""


class BaseCalculator(object):
    """
    Abstract base class for all calculators
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, oqparam, monitor):
        self.oqparam = oqparam
        self.monitor = monitor
        self.monitor.write('operation pid time_sec memory_mb'.split())

    def run(self):
        """
        Run the calculation and return the exported files
        """
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


class BaseRiskCalculator(BaseCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    def build_riskinputs(self, hazards_by_imt):
        """
        :param hazards_by_imt:
            a dictionary IMT -> numpy array of length equal to the
            number of hazard sites associated to the given assets
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        riskinputs = []
        idx_weight_pairs = [(i, len(assets))
                            for i, assets in enumerate(self.assets_by_site)]
        blocks = general.split_in_blocks(
            idx_weight_pairs,
            self.oqparam.concurrent_tasks + 1,
            weight=operator.itemgetter(1))
        for block in blocks:
            idx = numpy.array([idx for idx, _weight in block])
            for imt, hazards_by_site in hazards_by_imt.iteritems():
                taxonomies = self.riskmodel.get_taxonomies(imt)
                hazard_per_asset_group = []
                for hazard, assets in itertools.izip(
                        hazards_by_site[idx], self.assets_by_site[idx]):
                    group = general.group(
                        (a for a in assets if a.taxonomy in taxonomies),
                        get_taxonomy)
                    if group:
                        hazard_per_asset_group.append((hazard, group))
                if hazard_per_asset_group:
                    riskinputs.append(RiskInput(imt, hazard_per_asset_group))
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
                'Could not associated any site to any assets within the '
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
        monitor = self.monitor.copy(self.core_func.__name__)
        monitor._procs = None
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, monitor),
            agg=operator.add,
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight,
            key=get_imt)
