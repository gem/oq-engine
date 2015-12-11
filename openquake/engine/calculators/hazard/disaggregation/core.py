# -*- coding: utf-8 -*-
# Copyright (c) 2010-2015, GEM Foundation.
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

from operator import attrgetter
import numpy

from openquake.hazardlib.imt import from_string

from openquake.baselib.general import groupby
from openquake.calculators.disaggregation import compute_disagg

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.calculators import calculators
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.calculators.hazard.classical.core import \
    ClassicalHazardCalculator


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
    site = models.HazardSite.objects.get(pk=site_id)
    site_wkt = 'POINT(%s %s)' % (site.lon, site.lat)

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
        for rlz in self._realizations:
            for imt_str in self.oqparam.imtls:
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
        hc = self.oqparam
        tl = self.oqparam.truncation_level
        sitecol = self.site_collection
        mag_bin_width = self.oqparam.mag_bin_width
        eps_edges = numpy.linspace(-tl, tl, self.oqparam.num_epsilon_bins + 1)
        logs.LOG.info('%d epsilon bins from %s to %s', len(eps_edges) - 1,
                      min(eps_edges), max(eps_edges))

        self.bin_edges = {}
        curves_dict = dict((site.id, self.get_curves(site))
                           for site in self.site_collection)
        all_args = []
        for trt_model_id, srcs in groupby(
                self.composite_model.get_sources(),
                attrgetter('trt_model_id')).iteritems():

            lt_model = models.TrtModel.objects.get(pk=trt_model_id).lt_model
            trt_names = tuple(lt_model.get_tectonic_region_types())
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

            bin_edges = {}
            for site in self.site_collection:
                if (lt_model.id, site.id) in self.bin_edges:
                    bin_edges[site.id] = self.bin_edges[lt_model.id, site.id]

            all_args.append(
                (sitecol, srcs, trt_model_id, self.rlzs_assoc,
                 trt_names, curves_dict, bin_edges, hc, self.monitor))

        res = tasks.starmap(compute_disagg, all_args)
        self.save_disagg_results(res.reduce(self.agg_result))

    def post_execute(self, result=None):
        super(DisaggHazardCalculator, self).post_execute(result)
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
                rlz_id, self.oqparam.investigation_time, imt, iml, poe)
