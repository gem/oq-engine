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
Implements SERA site amplification models
class:`PitilakisEtAl2018`, `PitilakisEtAl2020`, `Eurocode8Amplification`,
`Eurocode8AmplificationDefault`,`SandikkayaDinsever2018`
"""
import numpy as np
import copy
from scipy.constants import g

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, registry
from openquake.hazardlib.imt import PGA, SA, from_string
from openquake.hazardlib import const, contexts


# Pitilakis GMPE Wrapper
uppernames = '''
DEFINED_FOR_INTENSITY_MEASURE_TYPES
DEFINED_FOR_STANDARD_DEVIATION_TYPES
REQUIRES_SITES_PARAMETERS
REQUIRES_RUPTURE_PARAMETERS
REQUIRES_DISTANCES
'''.split()

CONSTANTS = {
    "F0": 2.5,
    "kappa": 5.0,
    "TA": 0.03}

IMLS = [0., 0.25, 0.5, 0.75, 1., 1.25]

MEAN, SIGMA, INTER, INTRA = 0, 1, 2, 3

get_amplification_factor = CallableDict()


@get_amplification_factor.add("base")
def get_amplification_factor_1(kind, F1, FS, s_s, s_1, sctx, ec8=None):
    """
    Returns the short and long-period amplification factors given the
    input Pitilakis et al. (2018) site class and the short and long-period
    input accelerations
    """
    f_s = np.ones(sctx.ec8_p18.shape, dtype=float)
    f_l = np.ones(sctx.ec8_p18.shape, dtype=float)
    for ec8b in np.unique(sctx.ec8_p18):
        ec8 = ec8b.decode('ascii')
        if ec8 == "A":
            # Amplification factors are 1
            continue
        idx = sctx.ec8_p18 == ec8b
        if np.any(idx):
            s_ss = s_s[idx]
            f_ss = np.ones(np.sum(idx))
            f_ls = np.ones(np.sum(idx))
            lb = s_ss < 0.25
            ub = s_ss > 1.25
            f_ss[lb] = FS[ec8][0]
            f_ls[lb] = F1[ec8][0]
            f_ss[ub] = FS[ec8][-1]
            f_ls[ub] = F1[ec8][-1]
            for j in range(1, len(IMLS) - 1):
                jdx = np.logical_and(s_ss >= IMLS[j], s_ss < IMLS[j + 1])
                if not np.any(jdx):
                    continue
                dfs = FS[ec8][j + 1] - FS[ec8][j]
                dfl = F1[ec8][j + 1] - F1[ec8][j]
                diml = IMLS[j + 1] - IMLS[j]
                f_ss[jdx] = FS[ec8][j] + (s_ss[jdx] - IMLS[j]) * (dfs / diml)
                f_ls[jdx] = F1[ec8][j] + (s_ss[jdx] - IMLS[j]) * (dfl / diml)
            f_s[idx] = f_ss
            f_l[idx] = f_ls
    return f_s, f_l


@get_amplification_factor.add("euro8")
def get_amplification_factor_2(kind, F1, FS, s_s_rp, s_1_rp, sctx, ec8):
    """
    Returns the amplification factors based on the proposed EC8 formulation
    in Table 3.4
    """
    r_alpha = 1.0 - 2.0E3 * (s_s_rp * g) / (sctx.vs30 ** 2)
    r_beta = 1.0 - 2.0E3 * (s_1_rp * g) / (sctx.vs30 ** 2)
    f_s = np.ones(sctx.vs30.shape)
    f_l = np.ones(sctx.vs30.shape)
    vsh_norm = sctx.vs30 / 800.
    for s_c in np.unique(ec8):
        if s_c == b"A":
            continue
        idx = ec8 == s_c
        if not np.any(idx):
            continue
        if s_c in (b"B", b"C", b"D"):
            f_s[idx] = vsh_norm[idx] ** (-0.25 * r_alpha[idx])
            f_l[idx] = vsh_norm[idx] ** (-0.7 * r_beta[idx])
        elif s_c == b"E":
            f_s[idx] = vsh_norm[idx] ** (-0.25 * r_alpha[idx] *
                                         (sctx.h800[idx] / 30.) *
                                         (4.0 - (sctx.h800[idx] / 10.)))
            f_l[idx] = vsh_norm[idx] ** (-0.7 * r_beta[idx] *
                                         (sctx.h800[idx] / 30.))
        elif s_c == b"F":
            f_s[idx] = 0.9 * (vsh_norm[idx] ** (-0.25 * r_alpha[idx]))
            f_l[idx] = 1.25 * (vsh_norm[idx] ** (-0.7 * r_beta[idx]))
        else:
            pass
    return f_s, f_l


@get_amplification_factor.add("euro8default")
def get_amplification_factor_3(kind, F1, FS, s_s_rp, s_1_rp, sctx, ec8=None):
    """
    Returns the default amplification factor dependent upon the site class
    """
    f_s = np.ones(sctx.ec8.shape)
    f_l = np.ones(sctx.ec8.shape)
    for key in EC8_FS_default:
        idx = sctx.ec8 == key
        f_s[idx] = EC8_FS_default[key]
        f_l[idx] = EC8_FL_default[key]
    return f_s, f_l


def get_amplified_mean(s_s, s_1, s_1_rp, imt):
    """
    Given the amplified short- and long-period input accelerations,
    returns the mean ground motion for the IMT according to the design
    spectrum construction in equations 1 - 5 of Pitilakis et al., (2018)
    """
    if "PGA" in str(imt) or imt.period <= CONSTANTS["TA"]:
        # PGA or v. short period acceleration
        return np.log(s_s / CONSTANTS["F0"])
    mean = np.copy(s_s)
    t_c = s_1 / s_s
    t_b = t_c / CONSTANTS["kappa"]
    t_b[t_b < 0.05] = 0.05
    t_b[t_b > 0.1] = 0.1
    t_d = 2.0 + np.zeros_like(s_1_rp)
    idx = s_1_rp > 0.1
    t_d[idx] = 1.0 + (10. * s_1_rp[idx])
    idx = np.logical_and(CONSTANTS["TA"] < imt.period,
                         t_b >= imt.period)
    mean[idx] = (s_s[idx] / (t_b[idx] - CONSTANTS["TA"])) *\
        ((imt.period - CONSTANTS["TA"]) +
         (t_b[idx] - imt.period) / CONSTANTS["F0"])
    idx = np.logical_and(t_c < imt.period, t_d >= imt.period)
    mean[idx] = s_1[idx] / imt.period
    idx = t_d < imt.period
    mean[idx] = t_d[idx] * s_1[idx] / (imt.period ** 2.)
    return np.log(mean)


def get_ec8_class(vsh, h800):
    """
    Method to return the vector of Eurocode 8 site classes based on
    Vs30 and h800
    """
    ec8 = np.array([b"A" for i in range(len(vsh))], dtype="|S1")
    idx = np.logical_and(vsh >= 400., h800 > 5.)
    ec8[idx] = b"B"
    idx1 = np.logical_and(vsh < 400., vsh >= 250.)
    idx = np.logical_and(idx1, np.logical_and(h800 > 5., h800 <= 30.))
    ec8[idx] = b"E"
    idx = np.logical_and(idx1, np.logical_and(h800 > 30., h800 <= 100.))
    ec8[idx] = b"C"
    idx = np.logical_and(idx1, h800 > 100.)
    ec8[idx] = b"F"
    idx1 = vsh < 250.
    idx = np.logical_and(idx1, h800 <= 30.)
    ec8[idx] = b"E"
    idx = np.logical_and(idx1, np.logical_and(h800 > 30., h800 <= 100.))
    ec8[idx] = b"D"
    idx = np.logical_and(idx1, h800 > 100.)
    ec8[idx] = b"F"
    return ec8


class PitilakisEtAl2018(GMPE):
    """
    Implements a site amplification model based on a design code approach,
    using the site characterisation and amplification coefficients proposed
    by Pitilakis et al. (2018)
    Pitilakis, K., Riga, E., Anastasiadis, A., Fotopoulou, S. and Karafagka, S.
    (2018) "Towards the revision of EC8: Proposal for an alternative site
    classification scheme and associated intensity dependent spectral
    amplification factors", Soil Dynamics & Earthquake Engineering,

    Care should be taken to note the following:

    1. In the absence of a specific guidance from Eurocode 8 as to how the
       short period coefficient SS is determine from the UHS the choice is
       made to anchor the short period spectrum to PGA, with SS taken as being
       equal to 2.5 * PGA. This is implied by the Eurocode 8 decision to
       fix F0 to 2.5 and that the ground motion is fixed to SS / F0 for T -> 0

    2. No uncertainty in amplification factor is presented in a code based
       approach and therefore the standard deviation of the original GMPE is
       retained.

    :param gmpe:
        Input ground motion prediction equation

    :param float rock_vs30:
        Reference shearwave velocity used for the rock calculation
    """
    kind = "base"

    #: Supported tectonic region type is undefined (applies to any)
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters are Vs30 and the Pitilakis et al (2018) site
    #: class (others will be added for the GMPE in question)
    REQUIRES_SITES_PARAMETERS = {'vs30', 'ec8_p18'}

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 800.0

    def __init__(self, gmpe_name, reference_velocity=None, **extra_args):
        if isinstance(gmpe_name, str):
            self.gsim = registry[gmpe_name](**extra_args)
        else:
            # An instantiated class is passed as an argument
            self.gsim = copy.deepcopy(gmpe_name)
        if reference_velocity:
            self.rock_vs30 = reference_velocity
        else:
            self.rock_vs30 = self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gsim, name)))

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations calling the input GMPE
        for the mean acceleration for PGA and Sa (1.0) on the reference rock,
        defining the amplification factors and code spectrum to return the
        mean ground motion at the desired period, before the calling the
        input GMPE once more in order to return the standard deviations for the
        required IMT.
        """
        # Get PGA and Sa (1.0) from GMPE
        ctx_r = copy.copy(ctx)
        ctx_r.vs30 = np.full_like(ctx_r.vs30, self.rock_vs30)
        rock = contexts.get_mean_stds(self.gsim, ctx_r, [PGA(),  SA(1.0)])
        pga_r = rock[0, 0]
        s_1_rp = rock[0, 1]
        s_s_rp = CONSTANTS["F0"] * np.exp(pga_r)
        s_1_rp = np.exp(s_1_rp)
        # Get the short and long period amplification factors
        if self.kind == 'euro8':
            ec8 = get_ec8_class(ctx.vs30, ctx.h800)
        else:
            ec8 = None
        f_s, f_l = get_amplification_factor(
            self.kind, self.F1, self.FS, s_s_rp, s_1_rp, ctx, ec8)
        s_1 = f_l * s_1_rp
        s_s = f_s * s_s_rp

        # NB: this is wasteful since means are computed and then discarded
        out = contexts.get_mean_stds(self.gsim, ctx_r, imts)
        for m, imt in enumerate(imts):
            # Get the mean ground motion using the design code spectrum
            mean[m] = get_amplified_mean(s_s, s_1, s_1_rp, imt)
            sig[m] = out[1, m]
            tau[m] = out[2, m]
            phi[m] = out[3, m]

    # Short period amplification factors defined by Pitilakis et al., (2018)
    FS = {
        "A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "B1": [1.3, 1.3, 1.2, 1.2, 1.2, 1.2],
        "B2": [1.4, 1.3, 1.3, 1.2, 1.1, 1.1],
        "C1": [1.7, 1.6, 1.4, 1.3, 1.3, 1.2],
        "C2": [1.6, 1.5, 1.3, 1.2, 1.1, 1.0],
        "C3": [1.8, 1.6, 1.4, 1.2, 1.1, 1.0],
        "D":  [2.2, 1.9, 1.6, 1.4, 1.2, 1.0],
        "E":  [1.7, 1.6, 1.6, 1.5, 1.5, 1.5]}

    # Long period amplification factors defined by Pitilakis et al., (2018)
    F1 = {
        "A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "B1": [1.4, 1.4, 1.4, 1.4, 1.3, 1.3],
        "B2": [1.6, 1.5, 1.5, 1.5, 1.4, 1.3],
        "C1": [1.7, 1.6, 1.5, 1.5, 1.4, 1.3],
        "C2": [2.1, 2.0, 1.9, 1.8, 1.8, 1.7],
        "C3": [3.2, 3.0, 2.7, 2.5, 2.4, 2.3],
        "D":  [4.1, 3.8, 3.3, 3.0, 2.8, 2.7],
        "E":  [1.3, 1.3, 1.2, 1.2, 1.2, 1.2]}


