# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013, GEM Foundation.
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
import numpy

import openquake.hazardlib
from openquake.hazardlib.imt import from_string
from openquake.engine import logs
from openquake.engine.calculators.hazard.classical.core import \
    ClassicalHazardCalculator
from openquake.engine.db import models
from openquake.engine.input import logictree
from openquake.engine.utils import general as general_utils
from openquake.engine.utils import tasks as utils_tasks
from openquake.engine.performance import EnginePerformanceMonitor


@utils_tasks.oqtask
def compute_disagg(job_id, sites, sources, lt_rlz, ltp):
    """
    Calculate disaggregation histograms and saving the results to the database.

    Here is the basic calculation workflow:

    1. Get all sources
    2. Get IMTs
    3. Get the hazard curve for each point, IMT, and realization
    4. For each `poes_disagg`, interpolate the IML for each curve.
    5. Get GSIMs, TOM (Temporal Occurence Model), and truncation level.
    6. Get histogram bin edges.
    7. Prepare calculation args.
    8. Call the hazardlib calculator
       (see :func:`openquake.hazardlib.calc.disagg.disaggregation`
       for more info).

    :param int job_id:
        ID of the currently running :class:`openquake.engine.db.models.OqJob`
    :param list sites:
        `list` of :class:`openquake.hazardlib.site.Site` objects, which
        indicate the locations (and associated soil parameters) for which we
        need to compute disaggregation histograms.
    :param list sources:
        `list` of hazardlib source objects
    :param lt_rlz:
        instance of :class:`openquake.engine.db.models.LtRealization` for which
        we want to compute disaggregation histograms. This realization will
        determine which hazard curve results to use as a basis for the
        calculation.
    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance
    """
    # Silencing 'Too many local variables'
    # pylint: disable=R0914
    assert sites, sites
    assert sources, sources
    logs.LOG.debug(
        '> computing disaggregation for %(np)s sites for realization %(rlz)s'
        % dict(np=len(sites), rlz=lt_rlz.id))

    job = models.OqJob.objects.get(id=job_id)
    hc = job.hazard_calculation
    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
    sources = map(apply_uncertainties, sources)

    f = openquake.hazardlib.calc.filters
    src_site_filter = f.source_site_noop_filter if hc.prefiltered \
        else f.source_site_distance_filter(hc.maximum_distance)
    rup_site_filter = f.rupture_site_distance_filter(hc.maximum_distance)

    for imt, imls in hc.intensity_measure_types_and_levels.iteritems():
        hc_im_type, sa_period, sa_damping = imt = from_string(imt)

        imls = numpy.array(imls[::-1])

        # loop over sites
        for site in sites:
            # get curve for this point/IMT/realization
            [curve] = models.HazardCurveData.objects.filter(
                location=site.location.wkt2d,
                hazard_curve__lt_realization=lt_rlz,
                hazard_curve__imt=hc_im_type,
                hazard_curve__sa_period=sa_period,
                hazard_curve__sa_damping=sa_damping,
            )

            # If the hazard curve is all zeros, don't even do the
            # disagg calculation.
            if all(x == 0.0 for x in curve.poes):
                logs.LOG.debug(
                    '* hazard curve contained all 0 probability values; '
                    'skipping')
                continue

            for poe in hc.poes_disagg:
                iml = numpy.interp(poe, curve.poes[::-1], imls)
                calc_kwargs = {
                    'sources': sources,
                    'site': site,
                    'imt': imt,
                    'iml': iml,
                    'gsims': gsims,
                    'time_span': hc.investigation_time,
                    'truncation_level': hc.truncation_level,
                    'n_epsilons': hc.num_epsilon_bins,
                    'mag_bin_width': hc.mag_bin_width,
                    'dist_bin_width': hc.distance_bin_width,
                    'coord_bin_width': hc.coordinate_bin_width,
                    'source_site_filter': src_site_filter,
                    'rupture_site_filter': rup_site_filter,
                }
                with EnginePerformanceMonitor(
                        'computing disaggregation', job_id, compute_disagg):
                    bin_edges, diss_matrix = openquake.hazardlib.calc.\
                        disagg.disaggregation_poissonian(**calc_kwargs)
                    if not bin_edges:  # no ruptures generated
                        continue

                with EnginePerformanceMonitor(
                        'saving disaggregation', job_id, compute_disagg):
                    _save_disagg_matrix(
                        job, site, bin_edges, diss_matrix, lt_rlz,
                        hc.investigation_time, hc_im_type, iml, poe, sa_period,
                        sa_damping
                    )

    logs.LOG.debug('< done computing disaggregation')


