# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
:class:`SilvaEtAl2002MblgJ1996NSHMP2008`,
:class:`SilvaEtAl2002MwNSHMP2008`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87,
    mblg_to_mw_johnston_96,
    clip_mean
)
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
