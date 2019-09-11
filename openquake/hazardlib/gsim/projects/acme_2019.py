# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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

import os
import math
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.yenier_atkinson_2015 import \
        YenierAtkinson2015BSSA
from openquake.hazardlib.gsim.nga_east import (get_phi_s2ss_at_quantile,
                                               get_tau_at_quantile,
                                               get_phi_ss_at_quantile,
                                               get_phi_ss,
                                               TAU_SETUP,
                                               PHI_SETUP,
                                               PHI_S2SS_MODEL,
                                               TAU_EXECUTION)

PATH = os.path.join(os.path.dirname(__file__), "..", "nga_east_tables")


def get_sof_adjustment(rake, imt):
    """
    Computes adjustment factor for style-of-faulting following the scheme
    proposed by Bommer et al. (2003).

    :param rake:
        Rake value
    :param imt:
        The intensity measure type
    :return:
        The adjustment factor
    """
    if imt.name == 'PGA' or (imt.name == 'SA' and imt.period <= 0.4):
        f_r_ss = 1.2
    elif imt.name == 'SA' and imt.period > 0.4:
        f_r_ss = 1.2 - (0.3/np.log10(3.0/0.4))*np.log10(imt.period/0.4)
    else:
        raise ValueError('Unsupported IMT')
    # Set coefficients
    f_n_ss = 0.95
    p_r = 0.85
    p_n = 0.0
    # Normal - F_N:EQ
    if -135 < rake <= -45:
        famp = f_r_ss**(-p_r) * f_n_ss**(1-p_n)
    # Reverse - F_R:EQ
    elif 45 < rake <= 135:
        famp = f_r_ss**(1-p_r) * f_n_ss**(-p_n)
    # Strike-Slip - F_SS:EQ
    elif ((-30 < rake <= 30) or (150 < rake <= 180) or (-180 < rake <= -150)):
        famp = f_r_ss**(-p_r) * f_n_ss**(-p_n)
    else:
        raise ValueError('Unrecognised rake value')
    return famp


class YenierAtkinson2015ACME2019(YenierAtkinson2015BSSA):
    """
    This is a modified version of the
    :class:`openquake.hazardlib.gsim.yenier_atkinson_2015.YenierAtkinson2015BSSA`
    which incorporates a correction of the median ground motion based on the
    focal mechanism.
    """

    def __init__(self):
        # Initialise using the super class
        super().__init__(focal_depth=10., region='CENA')
        # Adjust the set of required parameters for the description of the
        # rupture by adding rake
        _previous = [s for s in list(super().REQUIRES_RUPTURE_PARAMETERS)]
        self.REQUIRES_RUPTURE_PARAMETERS = frozenset(_previous + ['rake'])

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        # Compute mean and std
        mean, stddevs = super().get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                     stddev_types)
        # Get SoF correction
        famp = get_sof_adjustment(rctx.rake, imt)
        mean += np.log(famp)
        return mean, stddevs


class ChiouYoungs2014ACME2019(ChiouYoungs2014):
    """
    Implements a modified version of the CY2014 GMM. Main changes:
    - Hanging wall term excluded
    - Centered Ztor = 0
    - Centered Dpp = 0
    """

    def _get_mean(self, sites, C, ln_y_ref, exp1, exp2):
        """
        Add site effects to an intensity. Implements eq. 13b.
        """
        eta = epsilon = 0.
        ln_y = (
            # first line of eq. 12
            ln_y_ref + eta
            # second line
            + C['phi1'] * np.log(sites.vs30 / 1130).clip(-np.inf, 0)
            # third line
            + C['phi2'] * (exp1 - exp2)
            * np.log((np.exp(ln_y_ref) * np.exp(eta) + C['phi4']) / C['phi4'])
            # fourth line - removed
            # fifth line
            + epsilon
        )
        return ln_y

    def _get_ln_y_ref(self, rup, dists, C):
        """
        Get an intensity on a reference soil.
        Implements eq. 13a.
        """
        # Reverse faulting flag
        Frv = 1. if 30 <= rup.rake <= 150 else 0.
        # Normal faulting flag
        Fnm = 1. if -120 <= rup.rake <= -60 else 0.
        # A part in eq. 11
        mag_test1 = np.cosh(2. * max(rup.mag - 4.5, 0))
        # Centered DPP
        centered_dpp = 0
        # Centered Ztor
        centered_ztor = 0
        #
        dist_taper = np.fmax(1 - (np.fmax(dists.rrup - 40,
                                  np.zeros_like(dists)) / 30.),
                             np.zeros_like(dists))
        dist_taper = dist_taper.astype(np.float64)
        ln_y_ref = (
            # first part of eq. 11
            C['c1']
            + (C['c1a'] + C['c1c'] / mag_test1) * Frv
            + (C['c1b'] + C['c1d'] / mag_test1) * Fnm
            + (C['c7'] + C['c7b'] / mag_test1) * centered_ztor
            + (C['c11'] + C['c11b'] / mag_test1) *
            np.cos(math.radians(rup.dip)) ** 2
            # second part
            + C['c2'] * (rup.mag - 6)
            + ((C['c2'] - C['c3']) / C['cn'])
            * np.log(1 + np.exp(C['cn'] * (C['cm'] - rup.mag)))
            # third part
            + C['c4']
            * np.log(dists.rrup + C['c5']
                     * np.cosh(C['c6'] * max(rup.mag - C['chm'], 0)))
            + (C['c4a'] - C['c4'])
            * np.log(np.sqrt(dists.rrup ** 2 + C['crb'] ** 2))
            # forth part
            + (C['cg1'] + C['cg2'] / (np.cosh(max(rup.mag - C['cg3'], 0))))
            * dists.rrup
            # fifth part
            + C['c8'] * dist_taper
            * min(max(rup.mag - 5.5, 0) / 0.8, 1.0)
            * np.exp(-1 * C['c8a'] * (rup.mag - C['c8b']) ** 2) * centered_dpp
            # sixth part
            # + C['c9'] * Fhw * np.cos(math.radians(rup.dip)) *
            # (C['c9a'] + (1 - C['c9a']) * np.tanh(dists.rx / C['c9b']))
            # * (1 - np.sqrt(dists.rjb ** 2 + rup.ztor ** 2)
            #   / (dists.rrup + 1.0))
        )
        return ln_y_ref


