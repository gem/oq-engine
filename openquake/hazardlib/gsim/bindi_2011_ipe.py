# coding: utf-8
# The Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module exports :
class:`BindiEtAl2011Repi`,
class:`BindiEtAl2011RepiFixedH`,

"""
from __future__ import division
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class BindiEtAl2011Repi(GMPE):
    """
    Implements IPE developed by Dino Bindi et al. 2011 and published
    as "Intensity prediction equations for Central Asia"
    (Geo-physical journal international, 2011, 187,327-337).

    Model implemented by laurentiu.danciu@gmail.com
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {MMI}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    REQUIRES_DISTANCES = {'repi'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        mean = self._compute_mean(C, rup.mag, dists.repi, rup.hypo_depth)
        stddevs = self._get_stddevs(C, stddev_types, num_sites=dists.repi.shape)

        return mean, stddevs

    def _compute_mean(self, C, mag, repi, hypo_depth):
        """
        Compute mean value for MSK-64.
        """
        return (C['a1'] * mag + C['a2'] +
                self._get_term01(C, repi, hypo_depth))

    def _get_term01(self, C, repi, hypo_depth):
        h = hypo_depth
        term_repi = np.sqrt((repi**2+h**2)/h**2)
        term_h = np.sqrt(repi**2+h**2)-h
        return -C['a3']*np.log10(term_repi)-(C['a4']*term_h)

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            stddevs.append(C['sigma'] + np.zeros(num_sites))

        return stddevs

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper.Table 1 .page 331
    COEFFS = CoeffsTable(table="""\
    IMT       a1     a2      a3           a4   sigma
    MMI      0.898  1.215  1.809   0.003447   0.737
        """)


class BindiEtAl2011RepiFixedH(BindiEtAl2011Repi):
    """
    Implements IPE developed by Dino Bindi et al. 2011 and published
    as "Intensity prediction equations for Central Asia"
    (Geo-physical journal international, 2011, 187,327-337).
    for a fixed depth of 15 km and epicentral distance
    (equation 5 in the paper)
    Implements the Repi with fixed depth at 15km /coeff on Table 1

    Model implmented by laurentiu.danciu@gmail.com
    """
    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_DISTANCES = {'repi'}

    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Extends the Bindietal2011 IPE for Repi without a fixed
        depth of 15Km
        """
        C = self.COEFFS[imt]
        rup.hypo_depth = 15.

        mean, stddevs = super(BindiEtAl2011RepiFixedH, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        return mean,  stddevs

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper.
    COEFFS = CoeffsTable(table="""\
    IMT         a1     a2     a3          a4    sigma
    MMI      1.049  0.686  2.706   0.0001811    0.689
        """)
