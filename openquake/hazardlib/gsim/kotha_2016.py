# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Module exports :class:`KothaEtAl2016`,
               :class:`KothaEtAl2016Italy`,
               :class:`KothaEtAl2016Turkey`,
               :class:`KothaEtAl2016Others`,
"""
import os
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

KOTHA_CSV = os.path.join(os.path.dirname(__file__), 'kotha_2016.csv')


class KothaEtAl2016(GMPE):
    """
    Implements unregionalised form of the European GMPE of:
    Kotha, S. R., Bindi, D. and Cotton, F. (2016) "Partially non-ergodic
    region specific GMPE for Europe and the Middle-East", Bull. Earthquake Eng.
    14: 1245 - 1263
    """
    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude only (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        C = self.COEFFS[imt]

        mean = (self._get_magnitude_term(C, rup.mag) +
                self._get_distance_term(C, dists.rjb, rup.mag) +
                self._get_site_term(C, sites.vs30))

        # Units of GMPE are in terms of m/s (corrected in an Erratum)
        # Convert to g
        if imt.string.startswith(('PGA', 'SA')):
            mean = np.log(np.exp(mean) / g)
        else:
            # For PGV convert from m/s to cm/s/s
            mean = np.log(np.exp(mean) * 100.)

        # Get standard deviations
        stddevs = self._get_stddevs(C, stddev_types, dists.rjb.shape)
        return mean, stddevs

    def _get_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term - equation 3
        """
        if mag >= self.CONSTS["Mh"]:
            return C["e1"] + C["b3"] * (mag - self.CONSTS["Mh"])
        else:
            return C["e1"] + (C["b1"] * (mag - self.CONSTS["Mh"])) +\
                (C["b2"] * (mag - self.CONSTS["Mh"]) ** 2.)

    def _get_distance_term(self, C, rjb, mag):
        """
        Returns the general distance scaling term - equation 2
        """
        c_3 = self._get_anelastic_coeff(C)
        rval = np.sqrt(rjb ** 2. + C["h"] ** 2.)
        return (C["c1"] + C["c2"] * (mag - self.CONSTS["Mref"])) *\
            np.log(rval / self.CONSTS["Rref"]) +\
            c_3 * (rval - self.CONSTS["Rref"])

    def _get_anelastic_coeff(self, C):
        """
        This function is a regionalisable parameter - will be modified in
        other classes
        """
        return C["c3"]

    def _get_site_term(self, C, vs30):
        """
        Returns only a linear site amplification term
        """
        dg1, dg2 = self._get_regional_site_term(C)
        return (C["g1"] + dg1) + (C["g2"] + dg2) * np.log(vs30)

    def _get_regional_site_term(self, C):
        """
        Region specific site term - modified in subclasses
        """
        return 0., 0.

    def _get_stddevs(self, C, stddev_types, stddev_shape):
        """
        Returns a total standard deviation
        Intra-event standard deviation should be treated here as
        sqrt(phi0 ** 2. + phiS2S ** 2.)
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['sigma'] + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                phi = np.sqrt(C['phi0'] ** 2. + C["phiS2S"] ** 2.)
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(stddev_shape))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table=open(KOTHA_CSV).read())

    CONSTS = {"Mh": 6.75, "Mref": 5.5, "Rref": 1.0}


class KothaEtAl2016Italy(KothaEtAl2016):
    """
    Regional varient of the Kotha et al. (2016) GMPE for the Italy case
    """
    def _get_anelastic_coeff(self, C):
        """
        Returns the anelastic adjustment for the Italy case
        """
        return C["c3"] + C["Dc3IT"]

    def _get_regional_site_term(self, C):
        """
        Region specific site term for the Italy case
        """
        return C["Dg1IT"], C["Dg2IT"]


class KothaEtAl2016Turkey(KothaEtAl2016):
    """
    Regional varient of the Kotha et al. (2016) GMPE for the Turkey case
    """
    def _get_anelastic_coeff(self, C):
        """
        Returns the anelastic adjustment for the Turkey case
        """
        return C["c3"] + C["Dc3TR"]

    def _get_regional_site_term(self, C):
        """
        Region specific site term for the Turkey case
        """
        return C["Dg1TR"], C["Dg2TR"]


class KothaEtAl2016Other(KothaEtAl2016):
    """
    Regional varient of the Kotha et al. (2016) GMPE for the "Other" case
    """
    def _get_anelastic_coeff(self, C):
        """
        Returns the anelastic adjustment for the Other case
        """
        return C["c3"] + C["Dc3OTH"]

    def _get_regional_site_term(self, C):
        """
        Region specific site term for the Other case
        """
        return C["Dg1OTH"], C["Dg2OTH"]