class PitilakisEtAl2020(PitilakisEtAl2018):
    """
    Adaptation of the Pitilakis et al. (2018) amplification model adopting
    the revised FS and F1 factors proposed by Pitilakis et al., (2020)

    Pitilakis, K., Riga, E. and Anastasiadis, A. (2020), Towards the Revision
    of EC8: Proposal for an Alternative Site Classification Scheme and
    Associated Intensity-Dependent Amplification Factors. In the Proceedings
    of the 17th World Conference on Earthquake Engineering, 17WCEE, Sendai,
    Japan, September 13th to 18th 2020. Paper No. C002895.
    """
    # Short period amplification factors defined by Pitilakis et al., (2020)
    FS = {
        "A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "B1": [1.3, 1.3, 1.3, 1.2, 1.2, 1.2],
        "B2": [1.3, 1.3, 1.2, 1.2, 1.2, 1.1],
        "C1": [1.7, 1.7, 1.6, 1.5, 1.5, 1.4],
        "C2": [1.6, 1.5, 1.3, 1.2, 1.1, 1.0],
        "C3": [1.7, 1.6, 1.4, 1.2, 1.2, 1.1],
        "D":  [1.8, 1.7, 1.5, 1.4, 1.3, 1.2],
        "E":  [1.7, 1.6, 1.6, 1.5, 1.5, 1.4]}

    # Long period amplification factors defined by Pitilakis et al., (2020)
    F1 = {
        "A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "B1": [1.1, 1.1, 1.1, 1.1, 1.1, 1.1],
        "B2": [1.4, 1.4, 1.3, 1.3, 1.3, 1.3],
        "C1": [1.5, 1.5, 1.4, 1.4, 1.4, 1.4],
        "C2": [2.3, 2.2, 2.0, 1.9, 1.9, 1.8],
        "C3": [2.4, 2.3, 2.1, 2.0, 2.0, 1.9],
        "D":  [4.0, 3.5, 3.0, 2.7, 2.4, 2.3],
        "E":  [1.2, 1.1, 1.1, 1.1, 1.1, 1.1]}


