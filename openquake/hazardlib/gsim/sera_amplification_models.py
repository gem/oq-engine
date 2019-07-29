# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Implements SERA site amplification models class: `PitilakisEtAl2018`,
                                                 `Eurocode8Amplification`,
                                                 `Eurocode8AmplificationDefault`,
                                                 `SandikkayaDinsever2018`,
                                                 `KothaEtAl2018SERAGeology`
"""
import numpy as np
from copy import deepcopy
from scipy.constants import g
# from scipy.interpolate import interp1d
from openquake.hazardlib.gsim.base import (GMPE, CoeffsTable, registry)
from openquake.hazardlib.imt import PGA, SA, from_string
from openquake.hazardlib.gsim.kotha_2019 import KothaEtAl2019SERA
from openquake.hazardlib import const


imls = [0., 0.25, 0.5, 0.75, 1., 1.25]


# Short period amplification factors defined by Pitilakis et al., (2018)
FS = {
"A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
"B1": [1.3, 1.3, 1.2, 1.2, 1.2, 1.2],
"B2": [1.4, 1.3, 1.3, 1.2, 1.1, 1.1],
"C1": [1.7, 1.6, 1.4, 1.3, 1.3, 1.2],
"C2": [1.6, 1.5, 1.3, 1.2, 1.1, 1.0],
"C3": [1.8, 1.6, 1.4, 1.2, 1.1, 1.0],
"D":  [2.2, 1.9, 1.6, 1.4, 1.2, 1.0],
"E":  [1.7, 1.6, 1.6, 1.5, 1.5, 1.5]
}


# Long period amplification factors defined by Pitilakis et al., (2018)
F1 = {
"A":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
"B1": [1.4, 1.4, 1.4, 1.4, 1.3, 1.3],
"B2": [1.6, 1.5, 1.5, 1.5, 1.4, 1.3],
"C1": [1.7, 1.6, 1.5, 1.5, 1.4, 1.3],
"C2": [2.1, 2.0, 1.9, 1.8, 1.8, 1.7],
"C3": [3.2, 3.0, 2.7, 2.5, 2.4, 2.3],
"D":  [4.1, 3.8, 3.3, 3.0, 2.8, 2.7],
"E":  [1.3, 1.3, 1.2, 1.2, 1.2, 1.2]
}


# Pitilakis GMPE Wrapper
uppernames = '''
DEFINED_FOR_INTENSITY_MEASURE_TYPES
DEFINED_FOR_STANDARD_DEVIATION_TYPES
REQUIRES_SITES_PARAMETERS
REQUIRES_RUPTURE_PARAMETERS
REQUIRES_DISTANCES
'''.split()


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
    experimental = True

    #: Supported tectonic region type is undefined (applies to any)
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set((PGA, SA))

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,))

    #: Required site parameters are Vs30 and the Pitilakis et al (2018) site
    #: class (others will be added for the GMPE in question)
    REQUIRES_SITES_PARAMETERS = set(('vs30', "ec8_p18"))

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set(())

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 800.0

    def __init__(self, gmpe_name, reference_velocity=None, **kwargs):
        super().__init__()
        if isinstance(gmpe_name, str):
            self.gmpe = registry[gmpe_name](**kwargs)
        else:
            # An instantiated class is passed as an argument
            self.gmpe = deepcopy(gmpe_name)
        if reference_velocity:
            self.rock_vs30 = reference_velocity
        else:
            self.rock_vs30 = self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gmpe, name)))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations calling the input GMPE
        for the mean acceleration for PGA and Sa (1.0) on the reference rock,
        defining the amplification factors and code spectrum to return the
        mean ground motion at the desired period, before the calling the
        input GMPE once more in order to return the standard deviations for the
        required IMT.
        """
        sctx_r = deepcopy(sctx)
        sctx_r.vs30 = self.rock_vs30 * np.ones_like(sctx_r.vs30)
        # Get PGA and Sa (1.0) from GMPE
        pga_r = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, PGA(),
                                               stddev_types)[0]
        s_1_rp = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, SA(1.0),
                                                stddev_types)[0]
        s_s_rp = self.CONSTANTS["F0"] * np.exp(pga_r)
        s_1_rp = np.exp(s_1_rp)
        # Get the short and long period amplification factors
        f_s, f_l = self.get_amplification_factor(s_s_rp, s_1_rp, sctx)
        s_1 = f_l * s_1_rp
        s_s = f_s * s_s_rp
        # Get the mean ground motion at the IMT using the design code spectrum
        mean = self.get_amplified_mean(s_s, s_1, s_1_rp, imt)
        # Call the original GMPE to return the standard deviation for the
        # IMT in question
        stddevs = self.gmpe.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                 stddev_types)[1]
        return mean, stddevs

    def get_amplification_factor(self, s_s, s_1, sctx):
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
                for j in range(1, len(imls) - 1):
                    jdx = np.logical_and(s_ss >= imls[j],
                                         s_ss < imls[j + 1])
                    if not np.any(jdx):
                        continue
                    dfs = FS[ec8][j + 1] - FS[ec8][j]
                    dfl = F1[ec8][j + 1] - F1[ec8][j]
                    diml = imls[j + 1] - imls[j]
                    f_ss[jdx] = FS[ec8][j] + (s_ss[jdx] - imls[j]) *\
                        (dfs / diml)
                    f_ls[jdx] = F1[ec8][j] + (s_ss[jdx] - imls[j]) * \
                        (dfl / diml)
                f_s[idx] = f_ss
                f_l[idx] = f_ls
        return f_s, f_l

    def get_amplified_mean(self, s_s, s_1, s_1_rp, imt):
        """
        Given the amplified short- and long-period input accelerations,
        returns the mean ground motion for the IMT according to the design
        spectrum construction in equations 1 - 5 of Pitilakis et al., (2018)
        """
        if "PGA" in str(imt) or imt.period <= self.CONSTANTS["TA"]:
            # PGA or v. short period acceleration
            return np.log(s_s / self.CONSTANTS["F0"])
        mean = np.copy(s_s)
        t_c = s_1 / s_s
        t_b = t_c / self.CONSTANTS["kappa"]
        t_b[t_b < 0.05] = 0.05
        t_b[t_b > 0.1] = 0.1
        t_d = 2.0 + np.zeros_like(s_1_rp)
        idx = s_1_rp > 0.1
        if np.any(idx):
            t_d[idx] = 1.0 + (10. * s_1_rp[idx])
        idx = np.logical_and(self.CONSTANTS["TA"] < imt.period,
                             t_b >= imt.period)
        if np.any(idx):
            mean[idx] = (s_s[idx] / (t_b[idx] - self.CONSTANTS["TA"])) *\
                ((imt.period - self.CONSTANTS["TA"]) +
                 (t_b[idx] - imt.period) / self.CONSTANTS["F0"])
        idx = np.logical_and(t_c < imt.period, t_d >= imt.period)
        if np.any(idx):
            mean[idx] = s_1[idx] / imt.period
        idx = t_d < imt.period
        if np.any(idx):
            mean[idx] = t_d[idx] * s_1[idx] / (imt.period ** 2.)
        return np.log(mean)

    CONSTANTS = {
        "F0": 2.5,
        "kappa": 5.0,
        "TA": 0.03,
    }


