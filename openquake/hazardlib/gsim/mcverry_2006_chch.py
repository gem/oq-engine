# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`McVerry2006AscChch`, :class:`McVerry2006ChchStressDrop`,
and :class:`McVerry2006AscChchAdditionalSigma`
"""
import numpy as np
import shapely.geometry

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.mcverry_2006 import McVerry2006AscSC
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class McVerry2006Chch(McVerry2006AscSC):
    """
    Extends McVerry2006AscSC to implement modifications required for the
    Canterbury Seismic Hazard Model (CSHM).
    """
    #: This implementation is non-verified because the model has not been
    #: published, nor is independent code available.
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        # Compute SA with primed coeffs and PGA with both unprimed and
        # primed coeffs
        C = self.COEFFS_PRIMED[imt]
        C_PGA = self.COEFFS_PRIMED[PGA()]
        C_PGA_unprimed = self.COEFFS_UNPRIMED[PGA()]
        SC = self.STRESS_COEFFS[imt]

        # Get S term to determine if consider site term is applied
        S = self._get_site_class(sites)

        # Abrahamson and Silva (1997) hanging wall term. This is not used
        # in the latest version of GMPE but is defined in functional form in
        # the paper so we keep it here as a placeholder
        f4HW = self._compute_f4(C, rup.mag, dists.rrup)

        # Flags for rake angles
        CN, CR = self._get_fault_mechanism_flags(rup.rake)

        # Get volcanic path distance which Rvol=0 for current implementation
        # of McVerry2006Asc, but kept here as placeholder for future use
        rvol = self._get_volcanic_path_distance(dists.rrup)

        # Get delta_C and delta_D terms for site class
        delta_C, delta_D = self._get_deltas(sites)

        # Get Atkinson and Boore (2006) stress drop factors or additional
        # standard deviation adjustment. Only apply these factors to sources
        # located within the boundaries of the CSHM.
        in_cshm = self._check_in_cshm_polygon(rup)
        if in_cshm is True:
            stress_drop_factor = self._compute_stress_drop_adjustment(SC,
                                                                      rup.mag)
            additional_sigma = self._compute_additional_sigma()
        else:
            stress_drop_factor = 0
            additional_sigma = 0

        # Compute lnPGA_ABCD primed
        lnPGAp_ABCD = self._compute_mean(C_PGA, S, rup.mag, dists.rrup, rvol,
                                         rup.hypo_depth, CN, CR, f4HW,
                                         delta_C, delta_D)

        # Compute lnPGA_ABCD unprimed
        lnPGA_ABCD = self._compute_mean(C_PGA_unprimed, S, rup.mag, dists.rrup,
                                        rvol, rup.hypo_depth, CN, CR, f4HW,
                                        delta_C, delta_D)

        # Compute lnSA_ABCD
        lnSAp_ABCD = self._compute_mean(C, S, rup.mag, dists.rrup, rvol,
                                        rup.hypo_depth, CN, CR, f4HW,
                                        delta_C, delta_D)

        # Stage 3: Equation 6 SA_ABCD(T). This is lnSA_ABCD
        # need to calculate final lnSA_ABCD from non-log values but return log
        mean = np.log(np.exp(lnSAp_ABCD) *
                      (np.exp(lnPGA_ABCD) /
                       np.exp(lnPGAp_ABCD))) + stress_drop_factor

        # Compute standard deviations
        C_STD = self.COEFFS_STD[imt]
        stddevs = self._get_stddevs_chch(
            C_STD, rup.mag, stddev_types, sites, additional_sigma
        )

        return mean, stddevs

    def _get_stddevs_chch(self, C, mag, stddev_types, sites, additional_sigma):
        """
        Add additional 'epistemic' uncertainty to the total uncertainty, as
        specified in the Canterbury Seismic Hazard Model.
        """
        num_sites = sites.siteclass.size
        sigma_intra = np.zeros(num_sites)

        # interevent stddev
        tau = sigma_intra + C['tau']

        # intraevent std (equations 8a-8c page 29)
        if mag < 5.0:
            sigma_intra += C['sigmaM6'] - C['sigSlope']
        elif 5.0 <= mag < 7.0:
            sigma_intra += C['sigmaM6'] + C['sigSlope'] * (mag - 6)
        else:
            sigma_intra += C['sigmaM6'] + C['sigSlope']

        std = []

        for stddev_type in stddev_types:
            if stddev_type == const.StdDev.TOTAL:
                # equation 9 page 29
                std += [np.sqrt(sigma_intra**2 + tau**2 + additional_sigma**2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                std.append(np.sqrt(sigma_intra + (additional_sigma**2)/2))
            elif stddev_type == const.StdDev.INTER_EVENT:
                std.append(np.sqrt(tau + (additional_sigma**2)/2))

        return std

    def _compute_stress_drop_adjustment(self, SC, mag):
        """
        No adjustment for base class
        """
        return 0

    def _compute_additional_sigma(self):
        """
        No adjustment for base class
        """
        return 0

    def _check_in_cshm_polygon(self, rup):
        """
        Checks if any part of the rupture surface mesh is located within the
        intended boundaries of the Canterbury Seismic Hazard Model in
        Gerstenberger et al. (2014), Seismic hazard modelling for the recovery
        of Christchurch, Earthquake Spectra, 30(1), 17-29.
        """
        lats = np.ravel(rup.surface.mesh.array[1])
        lons = np.ravel(rup.surface.mesh.array[0])
        # These coordinates are provided by M Gerstenberger (personal
        # communication, 10 August 2018)
        polygon = shapely.geometry.Polygon([(171.6, -43.3), (173.2, -43.3),
                                            (173.2, -43.9), (171.6, -43.9)])
        points_in_polygon = [
            shapely.geometry.Point(lons[i], lats[i]).within(polygon)
            for i in np.arange(len(lons))]
        in_cshm = any(points_in_polygon)

        return in_cshm

    #: Coefficient table (Atkinson and Boore, 2006, table 7, page 2201)
    STRESS_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    delta  M1    Mh
    pga    0.15   0.50  5.50
    0.025  0.15   0.00  5.00
    0.031  0.15   0.00  5.00
    0.04   0.15   0.00  5.00
    0.05   0.15   0.00  5.00
    0.063  0.15   0.17  5.17
    0.079  0.15   0.34  5.34
    0.1    0.15   0.50  5.50
    0.126  0.15   1.15  5.67
    0.158  0.15   1.85  5.84
    0.199  0.15   2.50  6.00
    0.251  0.15   2.90  6.12
    0.315  0.15   3.30  6.25
    0.397  0.15   3.65  6.37
    0.5    0.15   4.00  6.50
    0.629  0.15   4.17  6.70
    0.794  0.15   4.34  6.95
    1.00   0.15   4.50  7.20
    1.25   0.15   4.67  7.45
    1.587  0.15   4.84  7.70
    2.0    0.15   5.00  8.00
    2.5    0.15   5.25  8.12
    3.125  0.15   5.50  8.25
    4.0    0.15   5.75  8.37
    5.0    0.15   6.00  8.50
    pgv    0.11   2.00  5.50
    """)