class Eurocode8Amplification(PitilakisEtAl2018):
    """
    Implements a general class to return a ground motion based on the
    Eurocode 8 design spectrum:
    CEN (2018): "Eurocode 8: Earthquake Resistant Design of Structures"
    Revised 2nd Draft SC8 PT1 - Rev 20

    The potential notes highlighted in :class:`PitilakisEtAl2018` apply
    in this case too.
    """
    kind = "euro8"

    #: Supported tectonic region type is undefined (applies to any)
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set((PGA, SA))

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameters will be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = {'vs30', 'h800'}

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 800.0

    def __init__(self, gmpe_name, reference_velocity=800.0, **kwargs):
        super().__init__(gmpe_name=gmpe_name, **kwargs)
        self.rock_vs30 = reference_velocity if reference_velocity else\
            self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gsim, name)))


# Default short period amplification factors defined by Eurocode 8 Table 3.4
EC8_FS_default = {
    b"A": 1., b"B": 1.2, b"C": 1.35, b"D": 1.5, b"E": 1.7, b"F": 1.35
}


# Default long period amplification factors defined by Eurocode 8 Table 3.4
EC8_FL_default = {
    b"A": 1., b"B": 1.6, b"C": 2.25, b"D": 3.20, b"E": 3.0, b"F": 4.0
}