class Eurocode8Amplification(PitilakisEtAl2018):
    """
    Implements a general class to return a ground motion based on the
    Eurocode 8 design spectrum:
    CEN (2018): "Eurocode 8: Earthquake Resistant Design of Structures"
    Revised 2nd Draft SC8 PT1 - Rev 20

    The potential notes highlighted in :class:`PitilakisEtAl2018` apply
    in this case too.
    """
    experimental = True

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
    REQUIRES_SITES_PARAMETERS = set(('vs30', "h800",))

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 800.0

    def __init__(self, gmpe_name, reference_velocity=800.0, **kwargs):
        super().__init__(gmpe_name=gmpe_name)
        self.rock_vs30 = reference_velocity if reference_velocity else\
            self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gmpe, name)))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        As with the :class:`PitilakisEtal2018`, the mean ground motion is
        determined by construction of the Eurocode 8 design spectrum from the
        short- and long-period acceleration coefficients amplified to the
        desired site class, with the standard deviations taken from the
        original GMPE at the desired IMT
        """
        sctx_r = deepcopy(sctx)
        sctx_r.vs30 = self.rock_vs30 * np.ones_like(sctx_r.vs30)
        # Get PGA and Sa (1.0) from GMPE
        pga_r = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, PGA(),
                                               stddev_types)[0]
        s_1_rp = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, SA(1.0),
                                                stddev_types)[0]
        s_s_rp = self.CONSTANTS["F0"] * np.exp(pga_r)
        s_1_rp = np.exp(s_1_rp)
        ec8 = self.get_ec8_class(sctx.vs30, sctx.h800)
        f_s, f_l = self.get_amplification_factor(s_s_rp, s_1_rp, ec8, sctx)
        s_1 = f_l * s_1_rp
        s_s = f_s * s_s_rp
        mean = self.get_amplified_mean(s_s, s_1, s_1_rp, imt)
        stddevs = self.gmpe.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                 stddev_types)[1]
        return mean, stddevs

    def get_amplification_factor(self, s_s_rp, s_1_rp, ec8, sctx):
        """
        Returns the amplification factors based on the proposed EC8 formulation
        in Table 3.4
        """
        r_alpha = 1.0 - 2.0E3 * ((s_s_rp * g) / (sctx.vs30 ** 2))
        r_beta = 1.0 - 2.0E3 * ((s_1_rp * g) / (sctx.vs30 ** 2))
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

    @staticmethod
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
    experimental = True

    #: Required site parameters are the EC8 site class, everything else will
    #: be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = set(('ec8',))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations following the approach
        in :class:`Eurocode8Amplification`
        """
        sctx_r = deepcopy(sctx)
        sctx_r.vs30 = self.rock_vs30 * np.ones_like(sctx_r.vs30)
        # Get PGA and Sa (1.0) from GMPE
        pga_r = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, PGA(),
                                               stddev_types)[0]
        s_1_rp = self.gmpe.get_mean_and_stddevs(sctx_r, rctx, dctx, SA(1.0),
                                                stddev_types)[0]
        s_s_rp = self.CONSTANTS["F0"] * np.exp(pga_r)
        s_1_rp = np.exp(s_1_rp)
        f_s, f_l = self.get_amplification_factor(s_s_rp, s_1_rp, sctx)
        s_1 = f_l * s_1_rp
        s_s = f_s * s_s_rp
        mean = self.get_amplified_mean(s_s, s_1, s_1_rp, imt)
        stddevs = self.gmpe.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                 stddev_types)[1]
        return mean, stddevs

    def get_amplification_factor(self, s_s_rp, s_1_rp, sctx):
        """
        Returns the default amplification factor dependent upon the site class
        """
        f_s = np.ones(sctx.ec8.shape)
        f_l = np.ones(sctx.ec8.shape)
        for key in EC8_FS_default:
            idx = sctx.ec8 == key
            if np.any(idx):
                f_s[idx] = EC8_FS_default[key]
                f_l[idx] = EC8_FL_default[key]
        return f_s, f_l


