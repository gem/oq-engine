# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA, CAV, RSD575, RSD595


class WangEtAl2025(GMPE):
    """
    Implements the GMM for Turkey developed by Mao-Xin Wang et al.,
    published as "Ground-motion models for Arias intensity, cumulative absolute 
    velocity, and duration parameters in Türkiye" (2025, Soil Dynam Earthq Eng).
    
    Wang, M. X., Leung, A. Y. F., Zhu, C., Güryuva, B.,
    Sandıkkaya, M. A., Ji, K. (2025). 
    Ground-motion models for Arias intensity, cumulative absolute velocity, 
    and duration parameters in Türkiye. Soil Dynamics and Earthquake Engineering, 
    196, 109440.  https://doi.org/10.1016/j.soildyn.2025.109440 
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA, CAV, RSD575, RSD595}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {"vs30"}

    #: Required rupture parameters are magnitude, rake, ztor
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "rake", "ztor"}

    #: Required distance measure is Joyner-Boore distance
    REQUIRES_DISTANCES = {"rjb"}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        # Get mean and standard deviation
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            
            # Magnitude Scaling (fmag), see equation (8)
            f_mag = C["c0"] + C["c1"] * ctx.mag
            idx = ctx.mag > C["b1"]
            f_mag[idx] += C["c2"] * (ctx.mag[idx] - C["b1"])
            idx = ctx.mag > C["b2"]
            f_mag[idx] += C["c3"] * (ctx.mag[idx] - C["b2"])
            
            # Magnitude-Dependent Distance Scaling (fdis,mag), see equation (9)
            f_dis = (C["c4"] + C["c5"] * ctx.mag) * np.log(np.sqrt(ctx.rjb**2 + C["c6"]**2))
                
            # Faulting Mechanism (fmech), see equation (10)
            frv = np.zeros_like(ctx.rake)
            fnm = np.zeros_like(ctx.rake)
            frv[(ctx.rake > 30.) & (ctx.rake < 150.)] = 1.
            fnm[(ctx.rake > -150.) & (ctx.rake < -30.)] = 1.
            f_mech = C["c7"] * (ctx.mag - C["b3"]) / (C["b4"] - C["b3"]) * fnm + C["c8"] * frv
            idx_smallMag = ctx.mag <= C["b3"]            
            f_mech[idx_smallMag] = C["c8"] * frv[idx_smallMag]
            idx_largeMag = ctx.mag > C["b4"]          
            f_mech[idx_largeMag] = C["c7"] * fnm[idx_largeMag] + C["c8"] * frv[idx_largeMag]
            
            # Source Depth (fdepth), see equation (11)
            f_depth = C["c9"] * np.log(ctx.ztor+1)

            # Assume No Aftershock Scaling, see equation (12)
            f_as = 0
            
            # Site Response (fsite), see equation (13)
            f_site = C["c11"] * np.log(np.minimum(ctx.vs30, C["b6"]) / C["vref"])

            # Anelastic Distance Scaling, see equation (14)
            f_anelas = C["c12"] * np.maximum(ctx.rjb-80, 0)

            # Final Mean Prediction, see equation (7)
            mean[m] = f_mag + f_dis + f_mech + f_depth + f_as + f_site + f_anelas
            
            # Compute Standard Deviations
            M_tau1 = 6
            M_tau2 = 6.5
            M_phi1 = 5
            M_phi2 = 6.5
            # between-event
            temp_tau = C["tau1"] + (C["tau2"] - C["tau1"]) * (ctx.mag - M_tau1) / (M_tau2 - M_tau1)
            temp_tau[ctx.mag <= M_tau1] = M_tau1
            temp_tau[ctx.mag > M_tau2] = M_tau2
            tau[m] = temp_tau
            # within-event
            temp_phi = C["phi1"] + (C["phi2"] - C["phi1"]) * (ctx.mag - M_phi1) / (M_phi2 - M_phi1)
            temp_phi[ctx.mag <= M_phi1] = M_phi1
            temp_phi[ctx.mag > M_phi2] = M_phi2
            phi[m] = temp_phi       
            # total
            sig[m] = np.sqrt(tau[m] ** 2 + phi[m] ** 2)

    # Coefficient table
    COEFFS = CoeffsTable(
        table="""\
        IMT    c0    c1    c2    c3    c4    c5    c6    c7    c8    c9    c10    c11    c12    b1    b2    b3    b4    b6    vref    tau1    tau2    phi1    phi2
        ia    -11.1415    2.0755    -0.9198    0    -3.7481    0.2951    5.347    -0.4587    0    0.3435    -0.0146    -1.3411    -0.0084    6.3    999    4.6    5.5    800    760    0.746    0.564    1.006    1.006
        cav    -4.8074    1.1833    -0.3845    0    -1.5225    0.1191    6.2075    -0.178    0    0.1614    -0.0077    -0.7554    -0.0033    6.3    999    4.6    5.5    800    760    0.346    0.303    0.459    0.459
        rsd575    -2.2988    0.3366    0.2848    2.2215    1.25    -0.1161    4.5577    0.2115    0.1011    -0.0557    0    -0.0999    0.0023    4.5    7.6    5.2    6    1200    370    0.236    0.164    0.429    0.362
        rsd595    -0.3917    0.2813    0.1272    1.8806    0.8438    -0.0721    3.252    0.1817    0.0753    -0.0437    0    -0.1698    0.0021    4.5    7.6    5.1    5.9    1200    370    0.195    0.17    0.35    0.308
    """,
    )
