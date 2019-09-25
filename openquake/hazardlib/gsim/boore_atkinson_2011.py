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
Module exports :class:`BooreAtkinson2011`,
               :class:`Atkinson2008prime`
"""
import numpy as np

from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const


class BooreAtkinson2011(BooreAtkinson2008):
    """
    Implements GMPE based on the corrections proposed by Gail M. Atkinson
    and D. Boore in 2011 and published as "Modifications to Existing
    Ground-Motion Prediction Equations in Light of New Data " (2011,
    Bulletin of the Seismological Society of America, Volume 101, No. 3,
    pages 1121-1135).
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # get mean and std using the superclass
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)

        # correction factor (see Atkinson and Boore, 2011; equation 5 at
        # page 1126 and nga08_gm_tmr.for line 508
        corr_fact = 10.0**(np.max([0, 3.888 - 0.674 * rup.mag]) -
                           (np.max([0, 2.933 - 0.510 * rup.mag]) *
                            np.log10(dists.rjb + 10.)))

        return np.log(np.exp(mean)*corr_fact), stddevs


class Atkinson2008prime(BooreAtkinson2011):
    """
    Implements the Boore & Atkinson (2011) adjustment to the Atkinson (2008)
    GMPE (not itself implemented in OpenQuake)
    """
    # GMPE is defined for application to Eastern North America (Stable Crust)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # get mean and std using the superclass
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        
        A08 = self.A08_COEFFS[imt]
        f_ena = 10.0 ** (A08["c"] + A08["d"] * dists.rjb)

        return np.log(np.exp(mean)*f_ena), stddevs


    A08_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c         d
    pgv     0.450   0.00211
    pga     0.419   0.00039
    0.005   0.417   0.00192
    0.050   0.417   0.00192
    0.100   0.245   0.00273
    0.200   0.042   0.00232
    0.300  -0.078   0.00190
    0.500  -0.180   0.00180
    1.000  -0.248   0.00153
    2.000  -0.214   0.00117
    3.030  -0.084   0.00091
    5.000   0.000   0.00000
    10.00   0.000   0.00000
    """)
