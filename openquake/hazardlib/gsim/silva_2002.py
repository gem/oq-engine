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
Module exports :class:`SilvaEtAl2002MblgAB1987NSHMP2008`,
:class:`SilvaEtAl2002MblgJ1996NSHMP2008`, :class:`SilvaEtAl2002MwNSHMP2008`,
:class:`SilvaEtAl2002SingleCornerSaturation`,
:class:`SilvaEtAl2002DoubleCornerSaturation`.
"""

import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87,
    mblg_to_mw_johnston_96,
    clip_mean)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class SilvaEtAl2002MblgAB1987NSHMP2008(GMPE):
    """
    Implements GMPE developed by Walter Silva, Nick Gregor and Robert Darragh
    and documented in "Development of regional hard rock attenuation relations
    for central and eastern north America" (2002). Document available at:
    http://pbadupws.nrc.gov/docs/ML0423/ML042310569.pdf

    This class replicates the algorithm as coded in the subroutine ``getSilva``
    in the ``hazgridXnga2.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    The class assumes rupture magnitude to be in Mblg scale (given that
    MFDs for central and eastern US are given in this scale). Therefore Mblg is
    converted to Mw using the Atkinson & Boore 1987 conversion equation.

    Coefficients are given for the B/C site conditions.
    """

    #: Supported tectonic region type is stable continental crust,
    #: given that the equations have been derived for central and eastern
    #: north America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the average horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude (Mblg).
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is rjb
    REQUIRES_DISTANCES = set(('rjb', ))

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.


    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mag = self._convert_magnitude(rup.mag)

        mean = (
            C['c1'] + C['c2'] * mag + C['c10'] * (mag - 6) ** 2 +
            (C['c6'] + C['c7'] * mag) * np.log(dists.rjb + np.exp(C['c4']))
        )
        mean = clip_mean(imt, mean)

        stddevs = self._compute_stddevs(C, dists.rjb.size, stddev_types)

        return mean, stddevs

    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Atkinson and Boore 1987
        equation
        """
        return mblg_to_mw_atkinson_boore_87(mag)

    def _compute_stddevs(self, C, num_sites, stddev_types):
        """
        Return total standard deviation.
        """
        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + C['sigma'])
        return stddevs

    #: Coefficient table obtained from coefficient arrays (c1, c2, c4, c6,
    #: c7, c10, sigma) defined in suroutine getSilva in hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT   c1       c2       c4     c6       c7        c10      sigma
    pga   5.9533  -0.11691  2.9   -3.42173  0.26461  -0.06810  0.8471
    0.1   5.9917  -0.02059  2.9   -3.25499  0.24527  -0.06853  0.8546
    0.2   4.2848   0.12490  2.8   -3.04591  0.22877  -0.08886  0.8338
    0.3   3.14919  0.23165  2.8   -2.96321  0.22112  -0.11352  0.8428
    0.5   1.15279  0.45254  2.8   -2.818    0.20613  -0.16423  0.8484
    1.0  -2.60639  0.88116  2.8   -2.58296  0.18098  -0.25757  0.8785
    2.0  -7.23821  1.41946  2.7   -2.26433  0.14984  -0.33999  1.0142
    5.0  -13.39    2.03488  2.5   -1.91969  0.12052  -0.35463  1.2253
    """)


class SilvaEtAl2002MblgJ1996NSHMP2008(SilvaEtAl2002MblgAB1987NSHMP2008):
    """
    Extend :class:`SilvaEtAl2002MblgAB1987NSHMP2008` but uses Johnston
    1996 equation for converting Mblg to Mw.
    """
    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Johnston 1996 equation
        """
        return mblg_to_mw_johnston_96(mag)


class SilvaEtAl2002MwNSHMP2008(SilvaEtAl2002MblgAB1987NSHMP2008):
    """
    Extend :class:`SilvaEtAl2002MblgAB1987NSHMP2008` but assumes magnitude
    to be in Mw scale, therefore no conversion is applied
    """
    def _convert_magnitude(self, mag):
        """
        Return magnitude value unchanged
        """
        return mag


