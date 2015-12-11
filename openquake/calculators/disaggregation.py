#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

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

"""
Disaggregation calculator core functionality
"""

import sys
import logging
from collections import namedtuple
import numpy

from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib.parallel import litetask
from openquake.calculators.calc import gen_ruptures_for_site


# a 6-uple containing float 4 arrays mags, dists, lons, lats,
# 1 int array trts and a list of dictionaries pnes
BinData = namedtuple('BinData', 'mags, dists, lons, lats, trts, pnes')


def _collect_bins_data(trt_num, source_ruptures, site, curves, trt_model_id,
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
    calc_dist = mon('calc distances', measuremem=False)
    make_ctxt = mon('making contexts', measuremem=False)
    disagg_poe = mon('disaggregate_poe', measuremem=False)
    cmaker = ContextMaker(gsims)
    for source, ruptures in source_ruptures:
        try:
            tect_reg = trt_num[source.tectonic_region_type]
            for rupture in ruptures:
                # extract rupture parameters of interest
                mags.append(rupture.mag)
                with calc_dist:
                    [jb_dist] = rupture.surface.get_joyner_boore_distance(
                        sitemesh)
                    dists.append(jb_dist)
                    [closest_point] = rupture.surface.get_closest_points(
                        sitemesh)
                lons.append(closest_point.longitude)
                lats.append(closest_point.latitude)
                trts.append(tect_reg)

                pne_dict = {}
                # a dictionary rlz.id, poe, imt_str -> prob_no_exceed

                with make_ctxt:
                    sctx, rctx, dctx = cmaker.make_contexts(sitecol, rupture)
                for gsim in gsims:
                    for imt_str, imls in imtls.iteritems():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        for rlz in rlzs_assoc[
                                trt_model_id, gsim.__class__.__name__]:
                            curve_poes = curves[rlz.id, imt_str].poes[::-1]
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
                                pne_dict[rlz.id, poe, imt_str] = (iml, pne)

                pnes.append(pne_dict)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err)
            raise etype, msg, tb

    calc_dist.flush()
    make_ctxt.flush()
    disagg_poe.flush()

    return BinData(numpy.array(mags, float),
                   numpy.array(dists, float),
                   numpy.array(lons, float),
                   numpy.array(lats, float),
                   numpy.array(trts, int),
                   pnes)


@litetask
def compute_disagg(sitecol, sources, trt_model_id, rlzs_assoc,
                   trt_names, curves_dict, bin_edges, oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param sources:
        list of hazardlib source objects
    :param trt_model_id:
        numeric ID of a TrtModel instance
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
        (site.id, rlz.id, poe, imt, iml, trt_names).
    """
    trt_num = dict((trt, i) for i, trt in enumerate(trt_names))
    gsims = rlzs_assoc.gsims_by_trt_id[trt_model_id]
    result = {}  # site.id, rlz.id, poe, imt, iml, trt_names -> array

    collecting_mon = monitor('collecting bins')
    arranging_mon = monitor('arranging bins')

    for site in sitecol:
        # edges as wanted by disagg._arrange_data_in_bins
        try:
            edges = bin_edges[site.id]
        except KeyError:
            # bin_edges for a given site are missing if the site is far away
            continue

        # generate source, rupture, sites once per site
        source_ruptures = list(
            gen_ruptures_for_site(
                site, sources, oqparam.maximum_distance, monitor))
        if not source_ruptures:
            continue
        logging.info('Collecting bins from %d ruptures close to %s',
                     sum(len(rupts) for src, rupts in source_ruptures),
                     site.location)

        with collecting_mon:
            bdata = _collect_bins_data(
                trt_num, source_ruptures, site, curves_dict[site.id],
                trt_model_id, rlzs_assoc, gsims, oqparam.imtls,
                oqparam.poes_disagg, oqparam.truncation_level,
                oqparam.num_epsilon_bins, monitor)

        if not bdata.pnes:  # no contributions for this site
            continue

        for poe in oqparam.poes_disagg:
            for imt in oqparam.imtls:
                for gsim in gsims:
                    for rlz in rlzs_assoc[
                            trt_model_id, gsim.__class__.__name__]:
                        # extract the probabilities of non-exceedance for the
                        # given realization, disaggregation PoE, and IMT
                        iml_pne_pairs = [pne[rlz.id, poe, imt]
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
                            key = (site.id, rlz.id, poe, imt, iml, trt_names)
                            matrix = disagg._arrange_data_in_bins(
                                bins, edges + (trt_names,))
                            result[key] = numpy.array(
                                [fn(matrix) for fn in disagg.pmf_map.values()])
    collecting_mon.flush()
    arranging_mon.flush()
    return result