class AlAtikSigmaModel(GMPE):
    """
    Implements a modifiable GMPE that uses the ground-motion standard
    deviation model proposed by Al-Atik in 2015 as described in:

    Al-Atik, L. (2015). "NGA-East: Ground-Motion Standard Deviation Models
    for Central and Eastern North America". PEER Report No. 2015/07, 217
    pages.

    The implementation of the sigma model is the one already available
    in the current implementation of the NGA East GMMs.

    :param gmpe_name:
        Name of the gmpe

    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, tau_quantile=None,
                 phi_ss_quantile=None, phi_s2ss_quantile=None):
        # this is taken from http://tiny.cc/krb5bz
        self.tau_model = tau_model
        self.phi_model = phi_model
        self.phi_s2ss_model = phi_s2ss_model
        self.TAU = None
        self.PHI_SS = None
        self.PHI_S2SS = None
        if self.phi_s2ss_model:
            self.ergodic = True
        else:
            self.ergodic = False
        self.tau_quantile = tau_quantile
        self.phi_ss_quantile = phi_ss_quantile
        self.phi_s2ss_quantile = phi_s2ss_quantile
        self._setup_standard_deviations(fle=None)

        super().__init__(gmpe_name=gmpe_name)
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()

    def _setup_standard_deviations(self, fle):
        # setup tau
        self.TAU = get_tau_at_quantile(TAU_SETUP[self.tau_model]["MEAN"],
                                       TAU_SETUP[self.tau_model]["STD"],
                                       self.tau_quantile)
        # setup phi
        self.PHI_SS = get_phi_ss_at_quantile(PHI_SETUP[self.phi_model],
                                             self.phi_ss_quantile)
        # if required setup phis2ss
        if self.ergodic:
            self.PHI_S2SS = get_phi_s2ss_at_quantile(
                PHI_S2SS_MODEL[self.phi_s2ss_model],
                self.phi_s2ss_quantile)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        mean, _ = self.gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stds_types)
        nsites = len(sites)
        stddevs = self.get_stddevs(rup.mag, imt, stds_types, nsites)
        return mean, stddevs

    def get_stddevs(self, mag, imt, stddev_types, num_sites):
        """
        Returns the standard deviations for either the ergodic or
        non-ergodic models
        """
        tau = self._get_tau(imt, mag)
        phi = self._get_phi(imt, mag)
        sigma = np.sqrt(tau ** 2. + phi ** 2.)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sigma + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(num_sites))
        return stddevs

    def _get_tau(self, imt, mag):
        """
        Returns the inter-event standard deviation (tau)
        """
        return TAU_EXECUTION[self.tau_model](imt, mag, self.TAU)

    def _get_phi(self, imt, mag):
        """
        Returns the within-event standard deviation (phi)
        """
        phi = get_phi_ss(imt, mag, self.PHI_SS)
        if self.ergodic:
            C = self.PHI_S2SS[imt]
            phi = np.sqrt(phi ** 2. + C["phi_s2ss"] ** 2.)
        return phi