class McVerry2006ChchStressDrop(McVerry2006Chch):
    """
    Extend :class:`McVerry2006AscChch` to implement the 'stress drop'
    factors developed in:
    McVerry, G., Gerstenberger, M., Rhoades, D., 2011. "Evaluation of the
    Z-factor and peak ground accelerations for Christchurch following the
    13 June 2011 earthquake", GNS Science Report 2011/45, 29p.

    The coefficient table is identical to that in Atkinson, G. and Boore,
    D., (2006), "Earthquake ground motion prediction equations for eastern
    North America, BSSA, 96(6), 2181-2205, doi:10.1785/0120050245.
    with a stress drop ratio of 1.5
    """

    def _compute_stress_drop_adjustment(self, SC, mag):
        """
        Compute equation (6) p. 2200 from Atkinson and Boore (2006). However,
        the ratio of scale factors is in log space rather than linear space,
        to reflect that log PSA scales linearly with log stress drop. Then
        convert from log10 to natural log (G McVerry, personal communication).
        """
        scale_fac = 1.5
        return np.log(10 ** ((np.log(scale_fac) / np.log(2)) * np.minimum(
            SC['delta'] + 0.05,
            0.05 + SC['delta'] * (
                np.maximum(mag - SC['M1'], 0) / (SC['Mh'] - SC['M1'])))
                            )
                      )


class McVerry2006ChchAdditionalSigma(McVerry2006Chch):
    """
    Extend :class:`McVerry2006AscChch` to implement the 'additional
    epistemic uncertainty' version of the model in:
    McVerry, G., Gerstenberger, M., Rhoades, D., 2011. "Evaluation of the
    Z-factor and peak ground accelerations for Christchurch following the
    13 June 2011 earthquake", GNS Science Report 2011/45, 29p.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35
