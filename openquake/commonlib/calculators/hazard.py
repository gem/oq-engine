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

import random
import logging

import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.hazard_curve import hazard_curves
from openquake.hazardlib.calc.filters import source_site_distance_filter, \
    rupture_site_distance_filter
from openquake.commonlib import readinput, parallel
from openquake.baselib.general import AccumDict

from openquake.commonlib.calculators import calculators, base, calc
from openquake.commonlib.export import export


def build_curves(rlz, curves_by_trt_model_gsim):
    """
    Build on the fly the hazard curves for the current realization
    """
    curves = 0
    for trt_model_id, gsim in rlz.items:
        pnes = 1. - curves_by_trt_model_gsim[trt_model_id, gsim]
        curves = 1. - (1. - curves) * pnes
    return curves


def classical(sources, sitecol, gsims_by_trt, monitor):
    """
    :param sources:
    :param sitecol:
    :param gsims_by_trt:
    :param monitor:
    """
    max_dist = monitor.oqparam.maximum_distancee
    truncation_level = monitor.oqparam.truncation_level
    imts = sorted(monitor.oqparam.intensity_measure_types_and_levels)
    trt_model_id = sources[0].trt_model_id
    trt = sources[0].tectonic_region_type
    result = AccumDict()  # (trt_model_id, gsim.__class__.__name__) -> curves
    for gsim in gsims_by_trt[trt]:
        result[trt_model_id, gsim.__class__.__name__] = hazard_curves(
            sources, sitecol, imts, {trt: gsim}, truncation_level,
            source_site_filter=source_site_distance_filter(max_dist),
            rupture_site_filter=rupture_site_distance_filter(max_dist))
    return result


@calculators.add('classical')
class ClassicalCalculator(base.BaseHazardCalculator):
    """
    Classical PSHA calculators
    """
    def post_execute(self, result):
        return {}


@calculators.add('event_based')
class EventBasedCalculator(base.BaseHazardCalculator):
    """
    Event based PSHA calculators
    """
    def post_execute(self, result):
        return {}


@calculators.add('disaggregation')
class DisaggregationCalculator(base.BaseHazardCalculator):
    """
    Classical disaggregation PSHA calculators
    """
    def post_execute(self, result):
        return {}


def calc_gmfs(tag_seed_pairs, computer, monitor):
    """
    Computes several GMFs in parallel, one for each tag and seed.

    :param tag_seed_pairs:
        list of pairs (rupture tag, rupture seed)
    :param computer:
        :class:`openquake.hazardlib.calc.gmf.GMFComputer` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary tag -> {imt: gmf}
    """
    with monitor:
        res = AccumDict()  # tag -> {imt: gmvs}
        for tag, seed in tag_seed_pairs:
            res += {tag: dict(computer.compute(seed))}
    return res


@calculators.add('scenario')
class ScenarioCalculator(base.BaseCalculator):
    """
    Scenario hazard calculator
    """
    core_func = calc_gmfs

    def _init_tags(self):
        self.imts = readinput.get_imts(self.oqparam)
        gsim = readinput.get_gsim(self.oqparam)
        trunc_level = getattr(self.oqparam, 'truncation_level', None)
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)

        self.tags = ['scenario-%010d' % i for i in xrange(n_gmfs)]
        self.computer = GmfComputer(rupture, self.sitecol, self.imts, gsim,
                                    trunc_level, correl_model)
        rnd = random.Random(getattr(self.oqparam, 'random_seed', 42))
        self.tag_seed_pairs = [(tag, rnd.randint(0, calc.MAX_INT))
                               for tag in self.tags]

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer, tags and seeds
        """
        if 'exposure' in self.oqparam.inputs:
            logging.info('Reading the exposure')
            exposure = readinput.get_exposure(self.oqparam)
            logging.info('Reading the site collection')
            self.sitecol, _assets = readinput.get_sitecol_assets(
                self.oqparam, exposure)
        else:
            self.sitecol = readinput.get_site_collection(self.oqparam)
        self._init_tags()

    def execute(self):
        """
        Compute the GMFs in parallel
        """
        logging.info('Computing the GMFs')
        return parallel.apply_reduce(
            self.core_func.__func__,
            (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs')),
            concurrent_tasks=self.oqparam.concurrent_tasks)

    def post_execute(self, result):
        """
        :param result: a dictionary imt -> gmfs
        :returns: a dictionary {'gmf_xml': <gmf.xml filename>}
        """
        logging.info('Exporting the result')
        gmfs_by_imt = {  # build N x R matrices
            imt: numpy.array(
                [result[tag][imt] for tag in self.tags]).T
            for imt in map(str, self.imts)}
        out = export(
            'gmf_xml', self.oqparam.export_dir,
            self.sitecol, self.tags, gmfs_by_imt)
        return out
