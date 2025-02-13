# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`Campbell1997`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


def get_fault_term(rake):
    """
    Returns coefficient for faulting style (pg 156)
    """
    rake = np.where(rake < 0, rake + 360, rake)
    f = np.zeros_like(rake)
    f[(rake >= 45) & (rake <= 135)] = 1.
    f[(rake >= 225) & (rake <= 315)] = .5
    return f


def get_Ssr_term(vs30):
    """
    Returns site term for soft rock (pg 157)
    """
    return (vs30 >= 760) & (vs30 < 1500)


def get_Shr_term(vs30):
    """
    Returns site term for hard rock (pg 157)
    """
    return vs30 >= 1500


class Campbell1997(GMPE):
    """
    Implements GMPE (PGA) by Campbell, Kenneth W. "Empirical near-source
    attenuation relationships for horizontal and vertical components of peak
    ground acceleration, peak ground velocity, and pseudo-absolute acceleration
    response spectra." Seismological research letters 68.1 (1997): 154-179.
    """
    #: Supported TRT active...we specify active_shallow_crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA, PGV, PSA, but we only define
    #: PGA because this is the only IMT used by an implemented model (09/18)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA}

    #: Supported intensity measure component is the horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see equation 4, pg 164
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture. In the
    #: publication, Rseis is used. We assume Rrup=Rseis, justified by
    #: our calculations matching the verification tables
    REQUIRES_DISTANCES = {'rrup'}

    #: Verification of the mean value was done by digitizing Figs. 9 and 10
    #: using Engauge Digitizer. The tests check varied magnitude, distance,
    #: vs30, and faulting type. Maximum error was ~1.3%. OpenQuake trellis
    #: plots match these figures. Also tested against a matlab implementation
    #: (web.stanford.edu/~bakerjw/GMPEs/C_1997_horiz.m), which also has no
    #: verification tables.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        R = ctx.rrup
        M = ctx.mag
        # get constants
        Ssr = get_Ssr_term(ctx.vs30)
        Shr = get_Shr_term(ctx.vs30)
        rake = ctx.rake
        F = get_fault_term(rake)

        # compute mean
        mean[:] = -3.512 + (0.904 * M) - (
            1.328 * np.log(np.sqrt(R**2 + (0.149 * np.exp(0.647 * M))**2))) \
            + (1.125 - 0.112 * np.log(R) - 0.0957 * M) * F \
            + (0.440 - 0.171 * np.log(R)) * Ssr \
            + (0.405 - 0.222 * np.log(R)) * Shr
        # standard deviations from mean (pg 164; more robust than
        # estimate using magnitude
        mean = np.exp(mean)
        sig[:] = 0.39
        sig[mean < 0.068] = 0.55
        idx = np.logical_and(mean >= 0.068, mean <= 0.21)
        sig[idx] = 0.173 - 0.140 * np.log(mean[idx])
