# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`BozorgniaCampbell2016VH`
               :class:`BozorgniaCampbell2016HighQVH`
               :class:`BozorgniaCampbell2016LowQVH`
               :class:`BozorgniaCampbell2016AveQJapanSiteVH`
               :class:`BozorgniaCampbell2016HighQJapanSiteVH`
               :class:`BozorgniaCampbell2016LowQJapanSiteVH`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const, contexts
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim import bozorgnia_campbell_2016
from openquake.hazardlib.gsim import campbell_bozorgnia_2014


def _get_tau_vh(C, mag, tau_v, tau_h):
    """
    Returns the inter-event random effects coefficient (tau) defined in
    Equation 10.
    """
    rhob1 = C['rhob1']
    rhob2 = C['rhob2']
    rhob = rhob2 + (rhob1 - rhob2)*(5.5 - mag)
    rhob[mag <= 4.5] = rhob1
    rhob[mag >= 5.5] = rhob2
    return np.sqrt(tau_v ** 2 + tau_h ** 2 - 2 * rhob * tau_v * tau_h)


def _get_phi_vh(C, mag, phi_v, phi_h):
    """
    Returns the intra-event random effects coefficient (phi) defined in
    Equation 11.
    """
    rhow1 = C['rhow1']
    rhow2 = C['rhow2']
    rhow = rhow2 + (rhow1 - rhow2) * (5.5 - mag)
    rhow[mag <= 4.5] = rhow1
    rhow[mag >= 5.5] = rhow2
    return np.sqrt(phi_v ** 2 + phi_h ** 2 - 2 * rhow * phi_v * phi_h)


class BozorgniaCampbell2016VH(GMPE):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    This V/H model is combined from VGMPE by Bozorgnia and Campbell (2016) as
    the vertical model, and HGMPE by Campbell and Bozorgnia (2014) as the
    horizontal model.

    **Reference:**

    Bozorgnia, Y. & Campbell, K. (2016). Ground Motion Model for the
    Vertical-to-Horizontal (V/H) Ratios of PGA, PGV, and Response Spectra
    *Earthquake Spectra*, 32(2), 951-978.

    Implements the global model that uses datasets from California, Taiwan,
    the Middle East, and other similar active tectonic regions to represent
    a typical or average Q region.

    Applies the average attenuation case (Dc20=0)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016()
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014()

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the
    #: :attr:`~openquake.hazardlib.const.IMC.VERTICAL_TO_HORIZONTAL_RATIO`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = (
        const.IMC.VERTICAL_TO_HORIZONTAL_RATIO)

    #: Supported standard deviation types are inter-event, intra-event
    #: and total; see the section for "Aleatory Variability Model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are taken from the V and H models
    REQUIRES_SITES_PARAMETERS = (
        VGMPE.REQUIRES_SITES_PARAMETERS |
        HGMPE.REQUIRES_SITES_PARAMETERS)

    #: Required rupture parameters are taken from the V and H models
    REQUIRES_RUPTURE_PARAMETERS = (
        VGMPE.REQUIRES_RUPTURE_PARAMETERS |
        HGMPE.REQUIRES_RUPTURE_PARAMETERS)

    #: Required distance measures are taken from the V and H models
    REQUIRES_DISTANCES = (
        VGMPE.REQUIRES_DISTANCES |
        HGMPE.REQUIRES_DISTANCES)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        mean_, _sig, tau_, phi_ = contexts.get_mean_stds(
            [self.VGMPE, self.HGMPE], ctx, imts)
        for m, imt in enumerate(imts):
            # V/H model, Equation 1 and 12 (in natural log units)
            mean[m] = mean_[0, m] - mean_[1, m]

            # Get standard deviations
            C = self.COEFFS[imt]
            t = _get_tau_vh(C, ctx.mag, tau_[0, m], tau_[1, m])
            p = _get_phi_vh(C, ctx.mag, phi_[0, m], phi_[1, m])
            sig[m] = np.sqrt(t ** 2 + p ** 2)
            tau[m] = t
            phi[m] = p

    #: Table of regression coefficients obtained from supplementary material
    #: published together with the EQS paper
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     rhow1    rhow2    rhob1    rhob2
    0.010   0.783    0.718    0.916    0.893
    0.020   0.785    0.718    0.917    0.891
    0.030   0.784    0.703    0.919    0.884
    0.050   0.782    0.678    0.931    0.877
    0.075   0.781    0.681    0.933    0.909
    0.100   0.778    0.657    0.944    0.900
    0.150   0.775    0.653    0.946    0.875
    0.200   0.774    0.630    0.946    0.826
    0.250   0.770    0.642    0.945    0.784
    0.300   0.757    0.658    0.949    0.819
    0.400   0.750    0.661    0.953    0.719
    0.500   0.742    0.666    0.955    0.716
    0.750   0.730    0.688    0.965    0.718
    1.000   0.721    0.684    0.967    0.765
    1.500   0.707    0.663    0.967    0.796
    2.000   0.691    0.664    0.966    0.799
    3.000   0.652    0.629    0.956    0.822
    4.000   0.669    0.613    0.945    0.839
    5.000   0.665    0.586    0.921    0.860
    7.500   0.586    0.573    0.898    0.685
    10.00   0.639    0.547    0.854    0.720
    PGA     0.782    0.720    0.915    0.893
    PGV     0.754    0.680    0.882    0.699
    """)


class BozorgniaCampbell2016HighQVH(BozorgniaCampbell2016VH):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    Applies regional corrections in path scaling term for regions with
    low attenuation (high quality factor, Q) (e.g. eastern China)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016(sgn=+1)
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014(
        coeffs=campbell_bozorgnia_2014.coeffs_high)


class BozorgniaCampbell2016LowQVH(BozorgniaCampbell2016VH):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    Applies regional corrections in path scaling term for regions with
    high attenuation (low quality factor, Q) (e.g. Japan and Italy)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016(sgn=-1)
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014(
        coeffs=campbell_bozorgnia_2014.coeffs_low)


class BozorgniaCampbell2016AveQJapanSiteVH(BozorgniaCampbell2016VH):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies the average attenuation case (Dc20=0)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016(SJ=1)
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014(SJ=1)


class BozorgniaCampbell2016HighQJapanSiteVH(
        BozorgniaCampbell2016AveQJapanSiteVH):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies regional corrections in path scaling term for regions with
    low attenuation (high quality factor, Q)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016(SJ=1, sgn=+1)
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014(
        coeffs=campbell_bozorgnia_2014.coeffs_high, SJ=1)


class BozorgniaCampbell2016LowQJapanSiteVH(
        BozorgniaCampbell2016AveQJapanSiteVH):
    """
    Implements the GMPE by Bozorgnia & Campbell (2016) vertical-to-horizontal
    ratio for ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies regional corrections in path scaling term for regions with
    high attenuation (low quality factor, Q)
    """
    VGMPE = bozorgnia_campbell_2016.BozorgniaCampbell2016(SJ=1, sgn=-1)
    HGMPE = campbell_bozorgnia_2014.CampbellBozorgnia2014(
        coeffs=campbell_bozorgnia_2014.coeffs_low, SJ=1)
