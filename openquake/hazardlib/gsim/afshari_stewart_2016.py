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
Module exports :class:`AfshariStewart2016`,
               :class:`AfshariStewart2016Japan`
"""
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD595, RSD575, RSD2080

CONSTANTS = {"mstar": 6.0,
             "r1": 10.0,
             "r2": 50.0,
             "v1": 600.0,
             "dz1ref": 200.0}

_get_lnmu_z1 = CallableDict()


@_get_lnmu_z1.add("CAL")
def _get_lnmu_z1_1(region, vs30):
    """
    Returns the z1.0 normalisation term for California (equation 11)
    """
    return (-7.15 / 4.) * np.log(
        (vs30 ** 4. + 570.94 ** 4) / (1360.0 ** 4. + 570.94 ** 4.)) -\
        np.log(1000.0)


@_get_lnmu_z1.add("JPN")
def _get_lnmu_z1_2(region, vs30):
    """
    Returns the z1.0 normalisation term for Japan (equation 12)
    """
    return (-5.23 / 2.) * np.log(
        (vs30 ** 2. + 412.39 ** 2) / (1360.0 ** 2. + 412.39 ** 2.)) -\
        np.log(1000.0)


def _get_phi(C, mag):
    """
    Returns the magnitude dependent intra-event standard deviation (phi)
    (equation 15)
    """
    phi = C["phi1"] + (C["phi2"] - C["phi1"]) * ((mag - 5.5) / 0.25)
    phi[mag < 5.5] = C["phi1"]
    phi[mag >= 5.75] = C["phi2"]
    return phi

def _get_sof_terms(C, rake):
    """
    Returns the style-of-faulting scaling parameters
    """
    # Strike-slip faulting
    b0 = np.full_like(rake, C["b0SS"])
    b1 = np.full_like(rake, C["b1SS"])
    # Reverse faulting
    rev = (rake >= 45.) & (rake <= 135.)
    b0[rev] = C["b0R"]
    b1[rev] = C["b1R"]
    # Normal faulting
    nor = (rake <= -45.) & (rake >= -135.)
    b0[nor] = C["b0N"]
    b1[nor] = C["b1N"]
    return b0, b1


def _get_tau(C, mag):
    """
    Returns magnitude dependent inter-event standard deviation (tau)
    (equation 14)
    """
    tau = C["tau1"] + (C["tau2"] - C["tau1"]) * ((mag - 6.5) / 0.5)
    tau[mag < 6.5] = C["tau1"]
    tau[mag >= 7.] = C["tau2"]
    return tau


def get_distance_term(C, rrup):
    """
    Returns the distance scaling term in equation 7
    """
    f_p = C["c1"] * rrup
    idx = np.logical_and(rrup > CONSTANTS["r1"],
                         rrup <= CONSTANTS["r2"])
    f_p[idx] = (C["c1"] * CONSTANTS["r1"]) +\
        C["c2"] * (rrup[idx] - CONSTANTS["r1"])
    idx = rrup > CONSTANTS["r2"]
    f_p[idx] = C["c1"] * CONSTANTS["r1"] +\
        C["c2"] * (CONSTANTS["r2"] - CONSTANTS["r1"]) +\
        C["c3"] * (rrup[idx] - CONSTANTS["r2"])
    return f_p


def get_magnitude_term(C, ctx):
    """
    Returns the magnitude scaling term in equation 3
    """
    b0, b1 = _get_sof_terms(C, ctx.rake)
    # Calculate moment (equation 5)
    m_0 = 10.0 ** (1.5 * ctx.mag + 16.05)
    # Get stress-drop scaling (equation 6)
    idx1 = ctx.mag > C["m2"]
    b1[idx1] += (C["b2"] * (C["m2"] - CONSTANTS["mstar"]) +
                 (C["b3"] * (ctx.mag[idx1] - C["m2"])))
    idx2 = ctx.mag <= C["m2"]
    b1[idx2] += C["b2"] * (ctx.mag[idx2] - CONSTANTS["mstar"])
    stress_drop = np.exp(b1)
    # Get corner frequency (equation 4)
    f0 = 4.9 * 1.0E6 * 3.2 * (stress_drop / m_0) ** (1. / 3.)
    term = 1. / f0
    term[ctx.mag <= C["m1"]] = b0[ctx.mag <= C["m1"]]
    return term


def _get_basin_term(C, ctx, region):
    """
    Return the basin term (equation 9)
    """
    dz1 = ctx.z1pt0 - np.exp(_get_lnmu_z1(region, ctx.vs30))
    fb = C['c5'] * dz1
    fb[dz1 > CONSTANTS["dz1ref"]] = (C["c5"] * CONSTANTS["dz1ref"])
    return fb


def get_site_amplification(region, C, ctx):
    """
    Returns the site amplification term
    """
    f_s = _get_basin_term(C, ctx, region) # First get basin term
    idx = ctx.vs30 > CONSTANTS["v1"]
    f_s[idx] += (C["c4"] * np.log(CONSTANTS["v1"] / C["vref"]))
    idx = np.logical_not(idx)
    f_s[idx] += (C["c4"] * np.log(ctx.vs30[idx] / C["vref"]))
    return f_s


def get_stddevs(C, mag):
    """
    Returns the standard deviations
    """
    tau = _get_tau(C, mag)
    phi = _get_phi(C, mag)
    return [np.sqrt(tau ** 2. + phi ** 2.), tau, phi]


class AfshariStewart2016(GMPE):
    """
    Implements the GMPE of Afshari & Stewart (2016) for relative significant
    duration for 5 - 75 %, 5 - 95 % and 20 - 80 % Arias Intensity.

    Afshari, K. and Stewart, J. P. (2016) "Physically Parameterized Prediction
    Equations for Signficant Duration in Active Crustal Regions", Earthquake
    Spectra, 32(4), 2057 - 2081
    """
    region = "CAL"

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {RSD595, RSD575, RSD2080}

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters are magnitude and rake
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (np.log(get_magnitude_term(C, ctx) +
                              get_distance_term(C, ctx.rrup)) +
                       get_site_amplification(self.region, C, ctx))
            sig[m], tau[m], phi[m] = get_stddevs(C, ctx.mag)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt        m1     m2    b0N     b0R    b0SS     b0U    b1N    b1R   b1SS    b1U      b2      b3      c1      c2      c3       c4      c5   vref  tau1  tau2  phi1  phi2
    rsd575   5.35   7.15  1.555  0.7806  1.2790   1.280  4.992  7.061  5.578  5.576  0.9011  -1.684  0.1159  0.1065  0.0682  -0.2246  0.0006  368.2  0.28  0.25  0.54  0.41
    rsd595    5.2   7.40  2.541  1.6120  2.3020   2.182  3.170  4.536  3.467  3.628  0.9443  -3.911  0.3165  0.2539  0.0932  -0.3183  0.0006  369.9  0.25  0.19  0.43  0.35
    rsd2080   5.2   7.40  1.409  0.7729  0.8804  0.8822  4.778  6.579  6.188  6.182  0.7414  -3.164  0.0646  0.0865  0.0373  -0.4237  0.0005  369.6  0.30  0.19  0.56  0.45
    """)


class AfshariStewart2016Japan(AfshariStewart2016):
    """
    Adaption of the Afshari & Stewart (2016) GMPE for relative significant
    duration for the case when the Japan basin model is preferred
    """
    region = "JPN"
