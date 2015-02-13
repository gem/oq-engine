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
import cPickle

import numpy

from openquake.hazardlib.geo import geodetic

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.parallel import apply_reduce, DummyMonitor, executor
from openquake.risklib import workflows

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

    def run(self):
        """
        Run the calculation and return the exported files.
        """
        self.monitor.write('operation pid time_sec memory_mb'.split())
        self.pre_execute()
        result = self.execute()
        return self.post_execute(result)

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


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    prefilter = True  # filter the sources before splitting them

    def pre_execute(self):
        """
        Read the site collection and the sources.
        """
        if 'exposure' in self.oqparam.inputs:
            logging.info('Reading the exposure')
            exposure = readinput.get_exposure(self.oqparam)
            self.sitecol, self.assets = readinput.get_sitecol_assets(
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
            self.rlzs_assoc = self.composite_source_model.get_rlzs_assoc()
        else:  # calculators without sources, i.e. scenario
            self.gsims = readinput.get_gsims(self.oqparam)
            self.rlzs_assoc = workflows.FakeRlzsAssoc(len(self.gsims))


def get_hazard(calculator, post_execute=False):
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
        hcalc.pre_execute()
        result = hcalc.execute()
        if post_execute:
            for item in sorted(hcalc.post_execute(result).iteritems()):
                logging.info('exported %s: %s', *item)

        haz_out = dict(result=result, rlzs_assoc=hcalc.rlzs_assoc,
                       sitecol=hcalc.sitecol)
        logging.info('Saving hazard output on %s', cache)
        with open(cache, 'w') as f:
            cPickle.dump(haz_out, f)
    return haz_out, hcalc


class RiskCalculator(BaseCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    hazard_calculator = None  # to be ovverriden in subclasses
    rlzs_assoc = None  # to be ovverriden in subclasses

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
            (self.riskinputs, self.riskmodel, self.rlzs_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight,
            key=get_imt)
