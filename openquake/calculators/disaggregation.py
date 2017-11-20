# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Disaggregation calculator core functionality
"""
from __future__ import division
import math
import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import split_in_blocks, pack
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.baselib import parallel
from openquake.hazardlib import sourceconverter
from openquake.commonlib import calc
from openquake.calculators import base, classical

DISAGG_RES_FMT = 'disagg/%(poe)srlz-%(rlz)s-%(imt)s-%(lon)s-%(lat)s'


def compute_disagg(src_filter, sources, cmaker, imldict, trti, bin_edges,
                   oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param src_filter:
        a :class:`openquake.hazardlib.calc.filter.SourceFilter` instance
    :param sources:
        list of hazardlib source objects
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param imldict:
        a list of dictionaries poe, gsim, imt, rlzi -> iml
    :param dict trti:
        tectonic region type index
    :param bin_egdes:
        a dictionary site_id -> edges
    :param oqparam:
        the parameters in the job.ini file
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary of probability arrays, with composite key
        (sid, rlz.id, poe, imt, iml, trti).
    """
    sitecol = src_filter.sitecol
    result = {}  # sid, rlz.id, poe, imt, iml -> array

    collecting_mon = monitor('collecting bins')
    arranging_mon = monitor('arranging bins')

    for i, site in enumerate(sitecol):
        sid = sitecol.sids[i]
        # edges as wanted by disagg._arrange_data_in_bins
        try:
            edges = bin_edges[sid]
        except KeyError:
            # bin_edges for a given site are missing if the site is far away
            continue

        with collecting_mon:
            acc = disagg.collect_bins_data(
                sources, site, cmaker, imldict[i],
                oqparam.truncation_level, oqparam.num_epsilon_bins,
                monitor('disaggregate_pne', measuremem=False))
            bindata = pack(acc, 'mags dists lons lats'.split())
            if not bindata:
                continue

        with arranging_mon:
            for (poe, imt, iml, rlzi), pmfs in disagg.arrange_data_in_bins(
                    bindata, edges, 'pmfs', arranging_mon).items():
                result[sid, rlzi, poe, imt, iml, trti] = pmfs
        result['cache_info'] = arranging_mon.cache_info
    return result


# 0 Mag
# 1 Dist
# 2 TRT
# 3 Mag Dist
# 4 Mag Dist Eps
# 5 Lon Lat
# 6 Mag Lon Lat
# 7 Lon Lat TRT
def fix_pmfs(pmfs, trti, num_trts):
    """
    Manages disaggregation by TRT and LonLatTRT
    """
    out = []
    for i, pmf in enumerate(pmfs):
        if i == 2:  # disagg by TRT
            arr = numpy.zeros(num_trts)
            arr[trti] = pmf
        else:  # no fix
            arr = pmf
        out.append(arr)
    # add disagg Lon_Lat_TRT
    lon_lat = pmfs[5]  # Lon_Lat
    arr = numpy.zeros(lon_lat.shape + (num_trts,))
    arr[:, :, trti] = lon_lat
    out.append(arr)
    return numpy.array(out)


