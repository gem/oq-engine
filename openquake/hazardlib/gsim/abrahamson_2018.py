# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
Module exports :class:`AbrahamsonEtAl2018SInter`
               :class:`AbrahamsonEtAl2018SInterHigh`
               :class:`AbrahamsonEtAl2018SInterLow`
               :class:`AbrahamsonEtAl2018SSlab`
               :class:`AbrahamsonEtAl2018SSlabHigh`
               :class:`AbrahamsonEtAl2018SSlabLow`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

CONSTANTS = {"n": 1.18,
             "c": 1.88,
             "C4": 10.0,
             "a3": 0.10,
             "a5": 0.0,
             "a9": 0.4,
             "a10": 1.73,
             "C1slab": 7.2,
             "phiamp": 0.3}


def _compute_pga_rock(slab, C_PGA, ctx):
    """
    Returns the PGA on rock (vs30 = 1000 m / s)
    """
    lpga1000 = (compute_base_term(slab, C_PGA) +
                compute_magnitude_term(slab, C_PGA, ctx.mag) +
                compute_depth_term(slab, C_PGA, ctx) +
                compute_distance_term(slab, C_PGA, ctx.rrup, ctx.mag))
    # Get linear site term for the case where vs30 = 1000.0
    flin = _get_linear_site_term(
        C_PGA, 1000.0 * np.ones_like(ctx.rrup))
    return lpga1000 + flin


def compute_base_term(slab, C):
    """
    Returns the base coefficient of the GMPE, which for interface events
    is just the coefficient a1 (adjusted regionally)
    """
    if slab:
        return C["a1"] + C["a4"] * (CONSTANTS["C1slab"] - C["C1inter"]) + \
            CONSTANTS["a10"]
    return C["a1"]


def compute_magnitude_term(slab, C, mag):
    """
    Returns the magnitude scaling term
    """
    if slab:
        # Returns the magnitude scaling term, this time using the constant
        # "C1slab" as the hinge magnitude
        f_mag = C["a13"] * ((10.0 - mag) ** 2.)
        return np.where(mag <= CONSTANTS["C1slab"],
                        C["a4"] * (mag - CONSTANTS["C1slab"]) + f_mag,
                        # parameter "a5" is zero, so linear term disappears
                        f_mag)
    f_mag = C["a13"] * (10.0 - mag) ** 2.
    return np.where(mag <= C["C1inter"],
                    C["a4"] * (mag - C["C1inter"]) + f_mag,
                    # C["a5"] is zero so linear term disappears
                    f_mag)


def compute_distance_term(slab, C, rrup, mag):
    """
    Returns the distance attenuation
    """
    scale = _get_magnitude_scale(slab, C, mag)
    fdist = scale * np.log(rrup + CONSTANTS["C4"] *
                           np.exp(CONSTANTS["a9"] * (mag - 6.0)))
    return fdist + C["a6"] * rrup


def _get_magnitude_scale(slab, C, mag):
    """
    Returns the magnitude scaling term that modifies the distance
    attenuation
    """
    if slab:
        return C["a2"] + C["a14"] + CONSTANTS["a3"] * (mag - 7.8)
    return C["a2"] + CONSTANTS["a3"] * (mag - 7.8)


def compute_depth_term(slab, C, ctx):
    """
    No top of rupture depth term for interface events
    """
    if slab:  # Equation on P11
        return np.where(ctx.ztor <= 100.0,
                        C["a11"] * (ctx.ztor - 60.0),
                        C["a11"] * (100.0 - 60.0))
    return 0.0


def compute_site_term(C, vs30, pga1000):
    """
    Returns the site amplification
    """
    vsstar = np.copy(vs30)
    vsstar[vs30 >= 1000.0] = 1000.0
    f_site = np.zeros_like(vs30)
    # Consider the cases of only linear amplification
    idx = vs30 >= C["vlin"]
    if np.any(idx):
        f_site[idx] = _get_linear_site_term(C, vsstar[idx])
    # Consider now only the nonlinear amplification cases
    idx = np.logical_not(idx)
    if np.any(idx):
        # Linear term
        flin = C["a12"] * np.log(vsstar[idx] / C["vlin"])
        # Nonlinear term
        fnl = (-C["b"] * np.log(pga1000[idx] + CONSTANTS["c"])) +\
            (C["b"] * np.log(pga1000[idx] + CONSTANTS["c"] *
             ((vsstar[idx] / C["vlin"]) ** CONSTANTS["n"])))
        f_site[idx] = flin + fnl
    return f_site