# Sandikkaya & Dinsever

REGION_SET = ["USNZ", "JP", "TW", "CH", "WA", "TRGR", "WMT", "NWE"]


class SandikkayaDinsever2018(GMPE):
    """
    Implements the nonlinear site amplification model of Sandikkaya &
    Dinsever (2018)
    Sandikkaya, M. A. and Dinsever, L. D. (2018) "A Site Amplification Model
        for Crustal Earthquakes", Geosciences, 264(8),
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
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Shallow Crust"

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set((PGA, SA))

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameters will be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'z1pt0'))

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    #: Defined reference velocity is 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 760.0

    def __init__(self, gmpe_name, reference_velocity=760., region=None,
                 phi_0=None, **kwargs):
        super().__init__()
        if isinstance(gmpe_name, str):
            self.gmpe = registry[gmpe_name](**kwargs)
        else:
            # An instantiated class is passed as an argument
            self.gmpe = deepcopy(gmpe_name)
        # Define the reference velocity - set to 760. by default
        self.rock_vs30 = reference_velocity if reference_velocity else\
            self.DEFINED_FOR_REFERENCE_VELOCITY
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gmpe, name)))
        stddev_check = (const.StdDev.INTER_EVENT in
                        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES) and\
                        (const.StdDev.INTRA_EVENT in
                        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
        if not stddev_check:
            raise ValueError("Input GMPE %s not defined for inter- and intra-"
                             "event standard deviation" % str(self.gmpe))

        if isinstance(phi_0, dict):
            # Input phi_0 model
            iphi_0 = {}
            for key in phi_0:
                iphi_0[from_string(key)] = phi_0[key]
            self.phi_0 = CoeffsTable(sa_damping=5, table=iphi_0)
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


    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        sctx_r = deepcopy(sctx)
        sctx_r.vs30 = self.rock_vs30 * np.ones_like(sctx_r.vs30)
        mean, stddevs = self.gmpe.get_mean_and_stddevs(
            sctx_r, rctx, dctx, imt, [const.StdDev.INTER_EVENT,
                                      const.StdDev.INTRA_EVENT])
        psarock = np.exp(mean)
        C = self.COEFFS_SITE[imt]
        if self.region:
            ck = self.COEFFS_REG[imt][self.region]
        else:
            ck = 0.0
        ampl = self.get_site_amplification(C, psarock, sctx, ck)
        mean += ampl
        stddevs = self.get_stddevs(C, stddevs, psarock, sctx.vs30, imt,
                                   stddev_types)
        return mean, stddevs

    def get_site_amplification(self, C, psarock, sites, ck):
        """
        Returns the site amplification model define in equation (9)
        """
        vs30_s = np.copy(sites.vs30)
        vs30_s[vs30_s > 1000.] = 1000.
        fn_lin = (C["b1"] + ck) * np.log(vs30_s / 760.)
        fn_z = C["b2"] * np.log(sites.z1pt0)
        fn_nl = C["b3"] * np.log((psarock + 0.1 * g) / (0.1 * g)) *\
            np.exp(-np.exp(2.0 * np.log(sites.vs30) - 11.))
        return fn_lin + fn_z + fn_nl

    def get_stddevs(self, C, istddevs, psa_rock, vs30, imt, stddev_types):
        """
        Returns the standard deviation adjusted for the site-response model
        """
        tau, phi = istddevs
        ysig = np.copy(psa_rock)
        ysig[ysig > 0.35] = 0.35
        ysig[ysig < 0.005] = 0.005
        vsig = np.copy(vs30)
        vsig[vsig > 600.0] = 600.0
        vsig[vsig < 150.] = 150.
        sigma_s = C["sigma_s"] * C["c0"] * (C["c1"] * np.log(ysig) +
                                            C["c2"] * np.log(vsig))
        if self.phi_0:
            phi0 = self.phi_0[imt]
        else:
            # In the case that no input phi0 is defined take 'approximate'
            # phi0 as 85 % of phi
            phi0 = 0.85 * phi
        phi = np.sqrt(phi0 ** 2. + sigma_s ** 2.)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(vs30.shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(vs30.shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(vs30.shape))
        return stddevs

    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    imt          b1        b3       b2  sigma_s       c0       c1        c2
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


class KothaEtAl2019SERAGeology(KothaEtAl2019SERA):
    """
    Adaptation of the Kotha et al. (2019) GMPE for use with slope and geology
    in place of inferred/measured Vs30.
    """
    experimental = True

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("slope", "geology"))

    #: Geological Units
    GEOLOGICAL_UNITS = [b"CENOZOIC", b"HOLOCENE", b"MESOZOIC",
                        b"PALEOZOIC", b"PLEISTOCENE", b"PRECAMBRIAN"]

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        C = self.COEFFS[imt]
        C_AMP_FIXED = self.COEFFS_FIXED[imt]
        C_AMP_RAND_INT = self.COEFFS_RANDOM_INT[imt]
        C_AMP_RAND_GRAD = self.COEFFS_RANDOM_GRAD[imt]

        mean = (self.get_magnitude_scaling(C, rup.mag) +
                self.get_distance_term(C, rup, dists.rjb, imt) +
                self.get_tau_f_adjustment(C) +
                self.get_site_amplification(C_AMP_FIXED, C_AMP_RAND_INT,
                                            C_AMP_RAND_GRAD, sites))
        if imt.name in "PGA SA":
            mean -= np.log(100.0 * g)
        stddevs = self.get_stddevs(C, C_AMP_FIXED, dists.rjb.shape,
                                   stddev_types, sites)
        if self.sigma_mu_epsilon:
            # Apply the epistemic uncertainty factor (sigma_mu) multiplied by
            # the number of standard deviations
            sigma_mu = self.get_sigma_mu_adjustment(C, imt, rup, dists)
            # Cap sigma_mu at 0.35
            sigma_mu[sigma_mu > 0.35] = 0.35
            mean += (self.sigma_mu_epsilon * sigma_mu)
        return mean, stddevs

    def get_site_amplification(self, C_AMP_FIXED, C_AMP_RAND_INT,
                               C_AMP_RAND_GRAD, sites):
        """
        Returns the site amplification term depending on whether the Vs30
        is observed of inferred
        """
        ampl = np.zeros(sites.slope.shape)
        geol_units = np.unique(sites.geology)
        t_slope = np.copy(sites.slope)
        t_slope[t_slope > 0.1] = 0.1
        for geol_unit in geol_units:
            idx = sites.geology == geol_unit
            if geol_unit in self.GEOLOGICAL_UNITS:
                v1 = C_AMP_FIXED["V1"] + C_AMP_RAND_INT[geol_unit.decode()]
                v2 = C_AMP_FIXED["V2"] + C_AMP_RAND_GRAD[geol_unit.decode()]
            else:

                v1 = C_AMP_FIXED["V1"]
                v2 = C_AMP_FIXED["V2"]
            ampl[idx] = v1 + v2 * np.log(t_slope[idx])
        return ampl

    def get_stddevs(self, C, C_FIXED, stddev_shape, stddev_types, sites):
        """
        Returns the standard deviations, with different site standard
        deviation for inferred vs. observed vs30 sites.
        """
        stddevs = []
        tau = C["tau_event"]
        phi = np.sqrt(C["phi0"] ** 2.0 + C_FIXED["phi_s"] ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs

    COEFFS_FIXED = CoeffsTable(sa_damping=5, table="""\
    imt             V1           V2       phi_s
    pga    -0.29594600  -0.09183800  0.57075400
    pgv    -0.36804900  -0.11453800  0.46278900
    0.010  -0.29209050  -0.09447700  0.57291750
    0.025  -0.28921325  -0.09568025  0.57902300
    0.040  -0.28462425  -0.09647375  0.59541900
    0.050  -0.28295050  -0.09424475  0.61734200
    0.070  -0.27990775  -0.08924825  0.64161025
    0.100  -0.26363625  -0.08390100  0.65599525
    0.150  -0.24501350  -0.08196050  0.64772600
    0.200  -0.25077550  -0.08429875  0.62417350
    0.250  -0.27834675  -0.08982250  0.59864700
    0.300  -0.31026225  -0.09745725  0.57698075
    0.350  -0.33999525  -0.10569825  0.56049800
    0.400  -0.36725150  -0.11258475  0.55141950
    0.450  -0.39050650  -0.11717625  0.54758150
    0.500  -0.41391825  -0.12185000  0.54270500
    0.600  -0.43917000  -0.12749250  0.53566000
    0.700  -0.45449650  -0.13062900  0.52891525
    0.750  -0.45800650  -0.13096425  0.52361200
    0.800  -0.46407100  -0.13190525  0.52104600
    0.900  -0.47601800  -0.13419625  0.52035575
    1.000  -0.48178325  -0.13455875  0.51749975
    1.200  -0.48527750  -0.13370700  0.51247825
    1.400  -0.49458775  -0.13496125  0.50752350
    1.600  -0.50175300  -0.13690675  0.50260125
    1.800  -0.50352650  -0.13782925  0.49706925
    2.000  -0.50485525  -0.13801150  0.48956175
    2.500  -0.50580975  -0.13804225  0.48092500
    3.000  -0.49708025  -0.13593300  0.47176350
    3.500  -0.47517075  -0.13018125  0.46087325
    4.000  -0.44889825  -0.12088900  0.45336125
    4.500  -0.42341650  -0.10901550  0.44920875
    5.000  -0.39536725  -0.09764825  0.44087650
    6.000  -0.36658825  -0.08814650  0.42946725
    7.000  -0.35351550  -0.08534975  0.42009150
    8.000  -0.35384600  -0.08686100  0.41627050
    """)

    COEFFS_RANDOM_INT = CoeffsTable(sa_damping=5, table="""\
    imt      CENOZOIC    HOLOCENE     MESOZOIC    PALEOZOIC  PLEISTOCENE  PRECAMBRIAN
    pga    0.00000000  0.00000000   0.00000000   0.00000000   0.00000000   0.00000000
    pgv   -0.02637900  0.15503300  -0.13205500  -0.10811500   0.15416300  -0.04264800
    0.010 -0.05485900  0.06018600  -0.06592600  -0.00670600   0.04745450   0.01985050
    0.025 -0.08811475  0.08763575  -0.09399725  -0.00547450   0.06940900   0.03054175
    0.040 -0.13240100  0.11203500  -0.11583375   0.00231150   0.09014075   0.04374750
    0.050 -0.11017575  0.08153475  -0.08152775   0.00763450   0.06696350   0.03557075
    0.070 -0.03846000  0.02704250  -0.02672825   0.00320150   0.02250450   0.01243975
    0.100 -0.03430225  0.02671650  -0.03745875   0.01218800   0.02102525   0.01183150
    0.150 -0.09512475  0.08072075  -0.11355975   0.03205725   0.06313950   0.03276750
    0.200 -0.11190625  0.10314475  -0.13820275   0.02538550   0.08540600   0.03617300
    0.250 -0.08486850  0.10203950  -0.11480175  -0.00777975   0.08397350   0.02143700
    0.300 -0.05058700  0.12498550  -0.11518875  -0.04274075   0.08121700   0.00231425
    0.350 -0.03410425  0.15222600  -0.12635550  -0.06804325   0.09039250  -0.01411450
    0.400 -0.03542500  0.16273825  -0.12304850  -0.08401400   0.11034900  -0.03059875
    0.450 -0.04344400  0.17864500  -0.11454275  -0.10350275   0.13765500  -0.05481075
    0.500 -0.05767100  0.20439875  -0.10854650  -0.13255575   0.17285700  -0.07848300
    0.600 -0.04740950  0.21638100  -0.10838175  -0.15723325   0.19255350  -0.09590975
    0.700 -0.00501500  0.21812050  -0.11718200  -0.16939250   0.18670725  -0.11323800
    0.750  0.02978525  0.22665325  -0.12979450  -0.17818575   0.18056125  -0.12901950
    0.800  0.04054575  0.23552775  -0.13498100  -0.18659825   0.18715200  -0.14164625
    0.900  0.04134525  0.23448350  -0.13162225  -0.18668025   0.19404775  -0.15157400
    1.000  0.02921750  0.21822875  -0.12182250  -0.17568350   0.20100050  -0.15094100
    1.200  0.01327950  0.19488825  -0.10668600  -0.16905475   0.21141850  -0.14384625
    1.400  0.01961050  0.17950150  -0.09589150  -0.17229700   0.21216175  -0.14308575
    1.600  0.03238425  0.17188925  -0.09245875  -0.17089625   0.20547250  -0.14639075
    1.800  0.02548350  0.16657725  -0.08847825  -0.16235625   0.20507475  -0.14630075
    2.000  0.00867850  0.15209175  -0.07797150  -0.15142050   0.21022750  -0.14160600
    2.500  0.00772100  0.13005225  -0.06929400  -0.14026600   0.20207975  -0.13029375
    3.000  0.01645200  0.11508775  -0.06808200  -0.13685650   0.18539975  -0.11200150
    3.500  0.01612800  0.10495550  -0.06778625  -0.13673125   0.17817025  -0.09473600
    4.000  0.01094075  0.07452950  -0.05107700  -0.09925375   0.13022525  -0.06536450
    4.500  0.00411475  0.02468825  -0.01745275  -0.03178775   0.04186600  -0.02142850
    5.000  0.00000000  0.00000000   0.00000000   0.00000000   0.00000000   0.00000000
    6.000  0.00000000  0.00000000   0.00000000   0.00000000   0.00000000   0.00000000
    7.000  0.00973950  0.01325425  -0.02404000  -0.01792800   0.03975650  -0.02078200
    8.000  0.01947900  0.02650850  -0.04808000  -0.03585600   0.07951300  -0.04156400
    """)

    COEFFS_RANDOM_GRAD = CoeffsTable(sa_damping=5, table="""\
    imt       CENOZOIC     HOLOCENE     MESOZOIC    PALEOZOIC  PLEISTOCENE  PRECAMBRIAN
    pga     0.00491300  -0.01478800   0.02632100   0.00210200  -0.01327800  -0.00527200
    pgv    -0.00470900  -0.00033700  -0.00079900  -0.00164800   0.00790300  -0.00041000
    0.010  -0.00597800   0.00200700   0.00281500  -0.00006700   0.00074950   0.00047300
    0.025  -0.01326100   0.01064200  -0.00879000  -0.00033325   0.00803075   0.00371100
    0.040  -0.02375950   0.01985600  -0.02046600   0.00054550   0.01599850   0.00782525
    0.050  -0.01913050   0.01403050  -0.01112200   0.00068025   0.01023475   0.00530725
    0.070  -0.00071150   0.00003975   0.00867650  -0.00200500  -0.00345650  -0.00254250
    0.100   0.00244550  -0.00245300   0.00975475  -0.00113725  -0.00482700  -0.00378200
    0.150  -0.01114125   0.00739725  -0.00812300   0.00320250   0.00625900   0.00240625
    0.200  -0.01619725   0.00791875  -0.00951050   0.00282375   0.01050450   0.00446075
    0.250  -0.01256200   0.00132725   0.00113125  -0.00018100   0.00760500   0.00267900
    0.300  -0.00581525   0.00084900   0.00131800  -0.00116300   0.00395375   0.00085725
    0.350  -0.00307375   0.00250400  -0.00170475  -0.00128000   0.00343625   0.00011775
    0.400  -0.00753350   0.00038150   0.00065700  -0.00037900   0.00573825   0.00113475
    0.450  -0.01626075  -0.00142300   0.00445925   0.00090125   0.00909050   0.00323250
    0.500  -0.02618350  -0.00164575   0.00726300   0.00098675   0.01359325   0.00598650
    0.600  -0.02596850  -0.00441200   0.00875025   0.00185275   0.01185200   0.00792525
    0.700  -0.01442475  -0.00730150   0.00771975   0.00416300   0.00277700   0.00706650
    0.750  -0.00414850  -0.00690575   0.00492675   0.00502275  -0.00351975   0.00462500
    0.800  -0.00123925  -0.00716450   0.00408100   0.00569225  -0.00572700   0.00435775
    0.900  -0.00182325  -0.01031100   0.00579050   0.00818425  -0.00861075   0.00677025
    1.000  -0.00647525  -0.01574800   0.00938750   0.01278275  -0.01166000   0.01171300
    1.200  -0.01280675  -0.02122750   0.01321675   0.01845900  -0.01493200   0.01729050
    1.400  -0.01205300  -0.02349525   0.01427350   0.02211175  -0.02067775   0.01984100
    1.600  -0.00822050  -0.02411175   0.01402375   0.02354150  -0.02606725   0.02083475
    1.800  -0.01009425  -0.02522300   0.01571100   0.02438225  -0.02728075   0.02250475
    2.000  -0.01598500  -0.02859225   0.01894200   0.02646950  -0.02641375   0.02557900
    2.500  -0.01650400  -0.03263775   0.02021700   0.02978850  -0.02904200   0.02817800
    3.000  -0.01255600  -0.03405875   0.01991325   0.03237800  -0.03261325   0.02693725
    3.500  -0.01103075  -0.03474150   0.02036150   0.03301225  -0.03140925   0.02380875
    4.000  -0.01450800  -0.04258125   0.02474075   0.04481975  -0.04269500   0.03022425
    4.500  -0.02238225  -0.05731850   0.03308050   0.06980050  -0.06842100   0.04524050
    5.000  -0.02712000  -0.06411950   0.03766550   0.07964600  -0.07926200   0.05318950
    6.000  -0.02758000  -0.06222675   0.03803475   0.07185725  -0.07524225   0.05515675
    7.000  -0.02296125  -0.05572500   0.02893225   0.06096075  -0.05998650   0.04877975
    8.000  -0.01827300  -0.05041250   0.01969150   0.05483050  -0.04697200   0.04113550
    """)