class Eurocode8AmplificationDefault(Eurocode8Amplification):
    """
    In the case that Vs30 and h800 are not known but a Eurocode 8 site class
    is otherwise determined then a set of default amplification factors
    are applied. This model implements the Eurocode 8 design spectrum
    """
    kind = "euro8default"
    #: Required site parameters are the EC8 site class, everything else will
    #: be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = {'ec8'}


# Sandikkaya & Dinsever

REGION_SET = ["USNZ", "JP", "TW", "CH", "WA", "TRGR", "WMT", "NWE"]


def _get_basin_term(C, ctx, region=None):
    """
    Get basin amplification term
    """
    return C["b2"] * np.log(ctx.z1pt0)


def get_site_amplification(C, psarock, ctx, ck):
    """
    Returns the site amplification model define in equation (9)
    """
    vs30_s = np.copy(ctx.vs30)
    vs30_s[vs30_s > 1000.] = 1000.
    fn_lin = (C["b1"] + ck) * np.log(vs30_s / 760.)
    fn_z = _get_basin_term(C, ctx)
    fn_nl = C["b3"] * np.log((psarock + 0.1 * g) / (0.1 * g)) *\
        np.exp(-np.exp(2.0 * np.log(ctx.vs30) - 11.))
    return fn_lin + fn_z + fn_nl