def _get_linear_site_term(C, vsstar):
    """
    As the linear site scaling is used for both the pga1000 case and the
    general case the relevant common part is returned here
    """
    return (C["a12"] + C["b"] * CONSTANTS["n"]) *\
        np.log(vsstar / C["vlin"])


def get_stddevs(C, C_PGA, pga1000, vs30):
    """
    Returns the standard deviations
    """
    dln = _get_dln_amp(C, pga1000, vs30)
    tau = get_inter_event_stddev(C, C_PGA, dln)
    phi = get_within_event_stddev(C, C_PGA, dln)
    return [np.sqrt(tau ** 2 + phi ** 2), tau, phi]


def _get_dln_amp(C, pga1000, vs30):
    """
    Returns the partial deriviative of the amplification term with respect
    to pga1000
    """
    dln = np.zeros(vs30.shape)
    idx = vs30 < C["vlin"]
    if np.any(idx):
        dln[idx] = C["b"] * pga1000[idx] * (
            (-1. / (pga1000[idx] + CONSTANTS["c"])) +
            (1. / (pga1000[idx] + CONSTANTS["c"] *
                   ((vs30[idx] / C["vlin"]) ** CONSTANTS["n"]))))
    return dln


def get_within_event_stddev(C, C_PGA, dln):
    """
    Returns the within-event aleatory uncertainty, phi
    """
    phi_amp2 = CONSTANTS["phiamp"] ** 2.
    phi_b = np.sqrt(C["phi0"] ** 2. - phi_amp2)
    phi_b_pga = np.sqrt((C_PGA["phi0"] ** 2.) - phi_amp2)

    phi = (C["phi0"] ** 2.) +\
          ((dln ** 2.) * (phi_b ** 2.)) +\
          (2.0 * dln * phi_b * phi_b_pga * C["rho_w"])
    return np.sqrt(phi)


def get_inter_event_stddev(C, C_PGA, dln):
    """
    Returns the between event aleatory uncertainty, tau
    """
    tau = (C["tau0"] ** 2.) +\
          ((dln ** 2.) * (C["tau0"] ** 2.)) +\
          (2.0 * dln * C["tau0"] * C_PGA["tau0"] * C["rho_b"])
    return np.sqrt(tau)


