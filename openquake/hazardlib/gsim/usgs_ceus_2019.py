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
Module exports :class:`NGAEastUSGSGMPE`
"""
import os
import numpy as np
import pandas as pd

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import CoeffsTable, add_alias
from openquake.hazardlib.gsim.nga_east import (
    ITPL, NGAEastGMPE, get_mean_amp, get_site_amplification_sigma)
from openquake.hazardlib.gsim.gmpe_table import _get_mean
from openquake.hazardlib.gsim.utils_chapman_guo_2021 import (get_psa_df,
                                                             get_fcpa,
                                                             get_zscale,
                                                             CPA_IMTS)


# Path to CSV containing the Coastal Plains PSA ratios required for Chapman and
# Guo (2021) site amplification model.
# NOTE: values for SA(0.6) have been computed through a weighted interpolation
# of SA(0.5) and SA(0.75) values as required for GEM Global Hazard Maps/Mosaic.
PSAS= os.path.join(os.path.dirname(__file__), 'chapman_guo_2021_psa_ratios.csv')


# Coefficients for period-dependent bias adjustment provided by Ramos-Sepulveda
# et al.(2023). These are required for the 2023 Conterminous US model and are
# taken from:
# https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/resources/gmm/coeffs/nga-east-usgs-adj-2023.csv?ref_type=heads 
COEFFS_USGS_2023_ADJ = CoeffsTable(sa_damping=5, table="""\
imt     nga_adj  vs30_b 
pgv     -0.085   -0.250
pga     -0.040   -0.346 
0.010   -0.070   -0.352 
0.020   -0.210   -0.305 
0.030   -0.211   -0.261 
0.050   -0.212   -0.220 
0.075   -0.205   -0.220 
0.100   -0.205   -0.220 
0.150   -0.192   -0.220
0.200   -0.149   -0.220
0.250   -0.132   -0.220
0.300   -0.121   -0.220
0.400   -0.097   -0.220
0.500   -0.090   -0.220
0.750   -0.040   -0.205
1.000   -0.010   -0.175
1.500    0.045   -0.173
2.000    0.140   -0.173
3.000    0.270   -0.173
4.000    0.315   -0.173
5.000    0.377   -0.173
7.500    0.448   -0.173
10.00    0.401   -0.173
""")


# Coefficients for EPRI sigma model taken from Table 5.5 of Goulet et al.
# (2017)
COEFFS_USGS_SIGMA_EPRI = CoeffsTable(sa_damping=5, table="""\
imt     tau_M5   phi_M5   tau_M6   phi_M6   tau_M7   phi_M7
pgv     0.3925   0.5979   0.3612   0.5218   0.3502   0.5090
pga     0.4320   0.6269   0.3779   0.5168   0.3525   0.5039
0.010   0.4320   0.6269   0.3779   0.5168   0.3525   0.5039
0.020   0.4710   0.6682   0.4385   0.5588   0.4138   0.5462
0.030   0.4710   0.6682   0.4385   0.5588   0.4138   0.5462
0.050   0.4710   0.6682   0.4385   0.5588   0.4138   0.5462
0.075   0.4710   0.6682   0.4385   0.5588   0.4138   0.5462
0.100   0.4710   0.6682   0.4385   0.5588   0.4138   0.5462
0.150   0.4433   0.6693   0.4130   0.5631   0.3886   0.5506
0.200   0.4216   0.6691   0.3822   0.5689   0.3579   0.5566
0.250   0.4150   0.6646   0.3669   0.5717   0.3427   0.5597
0.300   0.4106   0.6623   0.3543   0.5846   0.3302   0.5727
0.400   0.4088   0.6562   0.3416   0.5997   0.3176   0.5882
0.500   0.4175   0.6526   0.3456   0.6125   0.3217   0.6015
0.750   0.4439   0.6375   0.3732   0.6271   0.3494   0.6187
1.000   0.4620   0.6219   0.3887   0.6283   0.3650   0.6227
1.500   0.4774   0.5957   0.4055   0.6198   0.3819   0.6187
2.000   0.4809   0.5860   0.4098   0.6167   0.3863   0.6167
3.000   0.4862   0.5813   0.4186   0.6098   0.3952   0.6098
4.000   0.4904   0.5726   0.4144   0.6003   0.3910   0.6003
5.000   0.4899   0.5651   0.4182   0.5986   0.3949   0.5986
7.500   0.4803   0.5502   0.4067   0.5982   0.3835   0.5982
10.00   0.4666   0.5389   0.3993   0.5885   0.3761   0.5885
""")


COEFFS_USGS_SIGMA_PANEL = CoeffsTable(sa_damping=5, table="""\
imt         t1       t2       t3       t4     ss_a     ss_b    s2s1    s2s2
pgv     0.3633   0.3532   0.3340   0.3136   0.4985   0.3548   0.487   0.458
pga     0.4436   0.4169   0.3736   0.3415   0.5423   0.3439   0.533   0.566
0.010   0.4436   0.4169   0.3736   0.3415   0.5423   0.3439   0.533   0.566
0.020   0.4436   0.4169   0.3736   0.3415   0.5410   0.3438   0.537   0.577
0.030   0.4436   0.4169   0.3736   0.3415   0.5397   0.3437   0.542   0.598
0.050   0.4436   0.4169   0.3736   0.3415   0.5371   0.3435   0.583   0.653
0.075   0.4436   0.4169   0.3736   0.3415   0.5339   0.3433   0.619   0.633
0.100   0.4436   0.4169   0.3736   0.3415   0.5308   0.3431   0.623   0.590
0.150   0.4436   0.4169   0.3736   0.3415   0.5247   0.3466   0.603   0.532
0.200   0.4436   0.4169   0.3736   0.3415   0.5189   0.3585   0.578   0.461
0.250   0.4436   0.4169   0.3736   0.3415   0.5132   0.3694   0.554   0.396
0.300   0.4436   0.4169   0.3736   0.3415   0.5077   0.3808   0.527   0.373
0.400   0.4436   0.4169   0.3736   0.3415   0.4973   0.4004   0.491   0.339
0.500   0.4436   0.4169   0.3736   0.3415   0.4875   0.4109   0.472   0.305
0.750   0.4436   0.4169   0.3736   0.3415   0.4658   0.4218   0.432   0.273
1.000   0.4436   0.4169   0.3736   0.3415   0.4475   0.4201   0.431   0.257
1.500   0.4436   0.4169   0.3736   0.3415   0.4188   0.4097   0.424   0.247
2.000   0.4436   0.4169   0.3736   0.3415   0.3984   0.3986   0.423   0.239
3.000   0.4436   0.4169   0.3736   0.3415   0.3733   0.3734   0.418   0.230
4.000   0.4436   0.4169   0.3736   0.3415   0.3604   0.3604   0.412   0.221
5.000   0.4436   0.4169   0.3736   0.3415   0.3538   0.3537   0.404   0.214
7.500   0.4436   0.4169   0.3736   0.3415   0.3482   0.3481   0.378   0.201
10.00   0.4436   0.4169   0.3736   0.3415   0.3472   0.3471   0.319   0.193
""")
    

def get_us23_adjs(ctx, imt, bias_adj=False, cpa=False, psa_df=None):
    """
    This function assists with applying the CEUS GMM adjustments
    required for the 2023 Conterminous US NSHMP (if specified):
    
    1) Computes the period-dependent bias correction factor of
       Ramos-Sepulveda et al. (2023). If sediment depth (z_sed)
       is available for the sites the adjustment is scaled by
       z_scale (z_sed dependent scaling factor).
    
    2) Computes the f_cpa parameter required for the Coastal Plains
       amplification model of Chapman and Guo (2021).

    :param bias_adj: Bool determining if the period-dependent bias
                     adjustment is applied. 

    :param cpa: Bool determining if the Coastal Plains amplification
                adjustment model is applied. 

    :param psa_df: Pandas DataFrame containing the PSA ratios (table
                   for mag, rrup, z_sed combinations for the given IMT.
    """
    # Get sed. depth scaling
    if hasattr(ctx, 'z_sed'):
        # If z_sed_scaling is True
        z_scale = get_zscale(ctx.z_sed)
    else:
        # Turn off z_sed scaling
        z_scale = np.full(len(ctx.vs30), 0)

    # If period-dependent bias adjustment 
    if bias_adj:
        b_coeffs = COEFFS_USGS_2023_ADJ[imt]
        b_adj = np.full(len(ctx.vs30), b_coeffs['nga_adj'])
        mask_vs30 = ctx.vs30 > 1000.
        if mask_vs30.any():
            vs30 = ctx.vs30[mask_vs30]
            vs30[vs30 > 2000.] = 2000.
            b_adj[mask_vs30] += b_coeffs['vs30_b'] * np.log(vs30 / 1000.0)    
        u_adj = (1.0 - z_scale) * b_adj # Scale by z_sed factor
    else:
        u_adj = None

    # If Coastal Plains site amp get required params
    if cpa:
        coastal = get_fcpa(ctx, imt, z_scale, psa_df)
    else:
        coastal = None, None

    return u_adj, coastal


def get_epri_tau_phi(imt, mag):
    """
    Returns the inter-event (tau) and intra_event standard deviation (phi)
    according to the updated EPRI (2013) model
    """
    C = COEFFS_USGS_SIGMA_EPRI[imt]
    if mag <= 5.0:
        tau = C["tau_M5"]
        phi = C["phi_M5"]
    elif mag <= 6.0:
        tau = ITPL(mag, C["tau_M6"], C["tau_M5"], 5.0, 1.0)
        phi = ITPL(mag, C["phi_M6"], C["phi_M5"], 5.0, 1.0)
    elif mag <= 7.0:
        tau = ITPL(mag, C["tau_M7"], C["tau_M6"], 6.0, 1.0)
        phi = ITPL(mag, C["phi_M7"], C["phi_M6"], 6.0, 1.0)
    else:
        tau = C["tau_M7"]
        phi = C["phi_M7"]
    return tau, phi


def get_panel_tau_phi(imt, mag):
    """
    Returns the inter-event (tau) and intra_event standard deviation (phi)
    according to the USGS Sigma Panel recommendations
    """
    C = COEFFS_USGS_SIGMA_PANEL[imt]
    # Get tau
    if mag <= 4.5:
        tau = C["t1"]
    elif mag <= 5.0:
        tau = ITPL(mag, C["t2"], C["t1"], 4.5, 0.5)
    elif mag <= 5.5:
        tau = ITPL(mag, C["t3"], C["t2"], 5.0, 0.5)
    elif mag <= 6.5:
        tau = ITPL(mag, C["t4"], C["t3"], 5.5, 1.0)
    else:
        tau = C["t4"]
    # Get phi
    if mag <= 5.0:
        phi = C["ss_a"]
    elif mag <= 6.5:
        phi = ITPL(mag, C["ss_b"], C["ss_a"], 5.0, 1.5)
    else:
        phi = C["ss_b"]
    return tau, phi


def get_stewart_2019_phis2s(imt, vs30):
    """
    Returns the phis2s model of Stewart et al. (2019)
    """
    v_1 = 1200.
    v_2 = 1500.
    C = COEFFS_USGS_SIGMA_PANEL[imt]
    phis2s = C["s2s1"] + np.zeros(vs30.shape)
    idx = vs30 > v_2
    phis2s[idx] = C["s2s2"]
    idx = np.logical_and(vs30 > v_1, vs30 <= v_2)
    if np.any(idx):
        phis2s[idx] = C["s2s1"] - ((C["s2s1"] - C["s2s2"]) / (v_2 - v_1)) *\
            (vs30[idx] - v_1)
    return phis2s


@_get_mean.add("usgs")
def _get_mean(kind, data, dists, table_dists):
    """
    Returns the mean intensity measure level from the tables applying
    log-log interpolation of the IML with distance (contrast with the
    linear interpolation applied in usual GMPE tables)

    :param data:
        The intensity measure level vector for the given magnitude and IMT
    :param dists:
        The distances for the given magnitude and IMT
    :param table_dists:
        The distance table for the given magnitude and IMT
    """
    # For extremely short distance (rrup = 0) use an arbitrarily small
    # distance measure (1.0E-5 used by US NSHMP code)
    table_dists[table_dists < 1.0E-5] = 1.0E-5
    mean = np.exp(
        np.interp(np.log10(dists), np.log10(table_dists), np.log(data)))
    # For those distances less than or equal to the shortest distance
    # extrapolate the shortest distance value
    mean[dists <= table_dists[0]] = data[0]
    # For those distances significantly greater than the furthest distance
    # set to 1E-20.
    mean[dists > (table_dists[-1] + 1.0E-3)] = 1E-20
    # If any distance is between the final distance and a margin of 0.001
    # km then assign to smallest distance
    mean[mean < -1.] = data[-1]
    return mean


def _get_stddevs(sigma_model, mag, ctx, imt):
    """
    Returns the standard deviations according to the choice of aleatory
    uncertainty model. Note that for compatibility with the US NSHMP
    code a weighted sum of the two aleatory uncertainty models is used,
    with the EPRI model assigned a weight of 0.8 and the PANEL model 0.2.
    """
    if sigma_model in ("EPRI", "COLLAPSED"):
        # EPRI recommended aleatory uncertainty model
        tau_epri, phi_epri = get_epri_tau_phi(imt, mag)
    if sigma_model in ("PANEL", "COLLAPSED"):
        # Panel recommended model
        tau_panel, phi0_panel = get_panel_tau_phi(imt, mag)
        phis2s = get_stewart_2019_phis2s(imt, ctx.vs30)
        phi_panel = np.sqrt(phi0_panel ** 2. + phis2s ** 2.)
    if sigma_model == "EPRI":
        tau = tau_epri
        phi = phi_epri
        sigma = np.sqrt(tau ** 2. + phi ** 2.)
    elif sigma_model == "PANEL":
        tau = tau_panel
        phi = phi_panel
        sigma = np.sqrt(tau ** 2. + phi ** 2.)
    else:
        # Get the weighted sum of the two models
        sigma_epri = np.sqrt(tau_epri ** 2. + phi_epri ** 2.)
        sigma_panel = np.sqrt(tau_panel ** 2. + phi_panel ** 2.)
        sigma = 0.8 * sigma_epri + 0.2 * sigma_panel
        tau, phi = 0., 0.
    return [sigma, tau, phi]


class NGAEastUSGSGMPE(NGAEastGMPE):
    """
    For the "core" NGA East set the table is provided in the code in a
    subdirectory fixed to the path of the present file. The GMPE table option
    is therefore no longer needed if a GSIM alias is used.
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
    PATH = os.path.join(os.path.dirname(__file__), "usgs_nga_east_tables")
    kind = "usgs"

    def __init__(self, gmpe_table="", sigma_model="COLLAPSED",
                 epistemic_site=True, usgs_2023_bias_adj=False,
                 coastal_plains_site_amp=False, z_sed_scaling=False):
        self.sigma_model = sigma_model
        self.epistemic_site = epistemic_site
        if self.sigma_model not in ("EPRI", "PANEL", "COLLAPSED"):
            raise ValueError("USGS CEUS Sigma Model %s not supported"
                             % self.sigma_model)
        if self.sigma_model == "COLLAPSED":
            # In the case of the collapsed model only the total standard
            # deviation can be defined
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
        self.usgs_2023_bias_adj = usgs_2023_bias_adj # US 2023 NSHMP
        self.coastal_plains_site_amp = coastal_plains_site_amp # US 2023 NSHMP
        if self.coastal_plains_site_amp:
            # Add CG21 PSA ratios
            with open(PSAS, 'rb') as f:
                self.psa_tab = pd.read_csv(f)
        # Only scale bias adjustment or Coastal Plains site amp by sediment
        # depth scaling factor if specified by user
        if z_sed_scaling:
            self.REQUIRES_SITES_PARAMETERS |= {"z_sed"}
        super().__init__(gmpe_table)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        [mag] = np.unique(np.round(ctx.mag, 2))
        for m, imt in enumerate(imts):
            
            # Apply required 2023 US NSHMP adjustments if specified
            if self.usgs_2023_bias_adj or self.coastal_plains_site_amp:
                # Get PSA ratios if Coastal Plains site amp model
                if self.coastal_plains_site_amp:
                    if str(imt) in CPA_IMTS:
                        psa_df = get_psa_df(self.psa_tab, imt)
                    else:
                        raise ValueError(f'Chapman and Guo (2021) Coastal Plains '
                                         f'PSA ratios are not provided for {imt}.')
                else:
                    psa_df = None
                # Get the adjustment params
                u_adj, cstl = get_us23_adjs(ctx, imt, self.usgs_2023_bias_adj,
                                            self.coastal_plains_site_amp, psa_df)
            else:
                u_adj, cstl = None, None

            # Get mean
            imean, _site_amp, pga_r, cpa_term = get_mean_amp(self, mag, ctx,
                                                             imt, u_adj, cstl)

            # Get the coefficients for the IMTs
            C_LIN = self.COEFFS_LINEAR[imt]
            C_F760 = self.COEFFS_F760[imt]
            C_NL = self.COEFFS_NONLINEAR[imt]
            # Get collapsed amplification model for -sigma, 0, +sigma
            # with weights of 0.185, 0.63, 0.185 respectively
            if self.epistemic_site:
                f_rk = np.log((np.exp(pga_r) + C_NL["f3"]) / C_NL["f3"])
                site_amp_sigma = get_site_amplification_sigma(
                    self, ctx.vs30, f_rk, C_LIN, C_F760, C_NL)
                mean[m] = np.log(
                    0.185 * np.exp(imean - site_amp_sigma) +
                    0.63 * np.exp(imean) +
                    0.185 * np.exp(imean + site_amp_sigma)) + cpa_term
            else:
                mean[m] = imean + cpa_term

            # Get standard deviation model
            sig[m], tau[m], phi[m] = _get_stddevs(
                self.sigma_model, mag, ctx, imt)


lines = '''\
NGAEastUSGSSeedSP15 SP15
NGAEastUSGSSeed1CCSP 1CCSP
NGAEastUSGSSeed2CVSP 2CVSP
NGAEastUSGSSeed1CVSP 1CVSP
NGAEastUSGSSeed2CCSP 2CCSP
NGAEastUSGSSeedGraizer Graizer
NGAEastUSGSSeedB_ab95 B_ab95
NGAEastUSGSSeedB_bca10d B_bca10d
NGAEastUSGSSeedB_sgd02 B_sgd02
NGAEastUSGSSeedB_a04 B_a04
NGAEastUSGSSeedB_bs11 B_bs11
NGAEastUSGSSeedB_ab14 B_ab14
NGAEastUSGSSeedHA15 HA15
NGAEastUSGSSeedPEER_EX PEER_EX
NGAEastUSGSSeedPEER_GP PEER_GP
NGAEastUSGSSeedGraizer16 Graizer16
NGAEastUSGSSeedGraizer17 Graizer17
NGAEastUSGSSeedFrankel Frankel
NGAEastUSGSSeedYA15 YA15
NGAEastUSGSSeedPZCT15_M1SS PZCT15_M1SS
NGAEastUSGSSeedPZCT15_M2ES PZCT15_M2ES
NGAEastUSGSSammons1 usgs_1
NGAEastUSGSSammons2 usgs_2
NGAEastUSGSSammons3 usgs_3
NGAEastUSGSSammons4 usgs_4
NGAEastUSGSSammons5 usgs_5
NGAEastUSGSSammons6 usgs_6
NGAEastUSGSSammons7 usgs_7
NGAEastUSGSSammons8 usgs_8
NGAEastUSGSSammons9 usgs_9
NGAEastUSGSSammons10 usgs_10
NGAEastUSGSSammons11 usgs_11
NGAEastUSGSSammons12 usgs_12
NGAEastUSGSSammons13 usgs_13
NGAEastUSGSSammons14 usgs_14
NGAEastUSGSSammons15 usgs_15
NGAEastUSGSSammons16 usgs_16
NGAEastUSGSSammons17 usgs_17'''.splitlines()
for line in lines:
    alias, key = line.split()
    add_alias(alias, NGAEastUSGSGMPE, gmpe_table=f"nga_east_{key}.hdf5")
