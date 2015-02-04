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
from openquake.risklib import scientific
from openquake.commonlib import readinput, parallel
from openquake.commonlib.export import export
from openquake.baselib.general import AccumDict

from openquake.commonlib.calculators import base, calc


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


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
    imtls = monitor.oqparam.imtls
    trt_model_id = sources[0].trt_model_id
    trt = sources[0].tectonic_region_type
    gsims = gsims_assoc[trt_model_id]
    result = AccumDict()
    for gsim in gsims:
        curves = calc_hazard_curves(
            sources, sitecol, imtls, {trt: gsim}, truncation_level,
            source_site_filter=source_site_distance_filter(max_dist),
            rupture_site_filter=rupture_site_distance_filter(max_dist))
        # notice that the rupture filter may remove everything
        if sum(v.sum() for v in curves.itervalues()):
            result[trt_model_id, gsim.__class__.__name__] = AccumDict(curves)
    return result


@base.calculators.add('classical')
class ClassicalCalculator(base.HazardCalculator):
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
        zero = AccumDict((key, AccumDict())
                         for key in self.rlzs_assoc)
        gsims_assoc = self.rlzs_assoc.get_gsims_by_trt_id()
        return parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, gsims_assoc, monitor),
            agg=calc.agg_prob, acc=zero,
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

    def post_execute(self, result):
        """
        Collect the hazard curves by realization and export them.

        :param result:
            a dictionary of hazard curves dictionaries
        """
        curves_by_rlz = self.rlzs_assoc.combine(result)
        rlzs = self.rlzs_assoc.realizations
        oq = self.oqparam
        nsites = len(self.sitecol)

        # export curves
        saved = AccumDict()
        exports = oq.exports.split(',')
        for rlz in rlzs:
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = '_'.join(rlz.gsim_lt_path)
            for fmt in exports:
                fname = 'hazard_curve-smltp_%s-gsimltp_%s-ltr_%d.%s' % (
                    smlt_path, gsimlt_path, rlz.ordinal, fmt)
                saved += self.export_curves(curves_by_rlz[rlz], fmt, fname)

        if len(rlzs) == 1:  # cannot compute statistics
            return saved

        weights = (None if oq.number_of_logic_tree_samples
                   else [rlz.weight for rlz in rlzs])
        curves_by_imt = {imt: [curves_by_rlz[rlz][imt] for rlz in rlzs]
                         for imt in oq.imtls}
        mean_curves = scientific.mean_curve(
            [curves_by_rlz[rlz] for rlz in rlzs], weights)
        quantile = {
            q: {imt: scientific.quantile_curve(
                curves_by_imt[imt], q, weights).reshape((nsites, -1))
                for imt in oq.imtls}
            for q in getattr(oq, 'quantile_hazard_curves', [])
        }
        for fmt in exports:
            saved += self.export_curves(
                mean_curves, fmt, 'hazard_curve-mean.%s' % fmt)
            for q in quantile:
                saved += self.export_curves(
                    quantile[q], fmt, 'quantile_curve-%s.%s' % (q, fmt))
        return saved

    def hazard_maps(self, curves_by_imt):
        """
        Compute the hazard maps associated to the curves and returns
        a dictionary of arrays.
        """
        return {imt:
                calc.compute_hazard_maps(
                    curves, self.oqparam.imtls[imt], self.oqparam.poes)
                for imt, curves in curves_by_imt.iteritems()}

    def export_curves(self, curves, fmt, fname):
        """
        :param curves: an array of N curves to export
        :param fmt: the export format ('xml', 'csv', ...)
        :param fname: the name of the exported file
        """
        saved = AccumDict()
        oq = self.oqparam
        export_dir = oq.export_dir
        saved += export(
            ('hazard_curves', fmt), export_dir, fname, self.sitecol, curves,
            oq.imtls, oq.investigation_time)
        if getattr(oq, 'hazard_maps', None):
            hmaps = self.hazard_maps(curves)
            # a dictionary IMT -> matrix(P, N)
            saved += export(
                ('hazard_curves', fmt), export_dir,
                fname.replace('curve', 'map'), self.sitecol,
                {k: v.T for k, v in hmaps.iteritems()},
                oq.imtls, oq.investigation_time)
            if getattr(oq, 'uniform_hazard_spectra', None):
                uhs_curves = calc.make_uhs(hmaps)
                saved += export(
                    ('uhs', fmt), oq.export_dir,
                    fname.replace('curve', 'uhs'),
                    self.sitecol, uhs_curves)
        return saved


@base.calculators.add('disaggregation')
class DisaggregationCalculator(base.HazardCalculator):
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
    result = AccumDict({(0, str(gsim)): AccumDict()
                        for gsim in computer.gsims})
    with monitor:
        for tag, seed in tag_seed_pairs:
            for gsim_str, gmvs in computer.compute(seed):
                result[0, gsim_str][tag] = gmvs
    return result


@base.calculators.add('scenario')
class ScenarioCalculator(base.HazardCalculator):
    """
    Scenario hazard calculator
    """
    core_func = calc_gmfs

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer, tags and seeds
        """
        super(ScenarioCalculator, self).pre_execute()
        self.imts = readinput.get_imts(self.oqparam)
        trunc_level = getattr(self.oqparam, 'truncation_level', None)
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)

        self.tags = ['scenario-%010d' % i for i in xrange(n_gmfs)]
        self.computer = GmfComputer(
            rupture, self.sitecol, self.imts, self.gsims,
            trunc_level, correl_model)
        rnd = random.Random(getattr(self.oqparam, 'random_seed', 42))
        self.tag_seed_pairs = [(tag, rnd.randint(0, calc.MAX_INT))
                               for tag in self.tags]

    def execute(self):
        """
        Compute the GMFs in parallel and return a dictionary key -> imt -> gmfs
        """
        logging.info('Computing the GMFs')
        args = (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs'))
        data = {}
        for (trt_id, gsim), dic in parallel.apply_reduce(
                self.core_func.__func__, args,
                concurrent_tasks=self.oqparam.concurrent_tasks).iteritems():
            data[trt_id, gsim] = {  # build N x R matrices
                imt: numpy.array(
                    [dic[tag][imt] for tag in self.tags]).T
                for imt in map(str, self.imts)}
        return data

    def post_execute(self, result):
        """
        :param result: a dictionary imt -> gmfs
        :returns: a dictionary {('gmf', 'xml'): <gmf.xml filename>}
        """
        logging.info('Exporting the result')
        out = AccumDict()
        for (trt_id, gsim), gmfs_by_imt in result.iteritems():
            fname = '%s_gmf.xml' % gsim
            out += export(
                ('gmf', 'xml'), self.oqparam.export_dir, fname,
                self.sitecol, self.tags, gmfs_by_imt)
        return out