class AbrahamsonEtAl2018SInter(GMPE):
    """
    Implements the 2018 updated Abrahamson et al. (2018) "BC Hydro" GMPE for
    application to subduction earthquakes, for the case of subduction interface
    events.

    Abrahamson, N. A., Keuhn, N., Gulerce, Z., Gregor, N., Bozognia, Y.,
    Parker, G., Stewart, J., Chiou, B., Idriss, I. M., Campbell, K. and
    Youngs, R. (2018) "Update of the BC Hydro Subduction Ground-Motion Model
    using the NGA-Subduction Dataset", Pacific Earthquake Engineering
    Research Center (PEER) Technical Report, PEER 2018/02

    Whilst the original model provides coefficients for different regional
    variations, these are incomplete for the purpose of a working
    implementation. As the authors indicate in the source, the coefficients
    and adjustment factors are intended only for application to the
    Cascadia region; hence this is the only version implemented here.
    Furthermore, scalar adjustments are intended to be applied in order to
    define an "upper", "central" and "lower" branch to cover the epistemic
    uncertainty of the core model.
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Site amplification is dependent only upon Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup'}

    #: A "low" and "high" epistemic adjustment factor will be applied to
    #: subclasses of this model
    EPISTEMIC_ADJUSTMENT = None

    #: Adjustment variable to match Cascadia to global average
    CASCADIA_ADJUSTMENT = "adj_int"

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        C_PGA = self.COEFFS[PGA()]
        slab = self.CASCADIA_ADJUSTMENT == "adj_slab"
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # compute median pga on rock (vs30=1000), needed for site response
            # term calculation
            pga1000 = np.exp(_compute_pga_rock(slab, C_PGA, ctx) +
                             C_PGA[self.CASCADIA_ADJUSTMENT])
            # Get full model
            mean[m] = (compute_base_term(slab, C) +
                       compute_magnitude_term(slab, C, ctx.mag) +
                       compute_depth_term(slab, C, ctx) +
                       compute_distance_term(slab, C, ctx.rrup, ctx.mag) +
                       compute_site_term(C, ctx.vs30, pga1000))

            sig[m], tau[m], phi[m] = get_stddevs(C, C_PGA, pga1000, ctx.vs30)
            if self.EPISTEMIC_ADJUSTMENT:
                mean[m] += (C[self.CASCADIA_ADJUSTMENT] +
                            C[self.EPISTEMIC_ADJUSTMENT])
            else:
                mean[m] += C[self.CASCADIA_ADJUSTMENT]

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt    C1inter     vlin        b       a1      a2     a4        a6     a11     a12      a13     a14            adj_int           adj_slab   phi0   tau0   rho_w   rho_b  SINTER_LOW  SINTER_HIGH  SSLAB_LOW  SSLAB_HIGH
    pga       8.20    865.1   -1.186  2.34047  -1.044   0.59  -0.00705  0.0170   0.818  -0.0135  -0.223   1.04398007004686   0.83429221602170   0.61  0.580  1.0000  1.0000        -0.3          0.3      -0.50        0.50
    0.010     8.20    865.1   -1.186  2.34047  -1.044   0.59  -0.00705  0.0170   0.818  -0.0135  -0.223   1.04398007004686   0.83429221602170   0.61  0.580  1.0000  1.0000        -0.3          0.3      -0.50        0.50
    0.020     8.20    865.1   -1.219  2.36005  -1.044   0.59  -0.00707  0.0170   0.857  -0.0135  -0.196   1.04603523427650   0.79173401239125   0.61  0.580  1.0000  1.0000        -0.3          0.3      -0.50        0.50
    0.030     8.20    907.8   -1.273  2.38396  -1.080   0.59  -0.00710  0.0170   0.921  -0.0135  -0.128   1.23377425709977   0.70576030699887   0.61  0.580  0.9910  0.9910        -0.3          0.3      -0.50        0.50
    0.050     8.20   1053.5   -1.346  2.44598  -1.110   0.59  -0.00725  0.0180   1.007  -0.0138  -0.130   1.34342293514146   0.97601032906970   0.61  0.580  0.9730  0.9730        -0.3          0.3      -0.50        0.50
    0.075     8.20   1085.7   -1.471  2.75111  -1.110   0.59  -0.00758  0.0180   1.225  -0.0142  -0.130   1.32123133203975   0.99202176921030   0.61  0.580  0.9520  0.9520        -0.3          0.3      -0.50        0.50
    0.100     8.20   1032.5   -1.624  3.01943  -1.110   0.59  -0.00788  0.0180   1.457  -0.0145  -0.130   1.32307413547709   0.99825322734373   0.61  0.580  0.9290  0.9290        -0.3          0.3      -0.50        0.50
    0.150     8.20    877.6   -1.931  3.34867  -1.084   0.59  -0.00820  0.0175   1.849  -0.0153  -0.156   1.20604738361364   0.91891214881125   0.61  0.560  0.8960  0.8960        -0.3          0.3      -0.50        0.50
    0.200     8.20    748.2   -2.188  3.28397  -1.027   0.62  -0.00835  0.0170   2.082  -0.0162  -0.172   1.14232895808973   0.87856284947151   0.61  0.540  0.8740  0.8740        -0.3          0.3      -0.50        0.50
    0.250     8.20    654.3   -2.381  3.21131  -0.983   0.64  -0.00835  0.0160   2.240  -0.0172  -0.184   1.04808298000789   0.81234114576059   0.61  0.520  0.8560  0.8560        -0.3          0.3      -0.46        0.46
    0.300     8.20    587.1   -2.518  3.14548  -0.947   0.66  -0.00828  0.0152   2.341  -0.0183  -0.194   0.94565364697989   0.74536286357934   0.61  0.505  0.8410  0.8410        -0.3          0.3      -0.42        0.42
    0.400     8.20    503.0   -2.657  2.99656  -0.890   0.68  -0.00797  0.0140   2.415  -0.0206  -0.210   0.79394049645376   0.62046390803996   0.61  0.480  0.8180  0.8180        -0.3          0.3      -0.38        0.38
    0.500     8.20    456.6   -2.669  2.83921  -0.845   0.68  -0.00770  0.0130   2.359  -0.0231  -0.223   0.66202915411124   0.54491903264494   0.61  0.460  0.7830  0.7830        -0.3          0.3      -0.34        0.34
    0.600     8.20    430.3   -2.599  2.65827  -0.809   0.68  -0.00740  0.0122   2.227  -0.0256  -0.233   0.53601960759514   0.45568525725929   0.61  0.450  0.7315  0.7315        -0.3          0.3      -0.30        0.30
    0.750     8.15    410.5   -2.401  2.34577  -0.760   0.68  -0.00698  0.0113   1.949  -0.0296  -0.245   0.35555118688641   0.32581112214331   0.61  0.450  0.6800  0.6800        -0.3          0.3      -0.30        0.30
    1.000     8.10    400.0   -1.955  1.85131  -0.698   0.68  -0.00645  0.0100   1.402  -0.0363  -0.261   0.24282500000000   0.22809166666667   0.61  0.450  0.6070  0.6070        -0.3          0.3      -0.30        0.30
    1.500     8.05    400.0   -1.025  1.21559  -0.612   0.68  -0.00570  0.0082   0.329  -0.0493  -0.285  -0.07680250000000  -0.01107333333333   0.61  0.450  0.5004  0.5040        -0.3          0.3      -0.30        0.30
    2.000     8.00    400.0   -0.299  0.64875  -0.550   0.68  -0.00510  0.0070  -0.487  -0.0610  -0.301  -0.20847000000000  -0.08503000000000   0.61  0.450  0.4301  0.4310        -0.3          0.3      -0.30        0.30
    2.500     7.95    400.0    0.000  0.08221  -0.501   0.68  -0.00465  0.0060  -0.770  -0.0711  -0.313  -0.20955750000000  -0.05003166666667   0.61  0.450  0.3795  0.3795        -0.3          0.3      -0.30        0.30
    3.000     7.90    400.0    0.000 -0.36926  -0.460   0.68  -0.00430  0.0052  -0.700  -0.0798  -0.323  -0.21660250000000  -0.01508333333333   0.61  0.450  0.3280  0.3280        -0.3          0.3      -0.30        0.30
    4.000     7.85    400.0    0.000 -1.03439  -0.455   0.68  -0.00390  0.0040  -0.607  -0.0935  -0.282  -0.06406000000000   0.06239166666667   0.61  0.450  0.2505  0.2550        -0.3          0.3      -0.30        0.30
    5.000     7.80    400.0    0.000 -1.51967  -0.450   0.73  -0.00370  0.0030  -0.540  -0.0980  -0.250   0.06459750000000   0.06338666666667   0.61  0.450  0.2000  0.2000        -0.3          0.3      -0.30        0.30
    6.000     7.80    400.0    0.000 -1.81025  -0.450   0.78  -0.00357  0.0022  -0.479  -0.0980  -0.250   0.09014000000000   0.09661000000000   0.61  0.450  0.2000  0.2000        -0.3          0.3      -0.30        0.30
    7.500     7.80    400.0    0.000 -2.17269  -0.450   0.84  -0.00340  0.0013  -0.393  -0.0980  -0.250   0.13793250000000   0.12577500000000   0.61  0.450  0.2000  0.2000        -0.3          0.3      -0.30        0.30
    10.00     7.80    400.0    0.000 -2.71182  -0.450   0.93  -0.00327  0.0000  -0.350  -0.0980  -0.250   0.31434000000000   0.23962833333333   0.61  0.450  0.2000  0.2000        -0.3          0.3      -0.30        0.30
    """)


class AbrahamsonEtAl2018SInterHigh(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al (2018) subduction interface GMPE with the positive
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SINTER_HIGH"


class AbrahamsonEtAl2018SInterLow(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al (2018) subduction interface GMPE with the negative
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SINTER_LOW"


class AbrahamsonEtAl2018SSlab(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al. (2018) updated "BC Hydro" subduction GMPE for application
    to subduction in-slab earthquakes.
    """
    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Required rupture parameters for the in-slab model are magnitude and top
    # of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    #: Cascadia adjustment factor
    CASCADIA_ADJUSTMENT = "adj_slab"


class AbrahamsonEtAl2018SSlabHigh(AbrahamsonEtAl2018SSlab):
    """
    Abrahamson et al (2018) subduction in-slab GMPE with the positive
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SSLAB_HIGH"


class AbrahamsonEtAl2018SSlabLow(AbrahamsonEtAl2018SSlab):
    """
    Abrahamson et al (2018) subduction in-slab GMPE with the negative
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SSLAB_LOW"
