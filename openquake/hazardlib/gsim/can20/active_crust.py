#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Preliminary versions of the 6th Generation Seismic Hazard Model of Canada
(CanadaSHM6) Active Crust GMMs.

The GMMs are not valid for PGV and outside of the period range of 0.1 - 10.0s.

Warning: These GMMs are non-final and are subject to change.

The final documentation for the GMMs is being prepared. Preliminary
documentation is available in:

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
