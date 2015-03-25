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
import logging
import operator
import collections
from functools import partial
import numpy

from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.filters import source_site_distance_filter, \
    rupture_site_distance_filter
from openquake.risklib import scientific
from openquake.commonlib import parallel
from openquake.commonlib.export import export
from openquake.baselib.general import AccumDict, split_in_blocks, groupby

from openquake.commonlib.calculators import base, calc


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def classical(sources, sitecol, gsims_assoc, monitor):
    """
    :param sources:
        a non-empty sequence of sources of homogeneous tectonic region type
    :param sitecol:
        a SiteCollection instance
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
            result[trt_model_id, str(gsim)] = AccumDict(curves)
    return result


@base.calculators.add('classical')
class ClassicalCalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_func = classical
    result_kind = 'curves_by_trt_gsim'

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

    def _fix_empty_curves(self, curves_by_trt_gsim):
        imtls = self.oqparam.imtls
        n = len(self.sitecol)
        for curves_by_imt in curves_by_trt_gsim.itervalues():
            if not curves_by_imt:
                for imt in imtls:
                    curves_by_imt[imt] = numpy.zeros((n, len(imtls[imt])))

    def post_execute(self, result):
        """
        Collect the hazard curves by realization and export them.

        :param result:
            a nested dictionary (trt_id, gsim) -> IMT -> hazard curves
        """
        self._fix_empty_curves(result)
        curves_by_rlz = self.rlzs_assoc.combine(result)
        rlzs = self.rlzs_assoc.realizations
        oq = self.oqparam
        nsites = len(self.sitecol)

        saved = AccumDict()
        if not oq.exports:
            return saved

        # export curves
        exports = oq.exports.split(',')
        if getattr(oq, 'individual_curves', True):
            for rlz in rlzs:
                smlt_path = '_'.join(rlz.sm_lt_path)
                suffix = ('-ltr_%d' % rlz.ordinal
                          if oq.number_of_logic_tree_samples else '')
                for fmt in exports:
                    fname = 'hazard_curve-smltp_%s-gsimltp_%s%s.%s' % (
                        smlt_path, rlz.gsim_rlz.uid, suffix, fmt)
                    saved += self.export_curves(curves_by_rlz[rlz], fmt, fname)
        if len(rlzs) == 1:  # cannot compute statistics
            [self.mean_curves] = curves_by_rlz.values()
            return saved

        weights = (None if oq.number_of_logic_tree_samples
                   else [rlz.weight for rlz in rlzs])
        curves_by_imt = {imt: [curves_by_rlz[rlz][imt] for rlz in rlzs]
                         for imt in oq.imtls}
        mean = getattr(oq, 'mean_hazard_curves', None)
        if mean:
            self.mean_curves = scientific.mean_curve(
                [curves_by_rlz[rlz] for rlz in rlzs], weights)
        self.quantile = {
            q: {imt: scientific.quantile_curve(
                curves_by_imt[imt], q, weights).reshape((nsites, -1))
                for imt in oq.imtls}
            for q in getattr(oq, 'quantile_hazard_curves', [])
        }
        for fmt in exports:
            if mean:
                saved += self.export_curves(
                    self.mean_curves, fmt, 'hazard_curve-mean.%s' % fmt)
            for q in self.quantile:
                saved += self.export_curves(
                    self.quantile[q], fmt, 'quantile_curve-%s.%s' % (q, fmt))
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
        if hasattr(self, 'tileno'):
            fname += self.tileno
        saved = AccumDict()
        oq = self.oqparam
        export_dir = oq.export_dir
        saved += export(
            ('hazard_curves', fmt), export_dir, fname, self.sitecol, curves,
            oq.imtls, oq.investigation_time)
        if getattr(oq, 'hazard_maps', None):
            hmaps = self.hazard_maps(curves)
            saved += export(
                ('hazard_curves', fmt), export_dir,
                fname.replace('curve', 'map'), self.sitecol,
                # hmaps is a dictionary IMT -> matrix(P, N)
                {k: v.T for k, v in hmaps.iteritems()},
                oq.imtls, oq.investigation_time)
            if getattr(oq, 'uniform_hazard_spectra', None):
                uhs_curves = calc.make_uhs(hmaps)
                saved += export(
                    ('uhs', fmt), oq.export_dir,
                    fname.replace('curve', 'uhs'),
                    self.sitecol, uhs_curves)
        return saved


def is_effective_trt_model(result_dict, trt_model):
    """
    Returns True on tectonic region types
    which ID in contained in the result_dict.

    :param result_dict: a dictionary with keys (trt_id, gsim)
    """
    return any(trt_model.id == trt_id for trt_id, _gsim in result_dict)


def classical_tiling(calculator, sitecol, tileno):
    """
    :param calculator:
        a ClassicalCalculator instance
    :param sitecol:
        a SiteCollection instance
    :param tileno:
        the number of the current tile
    :returns:
        a dictionary file name -> full path for each exported file
    """
    calculator.sitecol = sitecol
    calculator.tileno = '.%04d' % tileno
    result = calculator.execute()
    # build the correct realizations from the (reduced) logic tree
    calculator.rlzs_assoc = calculator.composite_source_model.get_rlzs_assoc(
        partial(is_effective_trt_model, result))
    n_levels = sum(len(imls) for imls in calculator.oqparam.imtls.itervalues())
    tup = len(calculator.sitecol), n_levels, len(calculator.rlzs_assoc)
    logging.info('Processed tile %d, (sites, levels, keys)=%s', tileno, tup)
    # export the calculator outputs
    saved = calculator.post_execute(result)
    return saved


@base.calculators.add('classical_tiling')
class ClassicalTilingCalculator(ClassicalCalculator):
    """
    Classical Tiling calculator
    """
    prefilter = False
    result_kind = 'pathname_by_fname'

    def execute(self):
        """
        Split the computation by tiles which are run in parallel.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        self.tiles = map(SiteCollection, split_in_blocks(
            self.sitecol, self.oqparam.concurrent_tasks or 1))
        self.oqparam.concurrent_tasks = 0
        calculator = ClassicalCalculator(self.oqparam, monitor)
        calculator.composite_source_model = self.composite_source_model
        calculator.rlzs_assoc = self.composite_source_model.get_rlzs_assoc(
            lambda tm: True)  # build the full logic tree
        all_args = [(calculator, tile, i)
                    for (i, tile) in enumerate(self.tiles)]
        return parallel.starmap(classical_tiling, all_args).reduce()

    def post_execute(self, result):
        """
        Merge together the exported files for each tile.

        :param result: a dictionary key -> exported filename
        """
        # group files by name; for instance the file names
        # ['quantile_curve-0.1.csv.0000', 'quantile_curve-0.1.csv.0001',
        # 'hazard_map-mean.csv.0000', 'hazard_map-mean.csv.0001']
        # are grouped in the dictionary
        # {'quantile_curve-0.1.csv': ['quantile_curve-0.1.csv.0000',
        #                             'quantile_curve-0.1.csv.0001'],
        # 'hazard_map-mean.csv': ['hazard_map-mean.csv.0000',
        #                         'hazard_map-mean.csv.0001'],
        # }
        dic = groupby((fname for fname in result.itervalues()),
                      lambda fname: fname.rsplit('.', 1)[0])
        # merge together files coming from different tiles in order
        d = {}
        for fname in dic:
            with open(fname, 'w') as f:
                for tilename in sorted(dic[fname]):
                    f.write(open(tilename).read())
                    os.remove(tilename)
            d[os.path.basename(fname)] = fname
        return d
