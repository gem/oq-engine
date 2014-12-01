# -*- coding: utf-8 -*-
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Disaggregation calculator core functionality
"""

import sys
from operator import attrgetter
from collections import namedtuple
import numpy

from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import SiteCollection

from openquake.baselib.general import groupby
from openquake.commonlib.calculators.calc import gen_ruptures_for_site

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.calculators import calculators
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor
from openquake.engine.calculators.hazard.classical.core import \
    ClassicalHazardCalculator


# a 6-uple containing float 4 arrays mags, dists, lons, lats,
# 1 int array trts and a list of dictionaries pnes
BinData = namedtuple('BinData', 'mags, dists, lons, lats, trts, pnes')


def _collect_bins_data(mon, trt_num, source_ruptures, site, curves,
                       trt_model_id, gsims, imtls, poes, truncation_level,
                       n_epsilons):
    # returns a BinData instance
    sitecol = SiteCollection([site])
    mags = []
    dists = []
    lons = []
    lats = []
    trts = []
    pnes = []
    sitemesh = sitecol.mesh
    calc_dist = mon.copy('calc distances')
    make_ctxt = mon.copy('making contexts')
    disagg_poe = mon.copy('disaggregate_poe')
    trt_model = models.TrtModel.objects.get(pk=trt_model_id)
    rlzs = trt_model.get_rlzs_by_gsim()
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
                for gsim in gsims:
                    with make_ctxt:
                        sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
                    for imt_str, imls in imtls.iteritems():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        for rlz in rlzs[gsim.__class__.__name__]:
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
            msg %= (source.source_id, err.message)
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


_DISAGG_RES_NAME_FMT = 'disagg(%(poe)s)-rlz-%(rlz)s-%(imt)s-%(wkt)s'


def save_disagg_result(job_id, site_id, bin_edges, trt_names, matrix,
                       rlz_id, investigation_time, imt_str, iml, poe):
    """
    Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
    :class:`~openquake.engine.db.models.DisaggResult`).

    :param int job_id:
        id of the current job.
    :param int site_id:
        id of the current site
    :param bin_edges:
        The 5-uple mag, dist, lon, lat, eps
    :param trt_names:
        The list of Tectonic Region Types
    :param matrix:
        A probability array
    :param rlz:
        :class:`openquake.engine.db.models.LtRealization` to which these
        results belong.
    :param float investigation_time:
        Investigation time (years) for the calculation.
    :param imt_str:
        Intensity measure type (PGA, SA, etc.)
    :param float iml:
        Intensity measure level interpolated (using ``poe``) from the hazard
        curve at the ``site``.
    :param float poe:
        Disaggregation probability of exceedance value for this result.
    """
    job = models.OqJob.objects.get(id=job_id)

    site_wkt = models.HazardSite.objects.get(pk=site_id).location.wkt

    disp_name = _DISAGG_RES_NAME_FMT % dict(
        poe=poe, rlz=rlz_id, imt=imt_str, wkt=site_wkt)

    output = models.Output.objects.create_output(
        job, disp_name, 'disagg_matrix')

    imt, sa_period, sa_damping = from_string(imt_str)
    mag, dist, lon, lat, eps = bin_edges
    models.DisaggResult.objects.create(
        output=output,
        lt_realization_id=rlz_id,
        investigation_time=investigation_time,
        imt=imt,
        sa_period=sa_period,
        sa_damping=sa_damping,
        iml=iml,
        poe=poe,
        mag_bin_edges=mag,
        dist_bin_edges=dist,
        lon_bin_edges=lon,
        lat_bin_edges=lat,
        eps_bin_edges=eps,
        trts=trt_names,
        location=site_wkt,
        matrix=matrix,
    )


@tasks.oqtask
def compute_disagg(job_id, sitecol, sources, trt_model_id,
                   trt_num, curves_dict, bin_edges):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param int job_id:
        ID of the currently running :class:`openquake.engine.db.models.OqJob`
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param list sources:
        list of hazardlib source objects
    :param lt_model:
        an instance of :class:`openquake.engine.db.models.LtSourceModel`
    :param dict trt_num:
        a dictionary Tectonic Region Type -> incremental number
    :param curves_dict:
        a dictionary with the hazard curves for sites, realizations and IMTs
    :param bin_egdes:
        a dictionary (lt_model_id, site_id) -> edges
    :returns:
        a dictionary of probability arrays, with composite key
        (site.id, rlz.id, poe, imt, iml, trt_names).
    """
    mon = LightMonitor('disagg', job_id, compute_disagg)
    hc = models.oqparam(job_id)
    trt_model = models.TrtModel.objects.get(pk=trt_model_id)
    gsims = trt_model.get_gsim_instances()
    lt_model_id = trt_model.lt_model.id
    rlzs = trt_model.get_rlzs_by_gsim()
    trt_names = tuple(trt_model.lt_model.get_tectonic_region_types())
    result = {}  # site.id, rlz.id, poe, imt, iml, trt_names -> array

    for site in sitecol:
        # edges as wanted by disagg._arrange_data_in_bins
        try:
            edges = bin_edges[lt_model_id, site.id]
        except KeyError:
            # bin_edges for a given site are missing if the site is far away
            continue

        # generate source, rupture, sites once per site
        source_ruptures = list(
            gen_ruptures_for_site(site, sources, hc.maximum_distance, mon))
        if not source_ruptures:
            continue
        logs.LOG.info('Collecting bins from %d ruptures close to %s',
                      sum(len(rupts) for src, rupts in source_ruptures),
                      site.location)

        with EnginePerformanceMonitor(
                'collecting bins', job_id, compute_disagg):
            bdata = _collect_bins_data(
                mon, trt_num, source_ruptures, site, curves_dict[site.id],
                trt_model_id, gsims, hc.intensity_measure_types_and_levels,
                hc.poes_disagg, getattr(hc, 'truncation_level', None),
                hc.num_epsilon_bins)

        if not bdata.pnes:  # no contributions for this site
            continue

        for poe in hc.poes_disagg:
            for imt in hc.intensity_measure_types_and_levels:
                for gsim in gsims:
                    for rlz in rlzs[gsim.__class__.__name__]:
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
                        with EnginePerformanceMonitor(
                                'arranging bins', job_id, compute_disagg):
                            key = (site.id, rlz.id, poe, imt, iml, trt_names)
                            matrix = disagg._arrange_data_in_bins(
                                bins, edges + (trt_names,))
                            result[key] = numpy.array(
                                [fn(matrix) for fn in disagg.pmf_map.values()])

    return result