class SilvaEtAl2002DoubleCornerSaturation(SilvaEtAl2002MwNSHMP2008):
    """
    This implements the Silva et al. (2002) GMPE for the double corner model
    with saturation as described in the report from Silva, W., N. Gregor and
    R. Darragh (2002), titled "DEVELOPMENT OF REGIONAL HARD ROCK ATTENUATION
    RELATIONS FOR CENTRAL AND EASTERN NORTH AMERICA" available at
    www.pacificengineering.org

    For the construction of verification tables - given the unavailability
    of an independent code - we digitized values from figures included in the
    report.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mag = self._convert_magnitude(rup.mag)
        mean = (
            C['c1'] + C['c2'] * mag + C['c10'] * (mag - 6) ** 2 +
            (C['c6'] + C['c7'] * mag) * np.log(dists.rjb + np.exp(C['c4']))
        )
        stddevs = self._compute_stddevs(C, dists.rjb.size, stddev_types)
        return mean, stddevs


    COEFFS = CoeffsTable(sa_damping=5, table="""\
        IMT      c1           c2           c4           c5         c6        c7           c8         c10      sigma_par    sigma
    +10.0000000  -16.16329    +1.9653500   +2.3000000   +0.0000000 -1.71374  +0.1054700   +0.0000000 -.32832  +0.4199000   +1.3429000
    +5.0000000   -12.17910    +1.6245100   +2.5000000   +0.0000000 -1.88291  +0.1156400   +0.0000000 -.30150  +0.4529000   +1.2228000
    +3.0003000   -9.24347     +1.3620100   +2.6000000   +0.0000000 -2.05193  +0.1295400   +0.0000000 -.24133  +0.4887000   +1.0871000
    +2.0000000   -6.86049     +1.1554800   +2.7000000   +0.0000000 -2.23472  +0.1461000   +0.0000000 -.19315  +0.5217000   +1.0095000
    +1.6000000   -5.75016     +1.0506100   +2.7000000   +0.0000000 -2.32003  +0.1554000   +0.0000000 -.17317  +0.5388000   +0.9450000
    +1.0000000   -3.10841     +0.7956100   +2.8000000   +0.0000000 -2.58562  +0.1819500   +0.0000000 -.15020  +0.5697000   +0.8739000
    +0.7500188   -1.68010     +0.6697100   +2.8000000   +0.0000000 -2.68318  +0.1926100   +0.0000000 -.14513  +0.5844000   +0.8815000
    +0.5000000   +0.1710400   +0.4866300   +2.8000000   +0.0000000 -2.81997  +0.2077300   +0.0000000 -.13719  +0.6016000   +0.8426000
    +0.4000000   +1.1769500   +0.3907800   +2.8000000   +0.0000000 -2.87626  +0.2135200   +0.0000000 -.12940  +0.6110000   +0.8320000
    +0.3000030   +2.2762600   +0.2703100   +2.8000000   +0.0000000 -2.95623  +0.2219300   +0.0000000 -.11697  +0.6231000   +0.8358000
    +0.2399981   +3.0470500   +0.1947100   +2.8000000   +0.0000000 -3.00223  +0.2263900   +0.0000000 -.10675  +0.6326000   +0.8272000
    +0.2000000   +3.6156800   +0.1431100   +2.8000000   +0.0000000 -3.03239  +0.2290000   +0.0000000 -.09861  +0.6412000   +0.8260000
    +0.1600000   +4.1928100   +0.0844100   +2.8000000   +0.0000000 -3.07579  +0.2330000   +0.0000000 -.08991  +0.6535000   +0.8290000
    +0.1499993   +4.3427700   +0.0691100   +2.8000000   +0.0000000 -3.08805  +0.2340900   +0.0000000 -.08764  +0.6587000   +0.8339000
    +0.1200005   +4.8166300   +0.0279300   +2.8000000   +0.0000000 -3.12224  +0.2368600   +0.0000000 -.08119  +0.6717000   +0.8485000
    +0.1000000   +5.1370600   -0.00173     +2.8000000   +0.0000000 -3.15185  +0.2392900   +0.0000000 -.07703  +0.6837000   +0.8468000
    +0.0800000   +5.9494200   -0.06741     +2.9000000   +0.0000000 -3.27328  +0.2482200   +0.0000000 -.07318  +0.6923000   +0.8476000
    +0.0700001   +6.1070800   -0.08387     +2.9000000   +0.0000000 -3.29509  +0.2500000   +0.0000000 -.07142  +0.6982000   +0.8521000
    +0.0599999   +6.2638400   -0.10044     +2.9000000   +0.0000000 -3.31911  +0.2519200   +0.0000000 -.06982  +0.7058000   +0.8602000
    +0.0550001   +6.3423800   -0.10886     +2.9000000   +0.0000000 -3.33222  +0.2529500   +0.0000000 -.06908  +0.7106000   +0.8604000
    +0.0500000   +6.4242300   -0.11726     +2.9000000   +0.0000000 -3.34604  +0.2540100   +0.0000000 -.06838  +0.7165000   +0.8675000
    +0.0400000   +6.6120400   -0.13370     +2.9000000   +0.0000000 -3.37593  +0.2561300   +0.0000000 -.06711  +0.7339000   +0.8795000
    +0.0322581   +7.3373600   -0.18563     +3.0000000   +0.0000000 -3.49824  +0.2645600   +0.0000000 -.06625  +0.7462000   +0.8869000
    +0.0250000   +7.5114500   -0.19862     +3.0000000   +0.0000000 -3.52888  +0.2665200   +0.0000000 -.06568  +0.7534000   +0.8902000
    +0.0200000   +7.5564800   -0.20898     +3.0000000   +0.0000000 -3.55306  +0.2685300   +0.0000000 -.06551  +0.7561000   +0.8939000
    +0.0100000   +6.1221300   -0.16489     +2.9000000   +0.0000000 -3.43941  +0.2660100   +0.0000000 -.06925  +0.6994000   +0.8468000
    pga          +5.9119600   -0.15727     +2.9000000   +0.0000000 -3.42401  +0.2656400   +0.0000000 -.07004  +0.6912000   +0.8400000
    """)


class SilvaEtAl2002SingleCornerSaturation(SilvaEtAl2002DoubleCornerSaturation):
    """
    This implements the Silva et al. (2002) GMPE for the single corner model
    with saturation.
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
        IMT      c1           c2           c4           c5         c6        c7           c8         c10      sigma_par    sigma
    +10.0000000  -17.69763    +2.3387700   +2.3000000   +0.0000000 -1.75359  +0.1107100   +0.0000000 -.28005  +0.4204000   +1.3431000
    +5.0000000   -13.69697    +2.0348800   +2.5000000   +0.0000000 -1.91969  +0.1205200   +0.0000000 -.35463  +0.4597000   +1.2253000
    +3.0003000   -10.33313    +1.7175500   +2.6000000   +0.0000000 -2.08560  +0.1340100   +0.0000000 -.36316  +0.4981000   +1.0914000
    +2.0000000   -7.42051     +1.4194600   +2.7000000   +0.0000000 -2.26433  +0.1498400   +0.0000000 -.33999  +0.5309000   +1.0142000
    +1.6000000   -6.03692     +1.2582100   +2.7000000   +0.0000000 -2.33925  +0.1576500   +0.0000000 -.31816  +0.5472000   +0.9498000
    +1.0000000   -2.89906     +0.8811600   +2.8000000   +0.0000000 -2.58296  +0.1809800   +0.0000000 -.25757  +0.5767000   +0.8785000
    +0.7500188   -1.22930     +0.6851800   +2.8000000   +0.0000000 -2.68016  +0.1912700   +0.0000000 -.21501  +0.5914000   +0.8861000
    +0.5000000   +0.6953900   +0.4525400   +2.8000000   +0.0000000 -2.81800  +0.2061300   +0.0000000 -.16423  +0.6097000   +0.8484000
    +0.4000000   +1.6422800   +0.3475100   +2.8000000   +0.0000000 -2.87774  +0.2121500   +0.0000000 -.13838  +0.6199000   +0.8386000
    +0.3000030   +2.6068900   +0.2316500   +2.8000000   +0.0000000 -2.96321  +0.2211200   +0.0000000 -.11352  +0.6325000   +0.8428000
    +0.2399981   +3.2531900   +0.1661600   +2.8000000   +0.0000000 -3.01272  +0.2258900   +0.0000000 -.09854  +0.6423000   +0.8346000
    +0.2000000   +3.7195300   +0.1249000   +2.8000000   +0.0000000 -3.04591  +0.2287700   +0.0000000 -.08886  +0.6511000   +0.8338000
    +0.1600000   +4.1841600   +0.0787500   +2.8000000   +0.0000000 -3.09159  +0.2329700   +0.0000000 -.07992  +0.6633000   +0.8368000
    +0.1499993   +4.3041700   +0.0669500   +2.8000000   +0.0000000 -3.10445  +0.2341100   +0.0000000 -.07779  +0.6685000   +0.8417000
    +0.1200005   +5.1732000   +0.0018800   +2.9000000   +0.0000000 -3.22475  +0.2428600   +0.0000000 -.07200  +0.6814000   +0.8562000
    +0.1000000   +5.4378200   -0.02059     +2.9000000   +0.0000000 -3.25499  +0.2452700   +0.0000000 -.06853  +0.6933000   +0.8546000
    +0.0800000   +5.7063100   -0.04389     +2.9000000   +0.0000000 -3.29005  +0.2479900   +0.0000000 -.06548  +0.7017000   +0.8553000
    +0.0700001   +5.8347700   -0.05663     +2.9000000   +0.0000000 -3.31101  +0.2496500   +0.0000000 -.06416  +0.7077000   +0.8599000
    +0.0599999   +5.9639700   -0.06970     +2.9000000   +0.0000000 -3.33411  +0.2514500   +0.0000000 -.06300  +0.7152000   +0.8680000
    +0.0550001   +6.5676100   -0.11492     +3.0000000   +0.0000000 -3.44099  +0.2590400   +0.0000000 -.06249  +0.7200000   +0.8682000
    +0.0500000   +6.6393700   -0.12193     +3.0000000   +0.0000000 -3.45478  +0.2600800   +0.0000000 -.06201  +0.7259000   +0.8753000
    +0.0400000   +6.8101200   -0.13594     +3.0000000   +0.0000000 -3.48499  +0.2622000   +0.0000000 -.06115  +0.7429000   +0.8870000
    +0.0322581   +6.9787800   -0.14713     +3.0000000   +0.0000000 -3.51228  +0.2639200   +0.0000000 -.06051  +0.7550000   +0.8943000
    +0.0250000   +7.1408700   -0.15876     +3.0000000   +0.0000000 -3.54274  +0.2658900   +0.0000000 -.06019  +0.7619000   +0.8974000
    +0.0200000   +7.1744500   -0.16806     +3.0000000   +0.0000000 -3.56511  +0.2678600   +0.0000000 -.06041  +0.7643000   +0.9008000
    +0.0100000   +5.7388500   -0.12424     +2.9000000   +0.0000000 -3.43887  +0.2651000   +0.0000000 -.06699  +0.7079000   +0.8538000
    pga          +5.5345900   -0.11691     +2.9000000   +0.0000000 -3.42173  +0.2646100   +0.0000000 -.06810  +0.6998000   +0.8471000
    """)

