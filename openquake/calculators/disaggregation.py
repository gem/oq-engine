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
from openquake.baselib import parallel
from openquake.hazardlib import sourceconverter
from openquake.commonlib import calc
from openquake.calculators import base, classical

DISAGG_RES_FMT = 'disagg/poe-%(poe)s-rlz-%(rlz)s-%(imt)s-%(lon)s-%(lat)s'


def compute_disagg(src_filter, sources, src_group_id, rlzs_assoc,
                   trt_names, curves_dict, bin_edges, oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param src_filter:
        a :class:`openquake.hazardlib.calc.filter.SourceFilter` instance
    :param sources:
        list of hazardlib source objects
    :param src_group_id:
        numeric ID of a SourceGroup instance
    :param rlzs_assoc:
        a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param dict trt_names:
        a tuple of names for the given tectonic region type
    :param curves_dict:
        a dictionary with the hazard curves for sites, realizations and IMTs
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
    gsims = rlzs_assoc.gsims_by_grp_id[src_group_id]
    result = {}  # sid, rlz.id, poe, imt, iml, trt_names -> array

    collecting_mon = monitor('collecting bins')
    arranging_mon = monitor('arranging bins')

    for site, sid in zip(sitecol, sitecol.sids):
        # edges as wanted by disagg._arrange_data_in_bins
        try:
            edges = bin_edges[sid]
        except KeyError:
            # bin_edges for a given site are missing if the site is far away
            continue

        # generate source, rupture, sites once per site
        with collecting_mon:
            bdata = disagg._collect_bins_data(
                trt_num, sources, site, curves_dict[sid],
                src_group_id, rlzs_assoc, gsims, oqparam.imtls,
                oqparam.poes_disagg, oqparam.truncation_level,
                oqparam.num_epsilon_bins, oqparam.iml_disagg,
                monitor)

        for (rlzi, poe, imt), iml_pne_pairs in bdata.pnes.items():
            # extract the probabilities of non-exceedance for the
            # given realization, disaggregation PoE, and IMT
            iml = iml_pne_pairs[0][0]
            probs = numpy.array([p for (i, p) in iml_pne_pairs], float)

            # bins in a format handy for hazardlib
            bins = [bdata.mags, bdata.dists,
                    bdata.lons, bdata.lats,
                    bdata.trts, None, probs]

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
        Returns a dictionary {(rlz_id, imt) -> curve}.
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
                dic[rlz.ordinal, imt_str] = poes[imt_str]
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
        logging.info('%d epsilon bins from %s to %s', len(eps_edges) - 1,
                     min(eps_edges), max(eps_edges))

        self.bin_edges = {}
        curves_dict = {sid: self.get_curves(sid) for sid in sitecol.sids}
        all_args = []
        num_trts = sum(len(sm.src_groups) for sm in self.csm.source_models)
        nblocks = math.ceil(oq.concurrent_tasks / num_trts)
        for smodel in self.csm.source_models:
            sm_id = smodel.ordinal
            trt_names = tuple(mod.trt for mod in smodel.src_groups)
            max_mag = max(mod.max_mag for mod in smodel.src_groups)
            min_mag = min(mod.min_mag for mod in smodel.src_groups)
            mag_edges = mag_bin_width * numpy.arange(
                int(numpy.floor(min_mag / mag_bin_width)),
                int(numpy.ceil(max_mag / mag_bin_width) + 1))
            logging.info('%d mag bins from %s to %s', len(mag_edges) - 1,
                         min_mag, max_mag)
            for src_group in smodel.src_groups:
                if src_group.id not in self.rlzs_assoc.gsims_by_grp_id:
                    continue  # the group has been filtered away
                for sid, site in zip(sitecol.sids, sitecol):
                    curves = curves_dict[sid]
                    if not curves:
                        continue  # skip zero-valued hazard curves
                    bb = bb_dict[sm_id, sid]
                    if not bb:
                        logging.info(
                            'location %s was too far, skipping disaggregation',
                            site.location)
                        continue

                    dist_edges, lon_edges, lat_edges = bb.bins_edges(
                        oq.distance_bin_width, oq.coordinate_bin_width)
                    logging.info(
                        '%d dist bins from %s to %s', len(dist_edges) - 1,
                        min(dist_edges), max(dist_edges))
                    logging.info(
                        '%d lon bins from %s to %s', len(lon_edges) - 1,
                        bb.west, bb.east)
                    logging.info(
                        '%d lat bins from %s to %s', len(lon_edges) - 1,
                        bb.south, bb.north)

                    self.bin_edges[sm_id, sid] = (
                        mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)

                bin_edges = {}
                for sid, site in zip(sitecol.sids, sitecol):
                    if (sm_id, sid) in self.bin_edges:
                        bin_edges[sid] = self.bin_edges[sm_id, sid]

                src_filter = SourceFilter(sitecol, oq.maximum_distance)
                split_sources = []
                for src in src_group:
                    for split, _sites in src_filter(
                            sourceconverter.split_source(src), sitecol):
                        split_sources.append(split)
                mon = self.monitor('disaggregation')
                for srcs in split_in_blocks(split_sources, nblocks):
                    all_args.append(
                        (src_filter, srcs, src_group.id, self.rlzs_assoc,
                         trt_names, curves_dict, bin_edges, oq, mon))

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
            poe=poe, rlz=rlz_id, imt=imt_str, lon=lon, lat=lat)
        self.datastore[disp_name] = {
            '_'.join(key): mat for key, mat in zip(disagg.pmf_map, matrix)}
        attrs = self.datastore.hdf5[disp_name].attrs
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        attrs['iml'] = iml
        attrs['poe'] = poe
        attrs['trts'] = hdf5.array_of_vstr(trt_names)
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['location'] = (lon, lat)
