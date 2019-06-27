# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import numpy as np
from openquake.hazardlib.gsim.base import _norm_sf, _truncnorm_sf
from openquake.hazardlib import const
# NGA West 2 GMPEs
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import \
    CampbellBozorgnia2014
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.idriss_2014 import Idriss2014
# Required for Atkinson and Macias (2009)
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.can15.sinter import SInterCan15Mid


class AtkinsonMacias2009NSHMP2014(AtkinsonMacias2009):
    """
    Implements an adjusted version of the Atkinson and Macias (2009) GMPE.
    The motion is scaled B/C conditions following the approach described in
    Atkinson and Adams (2013) and implemented in
    :mod:`openquake.hazardlib.gsim.can15.sinter`.
    """

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        cff = SInterCan15Mid.SITE_COEFFS[imt]
        mean += np.log(cff['mf'])
        return mean, stddevs


def nga_west2_epistemic_adjustment(magnitude, distance):
    """
    Applies the "average" adjustment factor for epistemic uncertainty
    as defined in Table 17 of Petersen et al., (2014)::

                 |  R < 10.  | 10.0 <= R < 30.0  |    R >= 30.0
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


DEFAULT_WEIGHTING = [(0.185, -1.), (0.63, 0.), (0.185, 1.)]


def get_weighted_poes(gsim, sctx, rctx, dctx, imt, imls, truncation_level,
                      weighting=DEFAULT_WEIGHTING):
    """
    This function implements the NGA West 2 GMPE epistemic uncertainty
    adjustment factor without re-calculating the actual GMPE each time.

    :param gsim:
        Instance of the GMPE
    :param list weighting:
        Weightings as a list of tuples of (weight, number standard deviations
        of the epistemic uncertainty adjustment)
    """
    if truncation_level is not None and truncation_level < 0:
        raise ValueError('truncation level must be zero, positive number '
                         'or None')
    gsim._check_imt(imt)
    adjustment = nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup)
    adjustment = adjustment.reshape(adjustment.shape + (1, ))
    if truncation_level == 0:
        # zero truncation mode, just compare imls to mean
        imls = gsim.to_distribution_values(imls)
        mean, _ = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt, [])
        mean = mean.reshape(mean.shape + (1, ))
        output = np.zeros([mean.shape[0], imls.shape[0]])
        for (wgt, fct) in weighting:
            output += (wgt *
                       (imls <= (mean + (fct * adjustment))).astype(float))
        return output
    else:
        # use real normal distribution
        assert (const.StdDev.TOTAL
                in gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
        imls = gsim.to_distribution_values(imls)
        mean, [stddev] = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                   [const.StdDev.TOTAL])
        mean = mean.reshape(mean.shape + (1, ))
        stddev = stddev.reshape(stddev.shape + (1, ))
        output = np.zeros([mean.shape[0], imls.shape[0]])
        for (wgt, fct) in weighting:
            values = (imls - (mean + (fct * adjustment))) / stddev
            if truncation_level is None:
                output += (wgt * _norm_sf(values))
            else:
                output += (wgt * _truncnorm_sf(truncation_level, values))
        return output


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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class AbrahamsonEtAl2014NSHMPMean(AbrahamsonEtAl2014):
    """
    Implements the Abrahamson et al (2014) GMPE for application to the
    weighted mean case
    """
    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Adapts the original `get_poes()` from the :class:
        openquake.hazardlib.gsim.base.GMPE to call a function that take the
        weighted sum of the PoEs from the epistemic uncertainty adjustment
        """
        return get_weighted_poes(self, sctx, rctx, dctx, imt, imls,
                                 truncation_level)


class BooreEtAl2014NSHMPUpper(BooreEtAl2014):
    """
    Implements the positive NSHMP adjustment factor for the Boore et al.
    (2014) NGA West 2 GMPE
    """
    # Originally Boore et al. (2014) requires only Rjb, but the epistemic
    # adjustment factors are given in terms of Rrup, so both are required here
    REQUIRES_DISTANCES = set(("rjb", "rrup"))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean + nga_west2_epistemic_adjustment(
            rctx.mag, dctx.rrup), stddevs


class BooreEtAl2014NSHMPLower(BooreEtAl2014):
    """
    Implements the negative NSHMP adjustment factor for the Boore et al.
    (2014) NGA West 2 GMPE
    """
    # See similar comment above
    REQUIRES_DISTANCES = set(("rjb", "rrup"))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class BooreEtAl2014NSHMPMean(BooreEtAl2014):
    """
    Implements the Boore et al (2014) GMPE for application to the
    weighted mean case
    """
    # See similar comment above
    REQUIRES_DISTANCES = set(("rjb", "rrup"))

    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Adapts the original `get_poes()` from the :class:
        openquake.hazardlib.gsim.base.GMPE to call a function that take the
        weighted sum of the PoEs from the epistemic uncertainty adjustment
        """
        return get_weighted_poes(self, sctx, rctx, dctx, imt, imls,
                                 truncation_level)


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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class CampbellBozorgnia2014NSHMPMean(CampbellBozorgnia2014):
    """
    Implements the Campbell & Bozorgnia (2014) GMPE for application to the
    weighted mean case
    """
    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Adapts the original `get_poes()` from the :class:
        openquake.hazardlib.gsim.base.GMPE to call a function that take the
        weighted sum of the PoEs from the epistemic uncertainty adjustment
        """
        return get_weighted_poes(self, sctx, rctx, dctx, imt, imls,
                                 truncation_level)


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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class ChiouYoungs2014NSHMPMean(ChiouYoungs2014):
    """
    Implements the Chiou & Youngs (2014) GMPE for application to the
    weighted mean case
    """
    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Adapts the original `get_poes()` from the :class:
        openquake.hazardlib.gsim.base.GMPE to call a function that take the
        weighted sum of the PoEs from the epistemic uncertainty adjustment
        """
        return get_weighted_poes(self, sctx, rctx, dctx, imt, imls,
                                 truncation_level)


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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
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
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        # Return mean, increased by the adjustment factor,
        # and standard devation
        return mean - nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup),\
            stddevs


class Idriss2014NSHMPMean(Idriss2014):
    """
    Implements the Idriss (2014) GMPE for application to the
    weighted mean case
    """
    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Adapts the original `get_poes()` from the :class:
        openquake.hazardlib.gsim.base.GMPE to call a function that take the
        weighted sum of the PoEs from the epistemic uncertainty adjustment
        """
        return get_weighted_poes(self, sctx, rctx, dctx, imt, imls,
                                 truncation_level)
