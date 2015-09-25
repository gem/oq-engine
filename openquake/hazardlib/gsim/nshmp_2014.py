# The Hazard Library
# Copyright (C) 2015 GEM Foundation
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
Module exports :class:`AbrahamsonEtAl2014NSHMPUpper`
               :class:`AbrahamsonEtAl2014NSHMPLower`
               :class:`BooreEtAl2014NSHMPUpper`
               :class:`BooreEtAl2014NSHMPLower`
               :class:`CampbellBozorgnia2014NSHMPUpper`
               :class:`CampbellBozorgnia2014NSHMPLower`
               :class:`ChiouYoungs2014NSHMPUpper`
               :class:`ChiouYoungs2014NSHMPLower`
               :class:`Idriss2014NSHMPUpper`
               :class:`Idriss2014NSHMPLower`
"""
from __future__ import division
import numpy as np
# NGA West 2 GMPEs
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import \
    CampbellBozorgnia2014
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.idriss_2014 import Idriss2014


def nga_west2_epistemic_adjustment(magnitude, distance):
    """
    Applies the "average" adjustment factor for epistemic uncertainty
    as defined in Table 17 of Petersen et al., (2014)

                   R < 10.  | 10.0 <= R < 30.0  |    R >= 30.0
    -----------------------------------------------------------
      M < 6.0   |   0.37    |      0.22         |       0.22
    6 <= M <7.0 |   0.25    |      0.23         |       0.23
      M >= 7.0  |   0.40    |      0.36         |       0.33
    """
    if magnitude < 6.0:
        adjustment = 0.22 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.37
    elif magnitude >= 7.0:
        adjustment = 0.36 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.40
        adjustment[distance >= 30.0] = 0.33
    else:
        adjustment = 0.23 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.25
    return adjustment


class AbrahamsonEtAl2014NSHMPUpper(AbrahamsonEtAl2014):
    """
    Implements the positive NSHMP adjustment factor for the Abrahamson et al.
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(AbrahamsonEtAl2014NSHMPUpper, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class AbrahamsonEtAl2014NSHMPLower(AbrahamsonEtAl2014):
    """
    Implements the negative NSHMP adjustment factor for the Abrahamson et al.
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(AbrahamsonEtAl2014NSHMPLower, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class BooreEtAl2014NSHMPUpper(BooreEtAl2014):
    """
    Implements the positive NSHMP adjustment factor for the Boore et al.
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(BooreEtAl2014NSHMPUpper, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(rctx.mag, dctx.rjb),\
            stddevs


class BooreEtAl2014NSHMPLower(BooreEtAl2014):
    """
    Implements the negative NSHMP adjustment factor for the Boore et al.
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(BooreEtAl2014NSHMPLower, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rjb),\
            stddevs


class CampbellBozorgnia2014NSHMPUpper(CampbellBozorgnia2014):
    """
    Implements the positive NSHMP adjustment factor for the Campbell and
    Bozorgnia (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(CampbellBozorgnia2014NSHMPUpper, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class CampbellBozorgnia2014NSHMPLower(CampbellBozorgnia2014):
    """
    Implements the negative NSHMP adjustment factor for the Campbell and
    Bozorgnia (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(CampbellBozorgnia2014NSHMPLower, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class ChiouYoungs2014NSHMPUpper(ChiouYoungs2014):
    """
    Implements the positive NSHMP adjustment factor for the Chiou & Youngs
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(ChiouYoungs2014NSHMPUpper, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class ChiouYoungs2014NSHMPLower(ChiouYoungs2014):
    """
    Implements the negative NSHMP adjustment factor for the Chiou & Youngs
    (2014) NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(ChiouYoungs2014NSHMPLower, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class Idriss2014NSHMPUpper(Idriss2014):
    """
    Implements the positive NSHMP adjustment factor for the Idriss (2014)
    NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(Idriss2014NSHMPUpper, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class Idriss2014NSHMPLower(Idriss2014):
    """
    Implements the negative NSHMP adjustment factor for the Idriss (2014)
    NGA West 2 GMPE
    """
    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super(Idriss2014NSHMPLower, self).\
            get_mean_and_stddevs(sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs
