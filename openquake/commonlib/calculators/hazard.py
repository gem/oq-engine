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

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.filters import source_site_distance_filter, \
    rupture_site_distance_filter
from openquake.commonlib import readinput, parallel, hazard_writers
from openquake.baselib.general import AccumDict

from openquake.commonlib.calculators import calculators, base, calc
from openquake.commonlib.export import export


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def write_hazard_curves(oqparam, sitecol, rlz, curves):
    """
    """
    smlt_path = '_'.join(rlz.sm_lt_path)
    gsimlt_path = '_'.join(rlz.gsim_lt_path)
    mdata = []
    hcurves = []
    for imt, imls in sorted(
            oqparam.intensity_measure_types_and_levels.iteritems()):
        hcurves.append(
            [HazardCurve(site.location, poes)
             for site, poes in zip(sitecol, curves[imt])])
        i = from_string(imt)
        mdata.append({
            'quantile_value': None,
            'statistics': None,
            'smlt_path': smlt_path,
            'gsimlt_path': gsimlt_path,
            'investigation_time': oqparam.investigation_time,
            'imt': imt,
            'sa_period': i[1],
            'sa_damping': i[2],
            'imls': imls,
        })
    dest = 'rlz%d.xml' % rlz.ordinal
    hazard_writers.MultiHazardCurveXMLWriter(dest, mdata).serialize(hcurves)
    return dest


def all_equal(obj, value):
    """
    :param obj: a numpy array or something else
    :param value: a numeric value
    :returns: a boolean
    """
    eq = (obj == value)
    if isinstance(eq, numpy.ndarray):
        return eq.all()
    else:
        return eq


def agg_prob(acc, prob):
    """
    Aggregation function for probabilities.

    :param acc: the accumulator
    :param prob: the probability (can be an array or more)

    In particular

    >> agg_prob(acc, 0) = acc
    >> agg_prob(acc, 1) = 1
    >> agg_prob(0, prob) = prob
    >> agg_prob(1, prob) = 1
    >> agg_prob(acc, prob) = agg_prob(prob, acc)

    >> agg_prob(acc, eps) = ~ acc + eps for eps << 1
    """
    return 1 - (1 - prob) * (1 - acc)


def classical(sources, sitecol, trt_gsims, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection
    :param trt_gsims:
        a dictionary trt_model_id -> (trt, gsims)
    :param monitor:
        a Monitor instance
    :returns:
        an AccumDict (trt_model_id, gsim_name) -> curves
    """
    max_dist = monitor.oqparam.maximum_distance
    truncation_level = monitor.oqparam.truncation_level
    imtls = monitor.oqparam.intensity_measure_types_and_levels
    trt_model_id = sources[0].trt_model_id
    trt, gsims = trt_gsims[trt_model_id]
    result = AccumDict()  # trt_model_id, gsim_name -> curves
    for gsim in gsims:
        curves = calc_hazard_curves(
            sources, sitecol, imtls, {trt: gsim}, truncation_level,
            source_site_filter=source_site_distance_filter(max_dist),
            rupture_site_filter=rupture_site_distance_filter(max_dist))
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
        zero = AccumDict(
            ((trt_id, gsim.__class__.__name__), AccumDict())
            for trt_id, (trt, gsims) in self.ltp.trt_gsims.iteritems()
            for gsim in gsims)
        return parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, self.ltp.trt_gsims, monitor),
            agg=agg_prob, acc=zero,
            concurrent_tasks=self.oqparam.concurrent_tasks or 1,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

    def post_execute(self, result):
        saved = AccumDict()
        acc = AccumDict()  # rlz_idx -> curves
        for (trt_model_id, gsim_name), curves in result.iteritems():
            try:
                idx = self.ltp.rlz_idx[trt_model_id, gsim_name]
            except KeyError:
                # some realizations may be missing when sampling is enabled
                assert self.oqparam.number_of_logic_tree_samples > 0
                continue
            acc = agg_prob(acc, AccumDict({idx: curves}))
        for idx in sorted(acc):
            rlz = self.ltp.realizations[idx]
            saved += self.export(rlz, acc[idx])
        return saved

    def export(self, rlz, curves):
        return {rlz.ordinal: write_hazard_curves(
            self.oqparam, self.sitecol, rlz, curves)}


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
