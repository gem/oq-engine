# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import CoeffsTable, gsim_aliases
from openquake.hazardlib.gsim.nga_east import ITPL, NGAEastGMPE

# Coefficients for EPRI sigma model taken from Table 5.5 of Goulet et al.
# (2017)
COEFFS_USGS_SIGMA_EPRI = CoeffsTable(sa_damping=5, table="""\
imt     tau_M5   phi_M5   tau_M6   phi_M6   tau_M7   phi_M7
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


def get_epri_tau_phi(imt, mag):
    """
    Returns the inter-event (tau) and intra_event standard deviation (phi)
    according to the updated EPRI (2013) model"""
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


class NGAEastUSGSGMPE(NGAEastGMPE):
    """
    For the "core" NGA East set the table is provided in the code in a
    subdirectory fixed to the path of the present file. The GMPE table option
    is therefore no longer needed
    """
    gmpe_table = ""
    PATH = os.path.join(os.path.dirname(__file__), "usgs_nga_east_tables")

    def __init__(self, **kwargs):
        if 'sigma_model' not in kwargs:
            kwargs['sigma_model'] = "EPRI"
        self.sigma_model = kwargs['sigma_model']
        if kwargs['sigma_model'] not in ("EPRI", "PANEL"):
            raise ValueError("USGS CEUS Sigma Model %s not supported"
                             % kwargs['sigma_model'])
        super().__init__(**kwargs)

    def _setup_standard_deviations(self, fle):
        # Not needed here
        pass

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        # Get the PGA on the reference rock condition
        if PGA in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
            rock_imt = PGA()
        else:
            rock_imt = SA(0.01)
        pga_r = self.get_hard_rock_mean(rctx, dctx, rock_imt, stddev_types)

        # Get the desired spectral acceleration on rock
        if not str(imt) == "PGA":
            # Calculate the ground motion at required spectral period for
            # the reference rock
            mean = self.get_hard_rock_mean(rctx, dctx, imt, stddev_types)
        else:
            # Avoid re-calculating PGA if that was already done!
            mean = np.copy(pga_r)

        mean += self.get_site_amplification(imt, np.exp(pga_r), sctx)
        # Get standard deviation model
        nsites = getattr(dctx, self.distance_type).shape
        stddevs = self.get_stddevs(rctx.mag, sctx.vs30, imt,
                                   stddev_types, nsites)
        return mean, stddevs

    def get_stddevs(self, mag, vs30, imt, stddev_types, num_sites):
        """
        Returns the standard deviations for either the ergodic or
        non-ergodic models
        """
        if self.sigma_model == "EPRI":
            # EPRI recommended aleatory uncertainty model
            tau, phi = get_epri_tau_phi(imt, mag)
            tau += np.zeros(num_sites)
            phi += np.zeros(num_sites)
        else:
            # Panel recommended model
            tau, phi0 = get_panel_tau_phi(imt, mag)
            tau += np.zeros(num_sites)
            phi0 += np.zeros(num_sites)
            phis2s = get_stewart_2019_phis2s(imt, vs30)
            phi = np.sqrt(phi0 ** 2. + phis2s ** 2.)

        sigma = np.sqrt(tau ** 2. + phi ** 2.)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sigma)
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau)
        return stddevs


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
    gsim_aliases[alias] = (f'[NGAEastUSGSGMPE]\n'
                           f'gmpe_table="nga_east_{key}.hdf5"')
