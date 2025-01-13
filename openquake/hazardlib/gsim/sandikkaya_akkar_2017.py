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
Module exports :class:`SandikkayaAkkar2017Rjb`
Module exports :class:`SandikkayaAkkar2017Repi`
Module exports :class:`SandikkayaAkkar2017Rhyp`
"""
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import CAV, IA


compute_logarithmic_distance_term = CallableDict()


@compute_logarithmic_distance_term.add("rjb")
def compute_logarithmic_distance_term_1(kind, C, ctx):
    """uses rjb for distance part"""
    return (C["a4"] + C["a5"] * (ctx.mag - 6.75)) * np.log(
        np.sqrt(ctx.rjb**2 + C["a6"] ** 2)
    )


@compute_logarithmic_distance_term.add("repi")
def compute_logarithmic_distance_term_2(kind, C, ctx):
    """uses repi for distance part"""
    return (C["a4"] + C["a5"] * (ctx.mag - 6.75)) * np.log(
        np.sqrt(ctx.repi**2 + C["a6"] ** 2)
    )


@compute_logarithmic_distance_term.add("rhypo")
def compute_logarithmic_distance_term_3(kind, C, ctx):
    """uses rhypo for distance part"""
    return (C["a4"] + C["a5"] * (ctx.mag - 6.75)) * np.log(
        np.sqrt(ctx.rhypo**2 + C["a6"] ** 2)
    )


def get_mean_values(kind, C, ctx):
    """
    Returns the mean values for a specific IMT from page 1887 of Sandikkaya and Akkar (2017) 
    """
    FNM = np.zeros_like(ctx.rake)
    FNM[np.absolute(ctx.rake + 90) < 45] = 1
    FRV = np.zeros_like(ctx.rake)
    FRV[np.absolute(ctx.rake - 90) < 45] = 1
    return (
        C["a1"]
        + C["a2"] * (ctx.mag - 6.75)
        + C["a3"] * (8.5 - ctx.mag) ** 2
        + compute_logarithmic_distance_term(kind, C, ctx)
        + C["a7"] * FNM
        + C["a8"] * FRV
        + C["a9"] * np.log(np.minimum(ctx.vs30, 1000) / 750)
    )


class SandikkayaAkkar2017Rjb(GMPE):
    """
    Implements ESM GMPE using rjb distances developed by M. Abdullah Sandikkaya
    and Sinan Akkar, published as "Cumulative Absolute Velocity, Arias
    Intensity and significant duration predictive models from a pan-European
    strong-motion dataset" (2017, Bulletin of Earthquake Engineering,
    Volume 15, pages 1881 - 1898).
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV, IA}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    #: Required site parameters are Vs30, Vs30 type (measured or inferred),
    REQUIRES_SITES_PARAMETERS = {"vs30"}

    #: Required rupture parameters are
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "rake"}

    #: Required distance measures are
    REQUIRES_DISTANCES = {"rjb"}
    kind = "rjb"

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        # Get mean and standard deviation
        for m, imt in enumerate(imts):
            conv_fact = 0
            conv_fact2 = 0
            ofact = 100
            gfact = 9.81
            if imt.string == "CAV":
                # convert from cm/s to m/s
                conv_fact = np.log(1 / ofact)
                # convert from m/s to g-s
                conv_fact2 = np.log(1 / gfact)

            C = self.COEFFS[imt]
            # Get mean and standard deviations for IMT
            mean[m] = get_mean_values(self.kind, C, ctx) + conv_fact \
                + conv_fact2
            sig[m] = np.sqrt(C["tau"] ** 2 + C["phi"] ** 2)
            tau[m] = C["tau"]
            phi[m] = C["phi"]

    COEFFS = CoeffsTable(
        table="""\
    IMT          a1         a2         a3         a4        a5  a6         a7         a8         a9      phi      tau    sigma
    cav     8.74378    0.75160   -0.03713   -0.88554   0.10417   9   0.027380   -0.16629   -0.64440   0.5538   0.3033   0.6314
     ia     4.85280    0.39645   -0.10684   -2.04165   0.39202   9   -0.01572   -0.09282   -1.02908   1.1229   0.6339   1.2895
    """,
    )


class SandikkayaAkkar2017Repi(SandikkayaAkkar2017Rjb):
    """
    for repi distance of Table 2
    """
    REQUIRES_DISTANCES = {"repi"}
    kind = "repi"
    COEFFS = CoeffsTable(
        table="""\
    IMT          a1         a2         a3         a4        a5  a6         a7         a8         a9      phi      tau    sigma
    cav     9.01362    0.75160   -0.03713   -0.93573   0.10417   9    0.02738   -0.16629   -0.64440   0.5584   0.3027   0.6352
     ia     5.48044    0.39645   -0.10684   -2.15658   0.39202   9   -0.01572   -0.09282   -1.02908   1.1405   0.6407   1.3081
    """,
    )


class SandikkayaAkkar2017Rhyp(SandikkayaAkkar2017Rjb):
    """
    for rhypo distance of Table 2
    """
    REQUIRES_DISTANCES = {"rhypo"}
    kind = "rhypo"
    COEFFS = CoeffsTable(
        table="""\
    IMT          a1         a2         a3         a4        a5  a6         a7         a8         a9      phi      tau    sigma 
    cav     9.44255     0.7516   -0.03713    -1.0271   0.10417   9    0.02738   -0.16629    -0.6444   0.5618   0.2946   0.6344
     ia     6.57230    0.39645   -0.10684   -2.38955   0.39202   9   -0.01572   -0.09282   -1.02908   1.1486   0.6058   1.2986
    """,
    )