_DISAGG_RES_NAME_FMT = 'disagg(%(poe)s)-rlz-%(rlz)s-%(imt)s-%(wkt)s'


def _save_disagg_matrix(job, site, bin_edges, diss_matrix, lt_rlz,
                        investigation_time, imt, iml, poe, sa_period,
                        sa_damping):
    """
    Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
    :class:`~openquake.engine.db.models.DisaggResult`).

    :param job:
        :class:`openquake.engine.db.models.OqJob` representing the current job.
    :param site:
        :class:`openquake.hazardlib.site.Site`, containing the location
        geometry for these results.
    :param bin_edges, diss_matrix
        The outputs of :func:
        `openquake.hazardlib.calc.disagg.disaggregation`.
    :param lt_rlz:
        :class:`openquake.engine.db.models.LtRealization` to which these
        results belong.
    :param float investigation_time:
        Investigation time (years) for the calculation.
    :param imt:
        Intensity measure type (PGA, SA, etc.)
    :param float iml:
        Intensity measure level interpolated (using ``poe``) from the hazard
        curve at the ``site``.
    :param float poe:
        Disaggregation probability of exceedance value for this result.
    :param float sa_period:
        Spectral Acceleration period; only relevant when ``imt`` is 'SA'.
    :param float sa_damping:
        Spectral Acceleration damping; only relevant when ``imt`` is 'SA'.
    """
    # Silencing 'Too many arguments', 'Too many local variables'
    # pylint: disable=R0913,R0914
    disp_name = _DISAGG_RES_NAME_FMT
    disp_imt = imt
    if disp_imt == 'SA':
        disp_imt = 'SA(%s)' % sa_period

    disp_name_args = dict(poe=poe, rlz=lt_rlz.id, imt=disp_imt,
                          wkt=site.location.wkt2d)
    disp_name %= disp_name_args

    output = models.Output.objects.create_output(
        job, disp_name, 'disagg_matrix'
    )

    mag, dist, lon, lat, eps, trts = bin_edges
    models.DisaggResult.objects.create(
        output=output,
        lt_realization=lt_rlz,
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
        trts=trts,
        location=site.location.wkt2d,
        matrix=diss_matrix,
    )


class DisaggHazardCalculator(ClassicalHazardCalculator):
    """
    A calculator which performs disaggregation calculations in a distributed /
    parallelized fashion.

    See :func:`openquake.hazardlib.calc.disagg.disaggregation` for more
    details about the nature of this type of calculation.
    """
    def disagg_task_arg_gen(self, block_size):
        """
        Generate task args for the second phase of disaggregation calculations.
        This phase is concerned with computing the disaggregation histograms.

        :param int block_size:
            The number of items per task. In this case, this the number of
            sources for hazard curve calc task, or number of sites for disagg
            calc tasks.
        """
        realizations = models.LtRealization.objects.filter(
            hazard_calculation=self.hc)

        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
        # then distribute tasks for disaggregation histogram computation
        for lt_rlz in realizations:
            sm = self.rlz_to_sm[lt_rlz]
            sources = (self.sources_per_model[sm, 'point'] +
                       self.sources_per_model[sm, 'other'])
            for sites in general_utils.block_splitter(
                    self.hc.site_collection, block_size):
                yield self.job.id, sites, sources, lt_rlz, ltp

    def post_execute(self):
        """
        Start the disaggregation phase after hazard curve finalization.
        """
        super(DisaggHazardCalculator, self).post_execute()
        self.parallelize(
            compute_disagg,
            self.disagg_task_arg_gen(self.block_size()),
            self.log_percent)
