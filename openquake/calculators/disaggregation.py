# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import sys
import math
import logging
from collections import namedtuple
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import raise_
from openquake.baselib.general import split_in_blocks
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import parallel
from openquake.commonlib.calc import gen_ruptures_for_site
from openquake.calculators import base, classical

DISAGG_RES_FMT = 'disagg/poe-%(poe)s-rlz-%(rlz)s-%(imt)s-%(lon)s-%(lat)s'


# a 6-uple containing float 4 arrays mags, dists, lons, lats,
# 1 int array trts and a list of dictionaries pnes
BinData = namedtuple('BinData', 'mags, dists, lons, lats, trts, pnes')


def _collect_bins_data(trt_num, source_ruptures, site, curves, src_group_id,
                       rlzs_assoc, gsims, imtls, poes, truncation_level,
                       n_epsilons, mon):
    # returns a BinData instance
    sitecol = SiteCollection([site])
    mags = []
    dists = []
    lons = []
    lats = []
    trts = []
    pnes = []
    sitemesh = sitecol.mesh
    make_ctxt = mon('making contexts', measuremem=False)
    disagg_poe = mon('disaggregate_poe', measuremem=False)
    cmaker = ContextMaker(gsims)
    for source, ruptures in source_ruptures:
        try:
            tect_reg = trt_num[source.tectonic_region_type]
            for rupture in ruptures:
                with make_ctxt:
                    sctx, rctx, dctx = cmaker.make_contexts(sitecol, rupture)
                # extract rupture parameters of interest
                mags.append(rupture.mag)
                dists.append(dctx.rjb[0])  # single site => single distance
                [closest_point] = rupture.surface.get_closest_points(sitemesh)
                lons.append(closest_point.longitude)
                lats.append(closest_point.latitude)
                trts.append(tect_reg)

                pne_dict = {}
                # a dictionary rlz.id, poe, imt_str -> prob_no_exceed
                for gsim in gsims:
                    gs = str(gsim)
                    for imt_str, imls in imtls.items():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        for rlz in rlzs_assoc[src_group_id, gs]:
                            rlzi = rlz.ordinal
                            curve_poes = curves[rlzi, imt_str][::-1]
                            for poe in poes:
                                iml = numpy.interp(poe, curve_poes, imls)
                                # compute probability of exceeding iml given
                                # the current rupture and epsilon_bin, that is
                                # ``P(IMT >= iml | rup, epsilon_bin)``
                                # for each of the epsilon bins
                                with disagg_poe:
                                    [poes_given_rup_eps] = \
                                        gsim.disaggregate_poe(
                                            sctx, rctx, dctx, imt, iml,
                                            truncation_level, n_epsilons)
                                pne = rupture.get_probability_no_exceedance(
                                    poes_given_rup_eps)
                                pne_dict[rlzi, poe, imt_str] = (iml, pne)

                pnes.append(pne_dict)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err)
            raise_(etype, msg, tb)

    return BinData(numpy.array(mags, float),
                   numpy.array(dists, float),
                   numpy.array(lons, float),
                   numpy.array(lats, float),
                   numpy.array(trts, int),
                   pnes)


def compute_disagg(sitecol, sources, src_group_id, rlzs_assoc,
                   trt_names, curves_dict, bin_edges, oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
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
    trt = sources[0].tectonic_region_type
    try:
        max_dist = oqparam.maximum_distance[trt]
    except KeyError:
        max_dist = oqparam.maximum_distance['default']
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
        source_ruptures = list(
            gen_ruptures_for_site(site, sources, max_dist, monitor))
        if not source_ruptures:
            continue
        with collecting_mon:
            bdata = _collect_bins_data(
                trt_num, source_ruptures, site, curves_dict[sid],
                src_group_id, rlzs_assoc, gsims, oqparam.imtls,
                oqparam.poes_disagg, oqparam.truncation_level,
                oqparam.num_epsilon_bins, monitor)

        if not bdata.pnes:  # no contributions for this site
            continue

        for poe in oqparam.poes_disagg:
            for imt in oqparam.imtls:
                for gsim in gsims:
                    for rlz in rlzs_assoc[src_group_id, gsim]:
                        rlzi = rlz.ordinal
                        # extract the probabilities of non-exceedance for the
                        # given realization, disaggregation PoE, and IMT
                        iml_pne_pairs = [pne[rlzi, poe, imt]
                                         for pne in bdata.pnes]
                        iml = iml_pne_pairs[0][0]
                        probs = numpy.array(
                            [p for (i, p) in iml_pne_pairs], float)
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
    def post_execute(self, result=None):
        super(DisaggregationCalculator, self).post_execute(result)
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
        for rlz in self.rlzs_assoc.realizations:
            poes = self.datastore['hcurves/rlz-%03d' % rlz.ordinal][sid]
            for imt_str in self.oqparam.imtls:
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

                for srcs in split_in_blocks(src_group, nblocks):
                    all_args.append(
                        (sitecol, srcs, src_group.id, self.rlzs_assoc,
                         trt_names, curves_dict, bin_edges, oq, self.monitor))

        results = parallel.starmap(compute_disagg, all_args).reduce(
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
        for i, rlzs in enumerate(self.rlzs_assoc.rlzs_by_smodel):
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

        self.datastore[disp_name] = matrix
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
