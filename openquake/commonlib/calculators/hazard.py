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
import operator
import logging
import collections

import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.filters import source_site_distance_filter, \
    rupture_site_distance_filter
from openquake.commonlib import readinput, parallel
from openquake.commonlib.export import export
from openquake.baselib.general import AccumDict

from openquake.commonlib.calculators import calculators, base, calc


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def agg_prob(acc, prob):
    """
    Aggregation function for probabilities.

    :param acc: the accumulator
    :param prob: the probability (can be an array or more)

    In particular::

       agg_prob(acc, 0) = acc
       agg_prob(acc, 1) = 1
       agg_prob(0, prob) = prob
       agg_prob(1, prob) = 1
       agg_prob(acc, prob) = agg_prob(prob, acc)

       agg_prob(acc, eps) =~ acc + eps for eps << 1
    """
    return 1. - (1. - prob) * (1. - acc)


def classical(sources, sitecol, gsims_assoc, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection
    :param gsims_assoc:
        associations trt_model_id -> gsims
    :param monitor:
        a Monitor instance
    :returns:
        an AccumDict rlz -> curves
    """
    max_dist = monitor.oqparam.maximum_distance
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.intensity_measure_types_and_levels
    trt_model_id = sources[0].trt_model_id
    trt = sources[0].tectonic_region_type
    gsims = gsims_assoc[trt_model_id]
    result = AccumDict()
    for gsim in gsims:
        curves = calc_hazard_curves(
            sources, sitecol, imtls, {trt: gsim}, truncation_level,
            source_site_filter=source_site_distance_filter(max_dist),
            rupture_site_filter=rupture_site_distance_filter(max_dist))
        assert sum(v.sum() for v in curves.itervalues()), 'all zero curves!'
        result[trt_model_id, gsim.__class__.__name__] = AccumDict(curves)
    return result


@calculators.add('classical')
class ClassicalCalculator(base.BaseHazardCalculator):
    """
    Classical PSHA calculator
    """
    core_func = classical

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        sources = list(self.composite_source_model.sources)
        zero = AccumDict((rlz, AccumDict())
                         for rlz in self.rlzs_assoc.realizations)
        gsims_assoc = self.rlzs_assoc.get_gsims_by_trt_id()
        return parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, gsims_assoc, monitor),
            agg=agg_prob, acc=zero,
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

    def post_execute(self, result):
        """
        Collect the hazard curves by realization and export them.

        :param result:
            a dictionary of hazard curves dictionaries
        """
        rlzs = self.rlzs_assoc.realizations
        curves_by_rlz = self.rlzs_assoc.reduce(agg_prob, result)
        oq = self.oqparam

        # export curves
        saved = AccumDict()
        for rlz in rlzs:
            curves = curves_by_rlz[rlz]
            saved += export(
                'hazard_curves_xml',
                oq.export_dir, self.sitecol, rlz, curves,
                oq.imtls, oq.investigation_time)
        return saved


@calculators.add('event_based')
class EventBasedCalculator(base.BaseHazardCalculator):
    """
    Event based PSHA calculator
    """
    def post_execute(self, result):
        return {}


@calculators.add('disaggregation')
class DisaggregationCalculator(base.BaseHazardCalculator):
    """
    Classical disaggregation PSHA calculator
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
        Compute the GMFs in parallel and return a dictionary imt -> gmfs
        """
        logging.info('Computing the GMFs')
        result = parallel.apply_reduce(
            self.core_func.__func__,
            (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs')),
            concurrent_tasks=self.oqparam.concurrent_tasks)
        gmfs_by_imt = {  # build N x R matrices
            imt: numpy.array(
                [result[tag][imt] for tag in self.tags]).T
            for imt in map(str, self.imts)}
        return gmfs_by_imt

    def post_execute(self, result):
        """
        :param result: a dictionary imt -> gmfs
        :returns: a dictionary {'gmf_xml': <gmf.xml filename>}
        """
        logging.info('Exporting the result')
        out = export(
            'gmf_xml', self.oqparam.export_dir,
            self.sitecol, self.tags, result)
        return out
