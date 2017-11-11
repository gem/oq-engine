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
from openquake.baselib.general import split_in_blocks
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.baselib import parallel
from openquake.hazardlib import sourceconverter
from openquake.commonlib import calc
from openquake.calculators import base, classical

DISAGG_RES_FMT = 'disagg/%(poe)srlz-%(rlz)s-%(imt)s-%(lon)s-%(lat)s'


def compute_disagg(src_filter, sources, rlzs_by_gsim,
                   trt_names, curves, bin_edges, oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param src_filter:
        a :class:`openquake.hazardlib.calc.filter.SourceFilter` instance
    :param sources:
        list of hazardlib source objects
    :param rlzs_by_gsim:
        a dictionary GSIM -> realizations
    :param dict trt_names:
        a tuple of names for the given tectonic region type
    :param curves:
        hazard curves for sites, realizations and IMTs
    :param bin_egdes:
        a dictionary site_id -> edges
    :param oqparam:
        the parameters in the job.ini file
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary of probability arrays, with composite key
        (sid, rlz.id, poe, imt, iml, trt_names).
    """
    sitecol = src_filter.sitecol
    trt_num = dict((trt, i) for i, trt in enumerate(trt_names))
    result = {}  # sid, rlz.id, poe, imt, iml, trt_names -> array

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

        # generate source, rupture, sites once per site
        with collecting_mon:
            cmaker = ContextMaker(
                rlzs_by_gsim, src_filter.integration_distance)
            bd = disagg._collect_bins_data(
                trt_num, sources, site, curves[i],
                rlzs_by_gsim, cmaker, oqparam.imtls,
                oqparam.poes_disagg, oqparam.truncation_level,
                oqparam.num_epsilon_bins, oqparam.iml_disagg,
                monitor('disaggregate_pne', measuremem=False))
        for (poe, imt, iml, rlzi), pnes in bd.eps.items():
            # extract the probabilities of non-exceedance for the
            # given realization, disaggregation PoE, and IMT
            # bins in a format handy for hazardlib
            bins = [bd.mags, bd.dists,  bd.lons, bd.lats, pnes, bd.trts]
            # call disagg._arrange_data_in_bins
            with arranging_mon:
                key = (sid, rlzi, poe, imt, iml, trt_names)
                matrix = disagg._arrange_data_in_bins(
                    bins, edges + (trt_names,))
                result[key] = numpy.array(
                    [fn(matrix) for fn in disagg.pmf_map.values()])
    return result


@base.calculators.add('disaggregation')
class DisaggregationCalculator(classical.ClassicalCalculator):
    """
    Classical PSHA disaggregation calculator
    """
    POE_TOO_BIG = '''\
You are trying to disaggregate for poe=%s.
However the source model #%d, '%s',
produces at most probabilities of %s for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''

    def post_execute(self, nbytes_by_kind):
        """Performs the disaggregation"""
        self.full_disaggregation()

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results,
        a dictionary with key (sid, rlz.id, poe, imt, iml, trt_names)
        and values which are probability arrays.

        :param acc: dictionary accumulating the results
        :param result: dictionary with the result coming from a task
        """
        for key, val in result.items():
            acc[key] = 1. - (1. - acc.get(key, 0)) * (1. - val)
        return acc

    def get_curves(self, sid):
        """
        Get all the relevant hazard curves for the given site ordinal.
        Returns a dictionary rlz_id -> curve_by_imt.
        """
        dic = {}
        imtls = self.oqparam.imtls
        pgetter = calc.PmapGetter(self.datastore)
        for rlz in self.rlzs_assoc.realizations:
            try:
                pmap = pgetter.get(numpy.array([sid]), rlz.ordinal)
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

    def full_disaggregation(self):
        """
        Run the disaggregation phase after hazard curve finalization.
        """
        oq = self.oqparam
        tl = self.oqparam.truncation_level
        bb_dict = self.datastore['bb_dict']
        sitecol = self.sitecol
        mag_bin_width = self.oqparam.mag_bin_width
        eps_edges = numpy.linspace(-tl, tl, self.oqparam.num_epsilon_bins + 1)

        self.bin_edges = {}
        curves = [self.get_curves(sid) for sid in sitecol.sids]
        # determine the number of effective source groups
        sg_data = self.datastore['csm_info/sg_data']
        num_grps = sum(1 for effrup in sg_data['effrup'] if effrup > 0)
        nblocks = math.ceil(oq.concurrent_tasks / num_grps)
        all_args = []
        src_filter = SourceFilter(sitecol, oq.maximum_distance)
        R = len(self.rlzs_assoc.realizations)
        max_poe = numpy.zeros(R, oq.imt_dt())
        for smodel in self.csm.source_models:
            sm_id = smodel.ordinal
            trt_names = tuple(mod.trt for mod in smodel.src_groups)
            max_mag = max(mod.max_mag for mod in smodel.src_groups)
            min_mag = min(mod.min_mag for mod in smodel.src_groups)
            mag_edges = mag_bin_width * numpy.arange(
                int(numpy.floor(min_mag / mag_bin_width)),
                int(numpy.ceil(max_mag / mag_bin_width) + 1))
            for i, site in enumerate(sitecol):
                sid = sitecol.sids[i]
                curve = curves[i]
                # populate max_poe array
                for rlzi, poes in curve.items():
                    for imt in oq.imtls:
                        max_poe[rlzi][imt] = max(
                            max_poe[rlzi][imt], poes[imt].max())
                if not curve:
                    continue  # skip zero-valued hazard curves
                bb = bb_dict[sid]
                if not bb:
                    logging.info(
                        'location %s was too far, skipping disaggregation',
                        site.location)
                    continue

                dist_edges, lon_edges, lat_edges = bb.bins_edges(
                    oq.distance_bin_width, oq.coordinate_bin_width)
                self.bin_edges[sm_id, sid] = bs = (
                    mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)
                shape = disagg.BinData(
                    *[len(edges) - 1 for edges in bs] + [len(trt_names)])
                logging.info('%s for model %d, sid %d', shape, sm_id, sid)

            # check for too big poes_disagg
            for poe in oq.poes_disagg:
                for rlz in self.rlzs_assoc.rlzs_by_smodel[sm_id]:
                    rlzi = rlz.ordinal
                    for imt in oq.imtls:
                        min_poe = max_poe[rlzi][imt]
                        if poe > min_poe:
                            raise ValueError(self.POE_TOO_BIG % (
                                poe, sm_id, smodel.name, min_poe, rlzi, imt))

            bin_edges = {sid: self.bin_edges[sm_id, sid]
                         for sid in sitecol.sids
                         if (sm_id, sid) in self.bin_edges}
            for sg in smodel.src_groups:
                split_sources = []
                for src in sg:
                    for split, _sites in src_filter(
                            sourceconverter.split_source(src), sitecol):
                        split_sources.append(split)
                if not split_sources:
                    continue
                mon = self.monitor('disaggregation')
                rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(sg.trt, sm_id)
                for srcs in split_in_blocks(split_sources, nblocks):
                    all_args.append(
                        (src_filter, srcs, rlzs_by_gsim, trt_names,
                         curves, bin_edges, oq, mon))

        results = parallel.Starmap(compute_disagg, all_args).reduce(
            self.agg_result)
        self.save_disagg_results(results)

    def save_disagg_results(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary of probability arrays
        """
        # build a dictionary rlz.ordinal -> source_model.ordinal
        sm_id = {}
        for i, rlzs in self.rlzs_assoc.rlzs_by_smodel.items():
            for rlz in rlzs:
                sm_id[rlz.ordinal] = i

        # since an extremely small subset of the full disaggregation matrix
        # is saved this method can be run sequentially on the controller node
        for key, probs in sorted(results.items()):
            sid, rlz_id, poe, imt, iml, trt_names = key
            edges = self.bin_edges[sm_id[rlz_id], sid]
            self.save_disagg_result(
                sid, edges, trt_names, probs, rlz_id,
                self.oqparam.investigation_time, imt, iml, poe)

    def save_disagg_result(self, site_id, bin_edges, trt_names, matrix,
                           rlz_id, investigation_time, imt_str, iml, poe):
        """
        Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
        :class:`~openquake.engine.db.models.DisaggResult`).

        :param site_id:
            id of the current site
        :param bin_edges:
            The 5-uple mag, dist, lon, lat, eps
        :param trt_names:
            The list of Tectonic Region Types
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
        attrs['trts'] = hdf5.array_of_vstr(trt_names)
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