@base.calculators.add('disaggregation')
class DisaggregationCalculator(base.HazardCalculator):
    """
    Classical PSHA disaggregation calculator
    """
    POE_TOO_BIG = '''\
You are trying to disaggregate for poe=%s.
However the source model #%d, '%s',
produces at most probabilities of %s for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''

    def execute(self):
        """Performs the disaggregation"""
        oq = self.oqparam
        if not oq.iml_disagg:
            cl = classical.ClassicalCalculator(oq, self.monitor('classical'))
            cl.run(close=False)
            self.datastore.parent = cl.datastore
            sids = self.sitecol.sids
            curves = [self.get_curves(sid) for sid in sids]
            #self.check_poes_disagg(curves)
        else:
            curves = [None] * len(sids)
        return self.full_disaggregation(curves)

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results,
        a dictionary with key (sid, rlz.id, poe, imt, iml, trti)
        and values which are probability arrays.

        :param acc: dictionary accumulating the results
        :param result: dictionary with the result coming from a task
        """
        if 'cache_info' in result:
            self.cache_info += result.pop('cache_info')
        for key, val in result.items():
            k = key[:-1]  # sid, rlzi, poe, imt, iml
            trti = key[-1]
            pmfs = fix_pmfs(val, trti, len(self.trts))
            acc[k] = 1. - (1. - acc.get(k, 0)) * (1. - pmfs)
        return acc

    def get_curves(self, sid):
        """
        Get all the relevant hazard curves for the given site ordinal.
        Returns a dictionary rlz_id -> curve_by_imt.
        """
        dic = {}
        imtls = self.oqparam.imtls
        pgetter = calc.PmapGetter(self.datastore, sids=numpy.array([sid]))
        for rlz in self.rlzs_assoc.realizations:
            try:
                pmap = pgetter.get(rlz.ordinal)
            except ValueError:  # empty pmaps
                logging.info(
                    'hazard curve contains all zero probabilities; '
                    'skipping site %d, rlz=%d', sid, rlz.ordinal)
                continue
            if sid not in pmap:
                continue
            poes = pmap[sid].convert(imtls)
            for imt_str in imtls:
                if all(x == 0.0 for x in poes[imt_str]):
                    logging.info(
                        'hazard curve contains all zero probabilities; '
                        'skipping site %d, rlz=%d, IMT=%s',
                        sid, rlz.ordinal, imt_str)
                    continue
                dic[rlz.ordinal] = poes
        return dic

    def check_poes_disagg(self, curves):
        """
        Raise an error if the given poes_disagg are too small compared to
        the hazard curves.
        """
        oq = self.oqparam
        max_poe = numpy.zeros(len(curves), oq.imt_dt())

        # check poes
        for smodel in self.csm.source_models:
            sm_id = smodel.ordinal
            for i, site in enumerate(self.sitecol):
                curve = curves[i]
                # populate max_poe array
                for rlzi, poes in curve.items():
                    for imt in oq.imtls:
                        max_poe[rlzi][imt] = max(
                            max_poe[rlzi][imt], poes[imt].max())
                if not curve:
                    continue  # skip zero-valued hazard curves

        # check for too big poes_disagg
        for smodel in self.csm.source_models:
            for poe in oq.poes_disagg:
                for rlz in self.rlzs_assoc.rlzs_by_smodel[sm_id]:
                    rlzi = rlz.ordinal
                    for imt in oq.imtls:
                        min_poe = max_poe[rlzi][imt]
                        if poe > min_poe:
                            raise ValueError(self.POE_TOO_BIG % (
                                poe, sm_id, smodel.name, min_poe, rlzi, imt))

    def full_disaggregation(self, curves=None):
        """
        Run the disaggregation phase after hazard curve finalization.
        """
        oq = self.oqparam
        tl = oq.truncation_level
        sitecol = self.sitecol
        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        self.bin_edges = {}
        # determine the number of source groups
        num_grps = sum(1 for sg in self.csm.src_groups)
        nblocks = math.ceil(oq.concurrent_tasks / num_grps)
        src_filter = SourceFilter(sitecol, oq.maximum_distance)

        # build trt_edges
        trts = tuple(sorted(set(sg.trt for smodel in self.csm.source_models
                                for sg in smodel.src_groups)))
        trt_num = {trt: i for i, trt in enumerate(trts)}
        self.trts = trts

        # build mag_edges
        min_mag = min(sg.min_mag for smodel in self.csm.source_models
                      for sg in smodel.src_groups)
        max_mag = max(sg.max_mag for smodel in self.csm.source_models
                      for sg in smodel.src_groups)
        mag_edges = oq.mag_bin_width * numpy.arange(
            int(numpy.floor(min_mag / oq.mag_bin_width)),
            int(numpy.ceil(max_mag / oq.mag_bin_width) + 1))

        # build dist_edges
        maxdist = max(oq.maximum_distance(trt, max_mag) for trt in trts)
        dist_edges = oq.distance_bin_width * numpy.arange(
            0, int(numpy.ceil(maxdist / oq.distance_bin_width) + 1))
        logging.info('dist = %s...%s', min(dist_edges), max(dist_edges))

        # build eps_edges
        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build lon_edges, lat_edges per sid
        bbs = src_filter.get_bounding_boxes(mag=max_mag)
        for sid, bb in zip(self.sitecol.sids, bbs):
            lon_edges, lat_edges = disagg.lon_lat_bins(
                bb, oq.coordinate_bin_width)
            logging.info('site %d, lon = %s...%s',
                         sid, min(lon_edges), max(lon_edges))
            logging.info('site %d, lat = %s...%s',
                         sid, min(lat_edges), max(lat_edges))
            self.bin_edges[sid] = bs = (
                mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)
            shape = [len(edges) - 1 for edges in bs] + [len(trts)]
            logging.info('%s for sid %d', shape, sid)

        # build all_args
        all_args = []
        for smodel in self.csm.source_models:
            for sg in smodel.src_groups:
                split_sources = []
                for src in sg:
                    for split, _sites in src_filter(
                            sourceconverter.split_source(src), sitecol):
                        split_sources.append(split)
                if not split_sources:
                    continue
                mon = self.monitor('disaggregation')
                rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(
                    sg.trt, smodel.ordinal)
                cmaker = ContextMaker(
                    rlzs_by_gsim, src_filter.integration_distance)
                imls = [disagg.make_imldict(
                    rlzs_by_gsim, oq.imtls, oq.iml_disagg, oq.poes_disagg,
                    curve) for curve in curves]
                for srcs in split_in_blocks(split_sources, nblocks):
                    trti = trt_num[srcs[0].tectonic_region_type]
                    all_args.append(
                        (src_filter, srcs, cmaker, imls, trti,
                         self.bin_edges, oq, mon))

        self.cache_info = numpy.zeros(2)  # operations, cache_hits
        results = parallel.Starmap(compute_disagg, all_args).reduce(
            self.agg_result)
        ops, hits = self.cache_info
        logging.info('Cache speedup %s', ops / (ops - hits))
        return results

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary of probability arrays
        """
        # since an extremely small subset of the full disaggregation matrix
        # is saved this method can be run sequentially on the controller node
        for key, probs in sorted(results.items()):
            sid, rlz_id, poe, imt, iml = key
            edges = self.bin_edges[sid]
            self.save_disagg_result(
                sid, edges, probs, rlz_id,
                self.oqparam.investigation_time, imt, iml, poe)

    def save_disagg_result(self, site_id, bin_edges, matrix,
                           rlz_id, investigation_time, imt_str, iml, poe):
        """
        Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
        :class:`~openquake.engine.db.models.DisaggResult`).

        :param site_id:
            id of the current site
        :param bin_edges:
            The 5-uple mag, dist, lon, lat, eps
        :param matrix:
            A probability array
        :param rlz_id:
            ordinal of the realization to which the results belong.
        :param float investigation_time:
            Investigation time (years) for the calculation.
        :param imt_str:
            Intensity measure type string (PGA, SA, etc.)
        :param float iml:
            Intensity measure level interpolated (using `poe`) from the hazard
            curve at the `site`.
        :param float poe:
            Disaggregation probability of exceedance value for this result.
        """
        lon = self.sitecol.lons[site_id]
        lat = self.sitecol.lats[site_id]
        mag, dist, lons, lats, eps = bin_edges
        disp_name = DISAGG_RES_FMT % dict(
            poe='' if poe is None else 'poe-%s-' % poe,
            rlz=rlz_id, imt=imt_str, lon=lon, lat=lat)
        self.datastore[disp_name] = dic = {
            '_'.join(key): mat for key, mat in zip(disagg.pmf_map, matrix)}
        attrs = self.datastore.hdf5[disp_name].attrs
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        attrs['iml'] = iml
        attrs['trts'] = hdf5.array_of_vstr(self.trts)
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['location'] = (lon, lat)
        if poe is not None:
            attrs['poe'] = poe
        # sanity check: all poe_agg should be the same
        attrs['poe_agg'] = [1. - numpy.prod(1. - dic[pmf])
                            for pmf in sorted(dic)]