@calculators.add('disaggregation')
class DisaggHazardCalculator(ClassicalHazardCalculator):
    """
    A calculator which performs disaggregation calculations in a distributed /
    parallelized fashion.

    See :func:`openquake.hazardlib.calc.disagg.disaggregation` for more
    details about the nature of this type of calculation.
    """
    def get_curves(self, site):
        """
        Get all the relevant hazard curves for the given site.
        Returns a dictionary {(rlz_id, imt) -> curve}.
        """
        dic = {}
        wkt = site.location.wkt2d
        for rlz in self._get_realizations():
            for imt_str in self.hc.intensity_measure_types_and_levels:
                imt = from_string(imt_str)
                [curve] = models.HazardCurveData.objects.filter(
                    location=wkt,
                    hazard_curve__lt_realization=rlz,
                    hazard_curve__imt=imt[0],
                    hazard_curve__sa_period=imt[1],
                    hazard_curve__sa_damping=imt[2])
                if all(x == 0.0 for x in curve.poes):
                    logs.LOG.warn(
                        '* hazard curve %d contains all zero '
                        'probabilities; skipping SRID=4326;%s, rlz=%d, IMT=%s',
                        curve.id, wkt, rlz.id, imt_str)
                    continue
                dic[rlz.id, imt_str] = curve
        return dic

    @EnginePerformanceMonitor.monitor
    def full_disaggregation(self):
        """
        Run the disaggregation phase after hazard curve finalization.
        """
        hc = self.hc
        tl = getattr(self.hc, 'truncation_level', None)
        sitecol = self.site_collection
        mag_bin_width = self.hc.mag_bin_width
        eps_edges = numpy.linspace(-tl, tl, self.hc.num_epsilon_bins + 1)
        logs.LOG.info('%d epsilon bins from %s to %s', len(eps_edges) - 1,
                      min(eps_edges), max(eps_edges))

        self.bin_edges = {}
        curves_dict = dict((site.id, self.get_curves(site))
                           for site in self.site_collection)
        all_args = []
        for trt_model_id, srcs in groupby(
                self.composite_model.sources,
                attrgetter('trt_model_id')).iteritems():
            lt_model = models.TrtModel.objects.get(pk=trt_model_id).lt_model
            trt_num = dict((trt, i) for i, trt in enumerate(
                           lt_model.get_tectonic_region_types()))
            infos = list(models.TrtModel.objects.filter(
                         lt_model=lt_model))

            max_mag = max(i.max_mag for i in infos)
            min_mag = min(i.min_mag for i in infos)
            mag_edges = mag_bin_width * numpy.arange(
                int(numpy.floor(min_mag / mag_bin_width)),
                int(numpy.ceil(max_mag / mag_bin_width) + 1))
            logs.LOG.info('%d mag bins from %s to %s', len(mag_edges) - 1,
                          min_mag, max_mag)

            for site in self.site_collection:
                curves = curves_dict[site.id]
                if not curves:
                    continue  # skip zero-valued hazard curves
                bb = self.bb_dict[lt_model.id, site.id]
                if not bb:
                    logs.LOG.info(
                        'location %s was too far, skipping disaggregation',
                        site.location)
                    continue

                dist_edges, lon_edges, lat_edges = bb.bins_edges(
                    hc.distance_bin_width, hc.coordinate_bin_width)
                logs.LOG.info(
                    '%d dist bins from %s to %s', len(dist_edges) - 1,
                    min(dist_edges), max(dist_edges))
                logs.LOG.info('%d lon bins from %s to %s', len(lon_edges) - 1,
                              bb.west, bb.east)
                logs.LOG.info('%d lat bins from %s to %s', len(lon_edges) - 1,
                              bb.south, bb.north)

                self.bin_edges[lt_model.id, site.id] = (
                    mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)

            all_args.append((self.job.id, sitecol, srcs, trt_model_id,
                             trt_num, curves_dict, self.bin_edges))

        res = tasks.starmap(compute_disagg, all_args, logs.LOG.progress)
        self.save_disagg_results(res.reduce(self.agg_result))

    def post_execute(self):
        super(DisaggHazardCalculator, self).post_execute()
        self.full_disaggregation()

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results,
        a dictionary with key (site.id, rlz.id, poe, imt, iml, trt_names)
        and values which are probability arrays.

        :param acc: dictionary accumulating the results
        :param result: dictionary with the result coming from a task
        """
        for key, val in result.iteritems():
            acc[key] = 1. - (1. - acc.get(key, 0)) * (1. - val)
        return acc

    @EnginePerformanceMonitor.monitor
    def save_disagg_results(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary of probability arrays
        """
        # since an extremely small subset of the full disaggregation matrix
        # is saved this method can be run sequentially on the controller node
        for key, probs in results.iteritems():
            site_id, rlz_id, poe, imt, iml, trt_names = key
            lt_model = models.LtRealization.objects.get(pk=rlz_id).lt_model
            edges = self.bin_edges[lt_model.id, site_id]
            save_disagg_result(
                self.job.id, site_id, edges, trt_names, probs,
                rlz_id, self.hc.investigation_time, imt, iml, poe)
