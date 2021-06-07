#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
6th Generation Seismic Hazard Model of Canada (CanadaSHM6) Active Crust GMMs.

The GMMs are not valid for PGV and outside of the period range of 0.1 - 10.0s.

Documentation is available in:

- Kolaj, M., Halchuk, S., Adams, J., Allen, T.I. (2020): Sixth Generation
  Seismic Hazard Model of Canada: input files to produce values proposed for
  the 2020 National Building Code of Canada; Geological Survey of Canada,
  Open File 8630, 2020, 15 pages, https://doi.org/10.4095/327322

- Kolaj, M., Adams, J., Halchuk, S (2020): The 6th Generation seismic hazard
  model of Canada. 17th World Conference on Earthquake Engineering, Sendai,
  Japan. Paper 1c-0028.

- Kolaj, M., Allen, T., Mayfield, R., Adams, J., Halchuk, S (2019):
  Ground-motion models for the 6th Generation Seismic Hazard Model of Canada.
  12th Canadian Conference on Earthquake Engineering, Quebec City, Canada.
"""

import numpy as np

from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014)

METRES_PER_KM = 1000.

COEFFS_AB06 = CoeffsTable(sa_damping=5, table="""\
    IMT c
    pgv 1.23
    pga  0.891
    0.005 0.791
    0.05 0.791
    0.1 1.072
    0.2 1.318
    0.3 1.38
    0.5 1.38
    1.0 1.288
    2.0 1.230
    5.0 1.148
    10.0 1.072
    """)


def CanadaSHM6_hardrock_site_factor(A1100, A2000, vs30, imt):
    """
    Returns CanadaSHM6 hard rock (Vs30 > 1100 m/s) amplification factors in
    log units.

    :param A1100:
        Native GMM site factor for 1100 m/s (relative to 760 m/s)
    :param A2000:
        Native GMM site factor for 2000 m/s (relative to 760 m/s)
    :param vs30:
        Array of Vs30 values
    :param imt:
        OQ imt class
    """

    # 760-to-2000 factor calculated from AB06 following methodology outlined
    # in AA13
    AB06 = np.log(1./COEFFS_AB06[imt]['c'])

    # Amplification at 2000 m/s for CanadaSHM6
    fac_2000 = np.min([A1100, np.max([A2000, AB06])])

    # Log-Log interpolate for amplification factors between 1100 and 2000
    F = np.interp(np.log(vs30), np.log([1100., 2000.]), [A1100, fac_2000])

    return F


class CanSHM6_ActiveCrust_BooreEtAl2014(BooreEtAl2014):
    """
    Boore et al., 2014 with CanadaSHM6 modifications to amplification factors
    for vs30 > 1100. The GMM is not valid for PGV and outside of the
    period range of 0.1 - 10.0s.

    Please also see the information in the header.
    """
    experimental = True

    def _get_site_scaling(self, C, pga_rock, sites, period, rjb):
        """
        Returns the site-scaling term (equation 5), broken down into a
        linear scaling, a nonlinear scaling and a basin scaling

        CanadaSHM6 edits: modified linear site term for Vs30 > 1100
        """
        # Native site factor for BSSA14
        flin = self._get_linear_site_term(C, sites.vs30)

        # Need site factors at Vs30 = 1100 and 2000 to calculate
        # CanadaSHM6 hard rock site factors
        BSSA14_1100 = self._get_linear_site_term(C, np.array([1100.0]))
        BSSA14_2000 = self._get_linear_site_term(C, np.array([2000.0]))

        # Need OQ IMT for CanadaSHM6 hard rock factor
        if period == 0.0:
            imt = PGA()
        elif period == -1.0:
            imt = PGV()
        else:
            try:
                imt = SA(period)
            except:
                imt = period

        # CanadaSHM6 hard rock site factor
        flin[sites.vs30 > 1100] = CanadaSHM6_hardrock_site_factor(
                                                BSSA14_1100[0],
                                                BSSA14_2000[0],
                                                sites.vs30[sites.vs30 > 1100],
                                                imt)

        fnl = self._get_nonlinear_site_term(C, sites.vs30, pga_rock)
        fbd = self._get_basin_depth_term(C, sites, period)  # returns 0

        return flin + fnl + fbd


class CanadaSHM6_ActiveCrust_CampbellBozorgnia2014(CampbellBozorgnia2014):
    """
    Campbell and Bozorgnia, 2014 with CanadaSHM6 modifications to amplification
    factors for vs30 > 1100 and the removal of the basin term (i.e., returns
    mean values on the GMM-centered z1pt0 value).

    Please also see the information in the header.
    """
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    experimental = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        CanadaSHM6 edits: added IMT to get_mean_values()
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]

        # Get mean and standard deviation of PGA on rock (Vs30 1100 m/s^2)
        pga1100 = np.exp(self.get_mean_values(C_PGA, sites, rup, dists, None,
                                              imt))
        # Get mean and standard deviations for IMT
        mean = self.get_mean_values(C, sites, rup, dists, pga1100, imt)
        if isinstance(imt, PGV) is False and imt.period <= 0.25:
            # According to Campbell & Bozorgnia (2013) [NGA West 2 Report]
            # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
            # Get PGA on soil
            pga = self.get_mean_values(C_PGA, sites, rup, dists, pga1100, imt)
            idx = mean <= pga
            mean[idx] = pga[idx]

        # Get standard deviations
        stddevs = self._get_stddevs(C,
                                    C_PGA,
                                    rup,
                                    sites,
                                    pga1100,
                                    stddev_types)
        return mean, stddevs

    def get_mean_values(self, C, sites, rup, dists, a1100, imt):
        """
        Returns the mean values for a specific IMT

        CanadaSHM6 edits: added IMT to get_mean_values(),
                          modified shallow site response term
                          removed basin term
        """
        if isinstance(a1100, np.ndarray):
            # Site model defined
            temp_vs30 = sites.vs30

        else:
            # Default site and basin model
            temp_vs30 = 1100.0 * np.ones(len(sites.vs30))

        return (self._get_magnitude_term(C, rup.mag) +
                self._get_geometric_attenuation_term(C, rup.mag, dists.rrup) +
                self._get_style_of_faulting_term(C, rup) +
                self._get_hanging_wall_term(C, rup, dists) +
                self._get_shallow_site_response_term_CanadaSHM6(C, temp_vs30,
                                                                a1100, imt) +
                self._get_hypocentral_depth_term(C, rup) +
                self._get_fault_dip_term(C, rup) +
                self._get_anelastic_attenuation_term(C, dists.rrup))

    def _get_shallow_site_response_term_CanadaSHM6(self, C, vs30, pga_rock,
                                                   imt):
        """
        Returns the mean values for a specific IMT

        CanadaSHM6 edits: modified linear site term for Vs30 > 1100
        """
        # Native site factor for CB14
        CB14_vs = self._get_shallow_site_response_term(C, vs30, pga_rock)

        # Need site factors at Vs30 = 760, 1100 and 2000 to calculate
        # CanadaSHM6 hard rock site factors
        CB14_1100 = self._get_shallow_site_response_term(C, np.array([1100.]),
                                                         np.array([0.]))
        CB14_760 = self._get_shallow_site_response_term(C, np.array([760.]),
                                                        np.array([0.]))
        CB14_2000 = self._get_shallow_site_response_term(C, np.array([2000.]),
                                                         np.array([0.]))

        # CB14 amplification factors relative to Vs30=760 to be consistent
        # with CanadaSHM6 hardrock site factor
        CB14_2000div760 = CB14_2000[0] - CB14_760[0]
        CB14_1100div760 = CB14_1100[0] - CB14_760[0]

        # CanadaSHM6 hard rock site factor
        F = CanadaSHM6_hardrock_site_factor(CB14_1100div760, CB14_2000div760,
                                            vs30[vs30 >= 1100], imt)

        # for Vs30 > 1100 add CB14 amplification at 760 and CanadaSHM6 factor
        CB14_vs[vs30 >= 1100] = F + CB14_760

        return CB14_vs
