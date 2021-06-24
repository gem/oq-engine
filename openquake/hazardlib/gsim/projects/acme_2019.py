# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
import warnings
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.gsim.projects.acme_base import (
    get_phi_ss_at_quantile_ACME)
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.yenier_atkinson_2015 import \
        YenierAtkinson2015BSSA
from openquake.hazardlib.gsim.nga_east import (get_phi_s2ss_at_quantile,
                                               get_tau_at_quantile,
                                               get_phi_ss,
                                               TAU_SETUP,
                                               PHI_SETUP,
                                               PHI_S2SS_MODEL,
                                               TAU_EXECUTION)
warnings.filterwarnings("ignore", category=np.RankWarning)
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
    elif imt.name == 'SA' and imt.period > 0.4 and imt.period < 3.0:
        f_r_ss = 1.2 - (0.3/np.log10(3.0/0.4))*np.log10(imt.period/0.4)
    elif imt.name == 'SA' and imt.period >= 3.0:
        f_r_ss = 1.2 - (0.3/np.log10(3.0/0.4))*np.log10(3.0/0.4)
    else:
        raise ValueError('Unsupported IMT')
    # Set coefficients
    f_n_ss = 0.95
    p_r = 0.68
    p_n = 0.02
    # Normal - F_N:EQ
    if -135 < rake <= -45:
        famp = f_r_ss**(-p_r) * f_n_ss**(1-p_n)
    # Reverse - F_R:EQ
    elif 45 < rake <= 135:
        famp = f_r_ss**(1-p_r) * f_n_ss**(-p_n)
    # Strike-Slip - F_SS:EQ
    elif (-30 < rake <= 30) or (150 < rake <= 180) or (-180 < rake <= -150):
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

    It also fixes vs30 to 760 m/s
    """

    adapted = True

    def __init__(self):
        # Initialise using the super class
        super().__init__(focal_depth=10., region='CENA')
        # Adjust the set of required parameters for the description of the
        # rupture by adding rake
        _previous = list(super().REQUIRES_RUPTURE_PARAMETERS)
        self.REQUIRES_RUPTURE_PARAMETERS = frozenset(_previous + ['rake'])

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):

        # Compute mean and std
        mean = self._get_mean_on_soil(sctx, rctx, dctx, imt, stddev_types)

        # Get SoF correction
        famp = get_sof_adjustment(rctx.rake, imt)
        mean += np.log(famp)
        stddevs = np.zeros_like(mean)
        return mean, stddevs

    def _get_mean_on_soil(self, sctx, rctx, dctx, imt, stddev_types):
        # Get PGA on rock
        tmp = PGA()
        pga_rock = super()._get_mean_on_rock(
            sctx, rctx, dctx, tmp, stddev_types)
        pga_rock = np.exp(pga_rock)
        # Site-effect model: always evaluated for 760 (see HID 2.6.2)
        vs30_760 = np.zeros_like(sctx.vs30)
        vs30_760[:] = 760
        f_s = self.get_fs_SeyhanStewart2014(imt, pga_rock, vs30_760)
        # Compute the mean on soil
        mean = super()._get_mean_on_rock(sctx, rctx, dctx, imt, stddev_types)
        mean += f_s
        return mean


class ChiouYoungs2014ACME2019(ChiouYoungs2014):
    """
    Implements a modified version of the CY2014 GMM. Main changes:
    - Hanging wall term excluded
    - Centered Ztor = 0
    - Centered Dpp = 0
    """

    adapted = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        # intensity on a reference soil is used for both mean
        # and stddev calculations.
        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        # exp1 and exp2 are parts of eq. 12 and eq. 13,
        # calculate it once for both.
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))
        mean = self._get_mean(sites, C, ln_y_ref, exp1, exp2)
        stddevs = np.zeros_like(mean)
        return mean, stddevs

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

    :param GMPE:
        GMPE is the **kwargs describing the GMPE (its name) and the sigma
        and kappa modifications to be imposed
    :param gmpe_name:
        GMPE class that will be adjusted by AlAtikSigmaModel
    :param tau_model:
        Choice of model for the inter-event standard deviation (tau), selecting
        from "global" {default}, "cena" or "cena_constant". default is global
    :param tau_quantile:
        tau quantile used in sigma model. default of None uses the mean.
    :param phi_model:
        Choice of model for the single-station intra-event standard deviation
        (phi_ss), selecting from "global" {default}, "cena" or "cena_constant"
        default is global.
    :param phi_quantile:
        phi quantile used in sigma model. default of None uses the mean.
    :param phi_s2ss_model:
        Choice of station-term s2ss model. Can be either "cena" or None. When
        None is input then the non-ergodic model is used
    :param phi_s2ss_quantile:
        s2ss quantile used in sigma model. default of None uses the mean.
    :param kappa_file:
        tab-delimited file of kappa values per IMT, where first column is
        IMT. includes a header.
    :param kappa_val:
        kappa value corresponding to a column header in kappa_file

    """

    adapted = True

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tau_model = kwargs.get('tau_model', 'global')
        self.phi_model = kwargs.get('phi_model', 'global')
        self.phi_s2ss_model = kwargs.get('phi_s2ss_model')
        self.TAU = None
        self.PHI_SS = None
        self.PHI_S2SS = None
        if self.phi_s2ss_model:
            self.ergodic = True
        else:
            self.ergodic = False
        self.tau_quantile = kwargs.get('tau_quantile')
        self.phi_ss_quantile = kwargs.get('phi_ss_quantile')
        self.phi_s2ss_quantile = kwargs.get('phi_s2ss_quantile')
        self._setup_standard_deviations(fle=None)
        self.kappa_file = kwargs.get('kappa_file')
        self.kappa_val = kwargs.get('kappa_val')

        self.gmpe_name = kwargs['gmpe_name']
        self.gmpe = registry[self.gmpe_name]()
        self.set_parameters()

        if self.kappa_file:
            with self.open(self.kappa_file) as myfile:
                data = myfile.read().decode('utf-8')
            self.KAPPATAB = CoeffsTable(table=data, sa_damping=5)

    def _setup_standard_deviations(self, fle):
        # setup tau
        self.TAU = get_tau_at_quantile(TAU_SETUP[self.tau_model]["MEAN"],
                                       TAU_SETUP[self.tau_model]["STD"],
                                       self.tau_quantile)
        # setup phi
        PHI_SETUP['global_linear'] = self.PHI_SS_GLOBAL_LINEAR
        self.PHI_SS = get_phi_ss_at_quantile_ACME(PHI_SETUP[self.phi_model],
                                                  self.phi_ss_quantile)
        # if required setup phis2ss
        if self.ergodic:
            if self.phi_s2ss_model == 'cena':
                self.PHI_S2SS = get_phi_s2ss_at_quantile(
                    PHI_S2SS_MODEL[self.phi_s2ss_model],
                    self.phi_s2ss_quantile)
            elif self.phi_s2ss_model == 'brb':
                self.PHI_S2SS = self.PHI_S2SS_BRB
            else:
                opts = "'cena', 'brb', or 'None'"
                raise ValueError('phi_s2ss_model can be {}'.format(opts))

    def get_corner_period(self, mag):
        """
        Corner period given as:
        10^(-1.884 - log10(D_sigma)/3 + 0.5*Mw)
        where D_sigma = 80 bars (8 MPa)
        from 2.6.5: cornerp is to be constrained to not go below 1.0
        """
        D_sigma = 80
        cornerp = 10**(-1.884 - np.log10(D_sigma)/3 + 0.5*mag)
        if cornerp < 1.0:
            cornerp = 1.0
        return cornerp

    def get_capping_period(self, cornerp, gmpe, imt):
        """
        Capping period is the smaller of the corner period and the
        max period of coefficents provided by the GMPE
        """
        try:
            coeffs = gmpe.COEFFS.sa_coeffs
            imts = [*coeffs]
            periods = [imt.period for imt in imts]
            if gmpe.__class__.__name__ == 'BindiEtAl2014Rjb':
                highest_period = 2.0
                periods = [p for p in periods if p <= highest_period]
                set_highest = periods[-5:]
            elif gmpe.__class__.__name__ == 'RietbrockEdwards2019Low':
                set_highest = periods[-2:]
            else:
                set_highest = periods
        except AttributeError:
            coeffs = gmpe.TAB2.sa_coeffs
            imts = [*coeffs]
            periods = [imt.period for imt in imts]
            if gmpe.__class__.__name__ == 'BindiEtAl2014Rjb':
                highest_period = 2.0
                periods = [p for p in periods if p <= highest_period]
                set_highest = periods[-5:]
            elif gmpe.__class__.__name__ == 'RietbrockEdwards2019Low':
                set_highest = periods[-2:]
            else:
                set_highest = periods

        return set_highest

    def get_disp_from_acc(self, acc, imt):
        """
        Method is only called when imt.period > cappingp
       :param acc:
            Acceleration in log space
       :param imt:
            The period
       :returns:
            Displacement
        """
        disp = np.exp(acc) * imt**2 / (2 * np.pi)**2
        return disp

    def get_acc_from_disp(self, disp, imt):
        """
        Method is only called when imt.period > cappingp
        :param imt:
            The period
        :param disp:
            Displacement
        :returns:
            Acceleration in log space
        """
        acc = np.log(disp * (2 * np.pi / imt)**2)
        return acc

    def extrapolate_in_PSA(self, sites, rup, dists, imt_high,
                           set_imt, stds_types, imt):

        extrap_mean = []
        t_log10 = np.log10([im for im in set_imt])
        for d in np.arange(0, len(dists.rjb)):
            dist = DistancesContext()
            if hasattr(dists, 'rjb'):
                dist.rjb = np.array([dists.rjb[d]])
            if hasattr(dists, 'rrup'):
                dist.rrup = np.array([dists.rrup[d]])
            means_log10 = []
            for im in set_imt:
                mean_ln, _ = self.gmpe.get_mean_and_stddevs(
                                   sites, rup, dist, SA(im), stds_types)
                mean = np.exp(mean_ln[0])
                means_log10.append(np.log10(mean))
                
            mb = np.polyfit(t_log10, means_log10, 1)
            mean_imt_log10 = mb[0] * np.log10(imt) + mb[1]
            extrap_mean.append(np.log(10**mean_imt_log10))

        return extrap_mean

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types,
                             extr=True):

        nsites = len(sites)
        stddevs = self.get_stddevs(rup.mag, imt, stds_types, nsites)
        cornerp = self.get_corner_period(rup.mag)
        # capping period only compares
        # - highest period with a coefficient
        # - corner period
        # - 2.0 if it's bindi
        sp = self.get_capping_period(cornerp, self.gmpe, imt)
        hp = sp[-1]

        # 1 - if imt.period < cornerp, no changes needed
        if extr and imt.period <= cornerp and imt.period <= hp:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, imt, stds_types)
        # if the period is larger than the corner period but the corner period
        # is less than the highest period
        elif extr and imt.period >= cornerp and cornerp <= hp:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, SA(cornerp), stds_types)
            disp = self.get_disp_from_acc(mean, cornerp)
            mean = self.get_acc_from_disp(disp, imt.period)
        # if the corner period is longer than highest and imt is above
        # highets but below corner
        elif extr and cornerp > hp and hp <= imt.period < cornerp:
            mean = self.extrapolate_in_PSA(
                sites, rup, dists, hp, sp, stds_types, imt.period)
        elif extr and cornerp > hp and imt.period > cornerp:
            mean = self.extrapolate_in_PSA(
                sites, rup, dists, hp, sp, stds_types, cornerp)
            disp = self.get_disp_from_acc(mean, cornerp)
            mean = self.get_acc_from_disp(disp, imt.period)

        else:
            mean, _ = self.gmpe.get_mean_and_stddevs(
                sites, rup, dists, imt, stds_types)

        kappa = 1
        if self.kappa_file:

            if imt.period == 0:
                kappa = self.KAPPATAB[SA(0.01)][self.kappa_val]
            elif imt.period > 2.0:
                kappa = self.KAPPATAB[SA(2.0)][self.kappa_val]
            else:
                kappa = self.KAPPATAB[imt][self.kappa_val]

        return mean + np.log(kappa), stddevs

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
        # check if phi adjustment (2.6.6) is needed
        # -> if phi < 0.4 in middle branch and T is below 0.5 s
        # -> preserve separation between high and low phi values
        if imt.period < 0.5 and self.phi_ss_quantile == 0.5:
            phi = max(phi, 0.4)

        elif imt.period < 0.5 and self.phi_ss_quantile != 0.5:
            # compute phi at quantile 0.5 and take the maximum comp to 0.4
            PHI_SS_0p5 = get_phi_ss_at_quantile_ACME(
                                        PHI_SETUP[self.phi_model], 0.5)
            phi_0p5 = get_phi_ss(imt, mag, PHI_SS_0p5)

            # make adjustment if needed
            phi = 0.4 + phi - phi_0p5 if phi_0p5 < 0.4 else phi

        if self.ergodic:
            C = self.PHI_S2SS[imt]
            phi = np.sqrt(phi ** 2. + C["phi_s2ss"] ** 2.)

        return phi

    # PHI_SS2S coefficients, table 2.2 HID
    PHI_S2SS_BRB = CoeffsTable(logratio=False, sa_damping=5., table="""\
        imt   phi_s2ss
        PGA     0.0000
        0.001   0.0000
        0.999   0.0000
        1.000   0.0011
        1.200   0.0040
        1.500   0.0075
        2.000   0.0111
        10.00   0.0111
        """)

    # Phi_ss coefficients for the global model
    PHI_SS_GLOBAL_LINEAR = CoeffsTable(logratio=False, sa_damping=5., table="""\
    imt     mean_a   var_a  mean_b  var_bs
    pgv     0.5034  0.0609  0.3585  0.0316
    pga     0.5477  0.0731  0.3505  0.0412
    0.010   0.5477  0.0731  0.3505  0.0412
    0.020   0.5464  0.0727  0.3505  0.0416
    0.030   0.5450  0.0723  0.3505  0.0419
    0.040   0.5436  0.0720  0.3505  0.0422
    0.050   0.5424  0.0716  0.3505  0.0425
    0.075   0.5392  0.0707  0.3505  0.0432
    0.100   0.5361  0.0699  0.3505  0.0439
    0.150   0.5299  0.0682  0.3543  0.0453
    0.200   0.5240  0.0666  0.3659  0.0465
    0.250   0.5183  0.0651  0.3765  0.0476
    0.300   0.5127  0.0637  0.3876  0.0486
    0.400   0.5022  0.0611  0.4066  0.0503
    0.500   0.4923  0.0586  0.4170  0.0515
    0.750   0.4704  0.0535  0.4277  0.0526
    1.000   0.4519  0.0495  0.4257  0.0508
    1.500   0.4231  0.0439  0.4142  0.0433
    2.000   0.4026  0.0405  0.4026  0.0396
    3.000   0.3775  0.0371  0.3775  0.0366
    4.000   0.3648  0.0358  0.3648  0.0358
    5.000   0.3583  0.0353  0.3583  0.0356
    7.500   0.3529  0.0350  0.3529  0.0355
    10.00   0.3519  0.0350  0.3519  0.0355
    """)