def get_stddevs(phi_0, C, tau, phi, psa_rock, vs30, imt):
    """
    Returns the standard deviation adjusted for the site-response model
    """
    ysig = np.copy(psa_rock)
    ysig[ysig > 0.35] = 0.35
    ysig[ysig < 0.005] = 0.005
    vsig = np.copy(vs30)
    vsig[vsig > 600.0] = 600.0
    vsig[vsig < 150.] = 150.
    sigma_s = C["sigma_s"] * C["c0"] * (
        C["c1"] * np.log(ysig) + C["c2"] * np.log(vsig))
    if phi_0:
        phi0 = phi_0[imt]['value'] + np.zeros(vs30.shape)
    else:
        # In the case that no input phi0 is defined take 'approximate'
        # phi0 as 85 % of phi
        phi0 = 0.85 * phi
    phi = np.sqrt(phi0 ** 2. + sigma_s ** 2.)
    return [np.sqrt(tau ** 2 + phi ** 2), tau, phi]


class SandikkayaDinsever2018(GMPE):
    """
    Implements the nonlinear site amplification model of Sandikkaya &
    Dinsever (2018), see Sandikkaya, M. A. and Dinsever, L. D. (2018)
    "A Site Amplification Model for Crustal Earthquakes", Geosciences, 264(8),
    doi:10.3390/geosciences8070264

    Note that the nonlinear amplification model has its own standard deviation,
    which should be applied with the phi0 model of the original GMPE. This
    is not defined for all GMPEs in the literature, nor is the retrieval
    of it consistently applied in OpenQuake. Therefore we allow the user
    to define manually the input phi0 model, and if this is not possible a
    "default" phi0 is taken by reducing the original GMPE's phi by 15 %.

    The amplification model is compatible only with GMPEs with separate
    inter- and intra-event standard deviation, otherwise an error is raised.

    :param gmpe:
        Input GMPE for calculation on reference rock and standrd deviation
        at the period of interest on surface rock

    :param phi_0:
        Single-station within-event standard deviation (as a period-dependent
        dictionary or None)

    :param str region:
        Defines the region for the region-adjusted version of the model
    """
    experimental = True

    #: Supported tectonic region type is undefined
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters will be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 760.0

    def __init__(self, gmpe_name, reference_velocity=760., region=None,
                 phi_0=None, **kwargs):
        super().__init__(**kwargs)
        if isinstance(gmpe_name, str):
            self.gsim = registry[gmpe_name](**kwargs)
        else:
            # An instantiated class is passed as an argument
            self.gsim = copy.deepcopy(gmpe_name)
        # Define the reference velocity - set to 760. by default
        self.rock_vs30 = reference_velocity if reference_velocity else\
            self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gsim, name)))
        stddev_check = (const.StdDev.INTER_EVENT in
                        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES) and\
                       (const.StdDev.INTRA_EVENT in
                        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
        if not stddev_check:
            raise ValueError("Input GMPE %s not defined for inter- and intra-"
                             "event standard deviation" % str(self.gsim))

        if isinstance(phi_0, dict):
            # Input phi_0 model
            iphi_0 = {from_string(key): {'value': phi_0[key]} for key in phi_0}
            self.phi_0 = CoeffsTable.fromdict(iphi_0)
        else:
            # No input phi_0 model
            self.phi_0 = None
        # Regionalisation of the linear site term is possible
        # check if region is in the set of supported terms and
        # raise error otherwise
        if region is not None:
            if region in REGION_SET:
                self.region = "ck{:s}".format(region)
            else:
                raise ValueError("Region must be one of: %s"
                                 % " ".join(REGION_SET))
        else:
            self.region = region

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        ctx_r = copy.copy(ctx)
        ctx_r.vs30 = np.full_like(ctx_r.vs30, self.rock_vs30)
        rock = contexts.get_mean_stds(self.gsim, ctx_r, imts)
        for m, imt in enumerate(imts):
            psarock = np.exp(rock[MEAN][m])
            C = self.COEFFS_SITE[imt]
            if self.region:
                ck = self.COEFFS_REG[imt][self.region]
            else:
                ck = 0.0
            mean[m] = rock[MEAN][m] + get_site_amplification(
                C, psarock, ctx, ck)
            t = rock[INTER][m]
            p = rock[INTRA][m]
            sig[m], tau[m], phi[m] = get_stddevs(
                self.phi_0, C, t, p, psarock, ctx.vs30, imt)

    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    imt          b1        b3       b2  sigma_s       c0       c2        c1
    pga    -0.53307  -0.46412  0.02105  0.47096  1.24013  0.09542  -0.05865
    0.010  -0.53307  -0.46412  0.02105  0.47096  1.24013  0.09542  -0.05865
    0.025  -0.50842  -0.39040  0.02023  0.47508  1.24682  0.09906  -0.05951
    0.040  -0.45025  -0.31255  0.01858  0.48906  1.33552  0.12324  -0.06481
    0.050  -0.38023  -0.23187  0.02029  0.50412  1.67790  0.18762  -0.08741
    0.070  -0.35050  -0.18413  0.02376  0.50892  1.57403  0.12994  -0.07910
    0.100  -0.42752  -0.37652  0.03221  0.49777  1.52282  0.12604  -0.07408
    0.150  -0.55919  -0.53679  0.03248  0.47977  1.31863  0.11085  -0.05612
    0.200  -0.66730  -0.65710  0.02956  0.46896  1.21025  0.10065  -0.04777
    0.250  -0.73135  -0.69189  0.02516  0.45698  1.13978  0.07837  -0.03958
    0.300  -0.78840  -0.68208  0.03152  0.45065  1.05645  0.04621  -0.03245
    0.350  -0.83320  -0.69252  0.03233  0.44141  1.01481  0.05533  -0.02765
    0.400  -0.86810  -0.74537  0.03521  0.43589  1.00182  0.05914  -0.02363
    0.450  -0.88575  -0.73547  0.03923  0.42954  0.94803  0.06557  -0.01790
    0.500  -0.89944  -0.69269  0.04159  0.42699  0.94724  0.06067  -0.01710
    0.600  -0.91493  -0.63480  0.04580  0.41593  0.95504  0.07576  -0.01606
    0.700  -0.93236  -0.63204  0.04993  0.40303  1.01362  0.08323  -0.01527
    0.750  -0.93217  -0.63780  0.04989  0.40219  1.03634  0.08203  -0.01622
    0.800  -0.92975  -0.65092  0.05114  0.39766  1.05807  0.08385  -0.01434
    0.900  -0.92777  -0.57775  0.05266  0.38861  1.11036  0.09388  -0.01658
    1.000  -0.93815  -0.60041  0.05421  0.38150  1.16634  0.09095  -0.01502
    1.200  -0.93377  -0.56801  0.05576  0.36982  1.29484  0.08078  -0.01434
    1.400  -0.93847  -0.48684  0.05782  0.35868  1.32222  0.08353  -0.00681
    1.600  -0.92242  -0.40484  0.05645  0.35713  1.30431  0.07158  -0.00268
    1.800  -0.91608  -0.29053  0.05615  0.34643  1.35426  0.07341   0.00000
    2.000  -0.90369  -0.18149  0.05307  0.34133  1.38763  0.06790   0.00000
    2.500  -0.89442  -0.04175  0.05954  0.33960  1.41986  0.08582   0.00000
    3.000  -0.87386   0.00000  0.05596  0.35349  1.37795  0.10208   0.00000
    3.500  -0.85510   0.00000  0.05469  0.35286  1.34678  0.07501   0.00000
    4.000  -0.84680   0.00000  0.05469  0.36845  1.25830  0.05876   0.00000
    """)

    COEFFS_REG = CoeffsTable(sa_damping=5, table="""\
    imt     ckUSNZ     ckJP     ckTW      ckCH     ckWA   ckGRTR     ckWMT    ckNWE
    pga    -0.0302   0.0117  -0.0233   0.01580  0.10010  -0.0118   0.01720   0.0314
    0.010  -0.0302   0.0117  -0.0233   0.01580  0.10010  -0.0118   0.01720   0.0314
    0.025  -0.0303   0.0135  -0.0272   0.01500  0.10130  -0.0100   0.01740   0.0264
    0.040  -0.0336   0.0298  -0.0394   0.01110  0.10590  -0.0148   0.01010   0.0178
    0.050  -0.0400   0.0575  -0.0541   0.00990  0.10710  -0.0240  -0.00930   0.0038
    0.070  -0.0346   0.0508  -0.0560  -0.00120  0.11190  -0.0190  -0.01140  -0.0206
    0.100  -0.0287   0.0199  -0.0450   0.02200  0.12510  -0.0095   0.00840  -0.0222
    0.150  -0.0187  -0.0228  -0.0114   0.01430  0.11050   0.0044   0.02580  -0.0307
    0.200  -0.0196  -0.0439   0.0089   0.00560  0.11340   0.0133   0.03500  -0.0254
    0.250  -0.0227  -0.0543   0.0222   0.00590  0.10160   0.0162   0.04800   0.0274
    0.300  -0.0216  -0.0583   0.0300  -0.00003  0.08600   0.0153   0.05800   0.0407
    0.350  -0.0187  -0.0583   0.0301   0.00250  0.08900   0.0135   0.05340   0.0650
    0.400  -0.0239  -0.0544   0.0313   0.00800  0.09462   0.0070   0.05177   0.0728
    0.450  -0.0254  -0.0502   0.0327   0.01420  0.09990   0.0041   0.05190   0.0798
    0.500  -0.0322  -0.0461   0.0360   0.01560  0.10730  -0.0022   0.05530   0.0879
    0.600  -0.0388  -0.0389   0.0356   0.01630  0.12090  -0.0125   0.05650   0.0978
    0.700  -0.0411  -0.0333   0.0336   0.02200  0.12460  -0.0197   0.04830   0.1104
    0.750  -0.0416  -0.0305   0.0339   0.02520  0.12240  -0.0269   0.04850   0.1166
    0.800  -0.0436  -0.0289   0.0346   0.02970  0.12440  -0.0321   0.05120   0.1193
    0.900  -0.0412  -0.0262   0.0289   0.03250  0.12390  -0.0408   0.05740   0.1303
    1.000  -0.0397  -0.0195   0.0146   0.03750  0.12730  -0.0434   0.06730   0.1369
    1.200  -0.0395  -0.0071  -0.0025   0.04630  0.13760  -0.0467   0.06680   0.0914
    1.400  -0.0365  -0.0036  -0.0115   0.05740  0.13970  -0.0446   0.06400   0.0893
    1.600  -0.0361   0.0073  -0.0188   0.06200  0.13190  -0.0473   0.06000   0.0914
    1.800  -0.0307   0.0108  -0.0252   0.06090  0.13320  -0.0452   0.05230   0.1062
    2.000  -0.0280   0.0129  -0.0328   0.05910  0.14080  -0.0445   0.04100   0.1092
    2.500  -0.0336   0.0277  -0.0413   0.05880  0.14710  -0.0316   0.01970   0.0509
    3.000  -0.0325   0.0369  -0.0579   0.05660  0.16790  -0.0268   0.01380   0.1050
    3.500  -0.0272   0.0461  -0.0630   0.05250  0.14220  -0.0294   0.02160   0.1560
    4.000  -0.0203   0.0503  -0.0641   0.05720  0.19450  -0.0242   0.01380   0.2198
    """)
