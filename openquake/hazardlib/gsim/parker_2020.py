#Grace Parker
#Modified February 26, 2020, to expand comments
#Modified March 25, 2020, to to call consolidated coefficient table

# Input Parameters --------------------------------------------------------

#Event type: 0 == interface, 1 == slab

#region corresponds to options in the DatabaseRegion column of the flatfile, plus global. Must be a string. If no matches, default will be global model:
# "global", "Alaska", "Cascadia", "CAM", "Japan", "SA" or "Taiwan"

#Saturation Region corresponds to regions defined by C. Ji and R. Archuleta (2018):
# "global", "Aleutian","Alaska","Cascadia","CAM_S", "CAM_N", "Japan_Pac","Japan_Phi","SA_N","SA_S", "Taiwan_W","Taiwan_E"

# Rrup is number in kilometers

#Hypocentral depth in km.
#To use Ztor value to estimate hypocentral depth, see Ch. 4.3.3/Eqs. 4.16 & 4.17  of Parker et al. (2020) PEER report

# period can be: (-1,0,0.01,0.02,0.025,0.03,0.04,0.05,0.075,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.75,1,1.5,2,2.5,3,4,5,7.5,10) 
# where -1 == PGV and 0 == PGA

#VS30 in units m/s

#Z2.5 in units m. Only used if DatabaseRegion == "Japan" or "Cascadia".
#Can also specify "default" to get no basin term (e.g. delta_Z2.5 = 0)

#basin is only used if DatabaseRegion == "Cascadia". Value can be 0, 1, or 2, 
#where 0 == having an estimate of Z2.5 outside mapped basin, 1 == Seattle basin,
#and 0 == other mapped basin (Tacoma, Everett, Georgia, etc.)

# Other pertinent information ---------------------------------------------

# Coefficient files must be in the active working directory or have the path specified

# "GMM_at_VS30_IF_v4.R" calls function "GMM_at_760_IF_v4.R" to compute PGAr in the nonlinear site term. 
#This function must be in the R environment else an error will occur.

# The output is the desired median model prediction in LN units
# Take the exponential to get PGA, PSA in g or the PGV in cm/s
# This model does not make predictions for New Zealand. We recommend using the global model for that case.


import math

import numpy as np
import pandas as pd

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA, PGV

class ParkerEtAl2020SInter(GMPE):

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground acceleration and peak ground velocity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV,
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Site amplification is dependent only upon Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z2pt5'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        return

    def GMM_at_VS30_v4(self, event_type, region, saturation_region, Rrup, M, period, \
            VS30, Z2p5, basin=None, hypocentre_depth=None):
        """
        """

        # SUBDUCTION or INTERFACE
        subduction = hypocentre_depth is not None

        # coefficients
        # TODO: input as CoeffsTable class
        coeff = pd.read_csv("Table_E1_Interface_Coefficients_051920.csv", index_col=0)
        coeff_pga = coeff.loc[0]
        if period == -1: # PGV
            coeff = coeff.loc[-1]
        elif period == 0: # PGA
            coeff = coeff_pga
        else:
            coeff = coeff.loc[period]

        # Mb
        Mb = 7.6 if subduction else 7.9
        mb_regions = ("Aleutian", "Alaska", "Cascadia", "CAM_S", "CAM_N", \
            "Japan_Pac", "Japan_Phi", "SA_N", "SA_S", "Taiwan_W", "Taiwan_E")
        if saturation_region in mb_regions:
            i = mb_regions.index(saturation_region)
            if subduction:
                Mb = (7.98, 7.2, 7.2, 7.6, 7.4, 7.65, 7.55, 7.3, 7.25, 7.7, 7.7)[i]
            else:
                Mb = (8, 8.6, 7.7, 7.4, 7.4, 8.5, 7.7, 8.5, 8.6, 7.1, 7.1)[i]

        # c0
        if region == "global":
            c0_col = "Global_c0"
        elif subduction and not (region == "Alaska" or region == "SA"):
            # Alaska region be paired with another saturation region?
            c0_col = region + "_c0"
        else:
            c0_col = saturation_region + "_c0"
        c0 = coeff[c0_col]
        c0_pga = coeff_pga[c0_col]

        # magnitude scaling
        m_diff = M - Mb
        if m_diff > 0:
            Fm = coeff.c6 * m_diff
            Fm_pga = coeff_pga.c6 * m_diff
        else:
            Fm = coeff.c4 * m_diff + coeff.c5 * m_diff ** 2
            Fm_pga = coeff_pga.c4 * m_diff + coeff_pga.c5 * m_diff ** 2

        # path term
        if subduction:
            if M <= Mb:
                m = (math.log10(35) - math.log10(3.12)) / (Mb - 4)
                h = 10 ** (m * m_diff + math.log10(35))
            else:
                h = 35
        else:
            h = 10 ** (-0.82 + 0.252 * M)
        R = math.sqrt(Rrup ** 2 + h ** 2)
        # log(R / Rref)
        R_Rref = math.log(R / math.sqrt(1 + h ** 2))

        # isolate regional anelastic coefficient, a0
        if region == "global" or (region == "Cascadia" and not subduction):
            a0 = coeff.Global_a0
            a0_pga = coeff_pga.Global_a0
        else:
            a0 = coeff[region + "_a0"]
            a0_pga = coeff_pga[region + "_a0"]
            # this shouldn't happen with given dataset
            if np.isnan(a0):
                a0 = coeff.Global_a0
            if np.isnan(a0_pga):
                a0_pga = coeff_pga.Global_a0

        b4 = 0.1
        Fp = coeff.c1 * math.log(R) + (b4 * M) * R_Rref + a0 * R
        Fp_pga = coeff_pga.c1 * math.log(R) + (b4 * M) * R_Rref + a0_pga * R

        # source depth scaling
        if subduction:
            Fd = self._depth_scaling(hypocentre_depth, coeff)
            Fd_pga = self._depth_scaling(hypocentre_depth, coeff_pga)

        # linear site term
        Flin = self._linear_amplification(coeff, region, VS30)

        # non-linear site term
        if subduction:
            PGAr = math.exp(Fp_pga + Fm_pga + c0_pga + Fd_pga)
        else:
            PGAr = math.exp(Fp_pga + Fm_pga + c0_pga)
        f3 = 0.05
        Vb = 200
        Vref_Fnl = 760

        if period >= 3:
            Fnl = 0
        else:
            Fnl = coeff.f4 * (math.exp(coeff.f5 * (min(VS30, Vref_Fnl) - Vb)) \
                - math.exp(coeff.f5 * (Vref_Fnl - Vb)))
            Fnl *= math.log((PGAr + f3) / f3)

        # basin term
        Fb = self._basin_term(Z2p5, region, VS30, coeff, basin)

        # mu as sum
        mu = Fp + Fnl + Fb + Flin + Fm + c0
        if subduction:
            mu += Fd
        return mu

    def _depth_scaling(self, hypocentre_depth, coeff):
        if hypocentre_depth >= coeff["db (km)"]:
            return coeff.d
        elif hypocentre_depth <= 20:
            return coeff.m * (20 - coeff["db (km)"]) + coeff.d
        else:
            return coeff.m * (hypocentre_depth - coeff["db (km)"]) + coeff.d

    def _linear_amplification(self, coeff, region, VS30):
        # site coefficients
        V1 = 270
        V2 = coeff["V2"]
        Vref = 760
        if region == "global" or region == "CAM":
            s2 = coeff.Global_s2
            s1 = s2
        elif region == "Taiwan" or region == "Japan":
            s2 = coeff[region + "_s2"]
            s1 = coeff[region + "_s1"]
        else:
            s2 = coeff[region + "_s2"]
            s1 = s2

        # linear site term
        if VS30 <= V1:
            return s1 * math.log(VS30 / V1) + s2 * math.log(V1 / Vref)
        elif VS30 <= V2:
            return s2 * math.log(VS30 / Vref)
        else:
            return s2 * math.log(V2 / Vref)

    def _basin_term(self, Z2p5, region, VS30, coeff, basin):
        if Z2p5 == "default" or Z2p5 <= 0 \
                or region not in ["Japan", "Cascadia"]:
            return 0

        if region == "Cascadia":
            theta0 = 3.94
            theta1 = -0.42
            vmu = 200
            vsig = 0.2
            e1 = coeff.C_e1
            e2 = coeff.C_e2
            e3 = coeff.C_e3

            if basin == 0:
                e3 += coeff.del_None
                e2 += coeff.del_None
            elif basin == 1:
                e3 += coeff.del_Seattle
                e2 += coeff.del_Seattle

        elif region == "Japan":
            theta0 = 3.05
            theta1 = -0.8
            vmu = 500
            vsig = 0.33
            e1 = coeff.J_e1
            e2 = coeff.J_e2
            e3 = coeff.J_e3

        Z2p5_pred = 10 ** (theta0 + theta1 * (1 + math.erf((math.log10(VS30) - math.log10(vmu)) / (vsig * math.sqrt(2)))))
        del_Z2p5 = math.log(Z2p5) - math.log(Z2p5_pred)

        if del_Z2p5 <= (e1 / e3):
            return e1
        elif del_Z2p5 >= (e2 / e3):
            return e2
        else:
            return e3 * del_Z2p5

    # sa_damping required but significance of 5 unknown
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    Global_c0 Alaska_c0    Aleutian_c0  Cascadia_c0 CAM_N_c0     CAM_S_c0    Japan_Pac_c0 Japan_Phi_c0 SA_N_c0     SA_S_c0      Taiwan_E_c0  Taiwan_W_c0  c1     Global_a0 Alaska_a0 CAM_a0    Japan_a0  SA_a0     Taiwan_a0 c4     c5    c6      V2  Japan_s1 Taiwan_s1 Global_s2 Alaska_s2 Cascadia_s2 Japan_s2 SA_s2  Taiwan_s2 f4       f5       J_e1   J_e2   J_e3  C_e1   C_e2   C_e3   del_None del_Seattle Tau   phi21 phi22  phi2V  VM phi2S2S,0 a1    phi2SS,1 phi2SS,2 a2
    pgv    8.097     9.283796298  8.374796298  7.728       7.046899908  7.046899908 8.772125851  7.579125851  8.528671414 8.679671414  7.559846279  7.559846279 -1.661 -0.00395  -0.00404  -0.00153  -0.00239  -0.000311 -0.00514   1.336 -0.039 1.844  850 -0.738   -0.454    -0.601    -1.031    -0.671      -0.738   -0.681 -0.59     -0.31763 -0.0052  -0.137  0.137  0.091 0      0.115  0.068 -0.115    0           0.477 0.348 0.288 -0.179 423 0.142     0.047 0.153    0.166    0.011
    pga    4.082     4.458796298  3.652796298  3.856       2.875899908  2.875899908 5.373125851  4.309125851  5.064671414 5.198671414  3.032846279  3.032846279 -1.662 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.246 -0.021 1.128 1350 -0.586   -0.44     -0.498    -0.785    -0.572      -0.586   -0.333 -0.44     -0.44169 -0.0052   0      0      1     0      0      1      0        0           0.48  0.396 0.565 -0.18  423 0.221     0.093 0.149    0.327    0.068
    0.01   3.714     4.094796298  3.288796298  3.488       2.564899908  2.564899908 5.022125851  3.901125851  4.673671414 4.807671414  2.636846279  2.636846279 -1.587 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.246 -0.021 1.128 1300 -0.604   -0.44     -0.498    -0.803    -0.571      -0.604   -0.333 -0.44     -0.4859  -0.0052   0      0      1     0      0      1      0        0           0.476 0.397 0.56  -0.18  423 0.223     0.098 0.148    0.294    0.071
    0.02   3.762     4.132796298  3.338796298  3.536       2.636899908  2.636899908 5.066125851  3.935125851  4.694671414 4.827671414  2.698846279  2.698846279 -1.593 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.227 -0.021 1.128 1225 -0.593   -0.458    -0.478    -0.785    -0.575      -0.593   -0.345 -0.458    -0.4859  -0.00518  0      0      1     0      0      1      0        0           0.482 0.401 0.563 -0.181 423 0.227     0.105 0.149    0.294    0.073
    0.025  3.859     4.246796298  3.392796298  3.633       2.731899908  2.731899908 5.140125851  4.094125851  4.779671414 4.911671414  2.800846279  2.800846279 -1.607 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.221 -0.021 1.128 1200 -0.569   -0.454    -0.464    -0.745    -0.573      -0.579   -0.362 -0.459    -0.4859  -0.00515  0      0      1     0      0      1      0        0           0.49  0.405 0.575 -0.183 423 0.231     0.12  0.15     0.31     0.076
    0.03   4.014     4.386796298  3.535796298  3.788       2.890899908  2.890899908 5.317125851  4.278125851  4.935671414 5.066671414  2.926846279  2.926846279 -1.63  -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.215 -0.021 1.128 1200 -0.539   -0.455    -0.446    -0.69     -0.565      -0.561   -0.38  -0.464    -0.4908  -0.00511  0      0      1     0      0      1      0        0           0.5   0.413 0.589 -0.188 423 0.239     0.145 0.153    0.313    0.077
    0.04   4.223     4.553796298  3.747796298  3.997       3.075899908  3.075899908 5.564125851  4.531125851  5.182671414 5.312671414  3.069846279  3.069846279 -1.657 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.207 -0.021 1.128 1200 -0.468   -0.453    -0.431    -0.636    -0.546      -0.508   -0.403 -0.466    -0.49569 -0.00505  0      0      1     0      0      1      0        0           0.515 0.439 0.616 -0.205 423 0.261     0.177 0.159    0.322    0.08
    0.05   4.456     4.745796298  3.959796298  4.23        3.287899908  3.287899908 5.843125851  4.816125851  5.457671414 5.586671414  3.236846279  3.236846279 -1.687 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.201 -0.021 1.128 1225 -0.403   -0.452    -0.42     -0.594    -0.519      -0.461   -0.427 -0.468    -0.49823 -0.00497  0      0      1     0.1   -0.1   -0.063 -0.05     0           0.528 0.473 0.653 -0.23  423 0.285     0.2   0.167    0.33     0.077
    0.075  4.742     4.972796298  4.231796298  4.516       3.560899908  3.560899908 6.146125851  5.126125851  5.788671414 5.917671414  3.446846279  3.446846279 -1.715 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.19  -0.021 1.128 1350 -0.325   -0.456    -0.442    -0.586    -0.497      -0.452   -0.458 -0.473    -0.49724 -0.00489  0.05  -0.043 -0.025 0.3   -0.34  -0.2   -0.075    0.078       0.53  0.529 0.722 -0.262 423 0.339     0.205 0.184    0.299    0.063
    0.1    4.952     5.160796298  4.471796298  4.726       3.788899908  3.788899908 6.346125851  5.333125851  5.998671414 6.126671414  3.643846279  3.643846279 -1.737 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.182 -0.021 1.128 1450 -0.264   -0.468    -0.485    -0.629    -0.486      -0.498   -0.49  -0.482    -0.49471 -0.00478  0.1   -0.085 -0.05  0.333 -0.377 -0.222 -0.081    0.075       0.524 0.517 0.712 -0.239 423 0.347     0.185 0.176    0.31     0.061
    0.15   5.08      5.285796298  4.665796298  4.848       3.945899908  3.945899908 6.425125851  5.420125851  6.103671414 6.230671414  3.798846279  3.798846279 -1.745 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.171 -0.021 1.162 1500 -0.25    -0.484    -0.546    -0.729    -0.499      -0.568   -0.536 -0.499    -0.48583 -0.0046   0.164 -0.139 -0.082 0.29  -0.29  -0.193 -0.091    0.064       0.51  0.457 0.644 -0.185 423 0.313     0.123 0.164    0.307    0.076
    0.2    5.035     5.277796298  4.661796298  4.798       3.943899908  3.943899908 6.288125851  5.289125851  6.013671414 6.140671414  3.827846279  3.827846279 -1.732 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.163 -0.021 1.187 1425 -0.288   -0.498    -0.612    -0.867    -0.533      -0.667   -0.584 -0.522    -0.47383 -0.00434  0.164 -0.139 -0.082 0.177 -0.192 -0.148 -0.092    0.075       0.501 0.432 0.64  -0.138 423 0.277     0.11  0.163    0.301    0.07
    0.25   4.859     5.154796298  4.503796298  4.618       3.800899908  3.800899908 5.972125851  4.979125851  5.849671414 5.974671414  3.765846279  3.765846279 -1.696 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.156 -0.021 1.204 1350 -0.36    -0.511    -0.688    -1.011    -0.592      -0.781   -0.654 -0.555    -0.47696 -0.00402  0.08  -0.08  -0.053 0.1   -0.035 -0.054  0        0           0.492 0.45  0.633 -0.185 423 0.26      0.119 0.169    0.233    0.077
    0.3    4.583     4.910796298  4.276796298  4.34        3.491899908  3.491899908 5.582125851  4.592125851  5.603671414 5.728671414  3.602846279  3.602846279 -1.643 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.151 -0.021 1.215 1250 -0.455   -0.514    -0.748    -1.133    -0.681      -0.867   -0.725 -0.596    -0.4845  -0.0037   0      0      1     0      0      1      0        0           0.492 0.436 0.584 -0.158 423 0.254     0.092 0.159    0.22     0.065
    0.4    4.18      4.548796298  3.919796298  3.935       3.128899908  3.128899908 5.091125851  4.089125851  5.151671414 5.277671414  3.343846279  3.343846279 -1.58  -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.143 -0.022 1.227 1150 -0.617   -0.51     -0.802    -1.238    -0.772      -0.947   -0.801 -0.643    -0.48105 -0.00342 -0.13   0.113  0.087 0      0.05   0.2    0        0           0.492 0.433 0.556 -0.19  423 0.23      0.044 0.158    0.222    0.064
    0.5    3.752     4.168796298  3.486796298  3.505       2.640899908  2.640899908 4.680125851  3.571125851  4.719671414 4.848671414  3.028846279  3.028846279 -1.519 -0.00657  -0.00541  -0.00387  -0.00862  -0.00397  -0.00787   1.143 -0.023 1.234 1025 -0.757   -0.506    -0.845    -1.321    -0.838      -1.003   -0.863 -0.689    -0.46492 -0.00322 -0.2    0.176  0.118 0      0.1    0.2    0        0           0.492 0.428 0.51  -0.186 423 0.225     0.038 0.16     0.243    0.044
    0.75   3.085     3.510796298  2.710796298  2.837       1.987899908  1.987899908 3.906125851  2.844125851  3.995671414 4.129671414  2.499846279  2.499846279 -1.44  -0.00635  -0.00478  -0.00342  -0.00763  -0.00351  -0.0068    1.217 -0.026 1.24   900 -0.966   -0.5      -0.911    -1.383    -0.922      -1.052   -0.942 -0.745    -0.43439 -0.00312 -0.401  0.284  0.167 0      0.2    0.125 -0.2      0.012       0.492 0.448 0.471 -0.177 422 0.218     0.04  0.175    0.241    0.04
    1.0    2.644     3.067796298  2.238796298  2.396       1.553899908  1.553899908 3.481125851  2.371125851  3.512671414 3.653671414  2.140846279  2.140846279 -1.419 -0.0058   -0.00415  -0.00297  -0.00663  -0.00305  -0.00605   1.27  -0.028 1.24   800 -0.986   -0.49     -0.926    -1.414    -0.932      -1.028   -0.96  -0.777    -0.38484 -0.0031  -0.488  0.346  0.203 0      0.245  0.153 -0.245    0.037       0.492 0.43  0.43  -0.166 422 0.227     0.015 0.195    0.195    0.043
    1.5    2.046     2.513796298  1.451796298  1.799       0.990899908  0.990899908 2.870125851  1.779125851  2.875671414 3.023671414  1.645846279  1.645846279 -1.4   -0.00505  -0.00342  -0.00245  -0.00546  -0.00252  -0.00498   1.344 -0.031 1.237  760 -0.966   -0.486    -0.888    -1.43     -0.814      -0.971   -0.942 -0.79     -0.32318 -0.0031  -0.578  0.48   0.24  0      0.32   0.2   -0.32     0.064       0.492 0.406 0.406 -0.111 422 0.244    -0.047 0.204    0.204   -0.034
    2.0    1.556     2.061796298  0.906796298  1.31        0.534899908  0.534899908 2.507125851  1.293125851  2.327671414 2.481671414  1.217846279  1.217846279 -1.391 -0.00429  -0.0029   -0.00208  -0.00463  -0.00214  -0.00423   1.396 -0.034 1.232  760 -0.901   -0.475    -0.808    -1.421    -0.725      -0.901   -0.891 -0.765    -0.26577 -0.0031  -0.645  0.579  0.254 0      0.37   0.239 -0.28     0.14        0.492 0.393 0.393  0     422 0.231    -0.036 0.196    0.196   -0.036
    2.5    1.167     1.709796298  0.392796298  0.922       0.186899908  0.186899908 2.160125851  0.895125851  1.950671414 2.111671414  0.871846279  0.871846279 -1.394 -0.00369  -0.0025   -0.00179  -0.00399  -0.00184  -0.00364   1.437 -0.036 1.227  760 -0.822   -0.453    -0.743    -1.391    -0.632      -0.822   -0.842 -0.724    -0.21236 -0.0031  -0.678  0.609  0.267 0      0.4    0.264 -0.313    0.19        0.492 0.381 0.381  0     421 0.222    -0.025 0.169    0.169   -0.029
    3.0    0.92      1.456796298  0.099796298  0.675      -0.087100092 -0.087100092 1.969125851  0.607125851  1.766671414 1.932671414  0.596846279  0.596846279 -1.416 -0.00321  -0.00217  -0.00156  -0.00347  -0.0016   -0.00316   1.47  -0.038 1.223  760 -0.751   -0.428    -0.669    -1.343    -0.57       -0.751   -0.787 -0.675     0       -0.0031  -0.772  0.635  0.265 0      0.43   0.287 -0.355    0.165       0.492 0.367 0.367  0     419 0.199    -0.03  0.177    0.177   -0.011
    4.0    0.595     1.207796298 -0.356203702  0.352      -0.353100092 -0.353100092 1.675125851  0.303125851  1.524671414 1.698671414  0.268846279  0.268846279 -1.452 -0.00244  -0.00165  -0.00118  -0.00264  -0.00122  -0.00241   1.523 -0.044 1.216  760 -0.68    -0.396    -0.585    -1.297    -0.489      -0.68    -0.706 -0.613     0       -0.0031  -0.699  0.709  0.259 0      0.44   0.303 -0.417    0.163       0.492 0.33  0.33   0     416 0.191    -0.042 0.158    0.158    0.033
    5.0    0.465     1.131796298 -0.601203702  0.223      -0.491100092 -0.491100092 1.601125851  0.183125851  1.483671414 1.665671414  0.014846279  0.014846279 -1.504 -0.0016   -0.00125  -0.000895 -0.002    -0.000919 -0.00182   1.564 -0.048 1.21   760 -0.592   -0.353    -0.506    -1.233    -0.421      -0.592   -0.621 -0.536     0       -0.0031  -0.642  0.63   0.215 0      0.45   0.321 -0.45     0.132       0.492 0.298 0.298  0     415 0.181     0.005 0.132    0.132    0.014                                                                    
    7.5    0.078     0.758796298 -1.137203702 -0.162      -0.837100092 -0.837100092 1.270125851 -0.143874149  1.175671414 1.366671414 -0.446153721 -0.446153721 -1.569 -0.000766 -0.000519 -0.000371 -0.000828 -0.000382 -0.000755  1.638 -0.059 1.2    760 -0.494   -0.311    -0.418    -1.147    -0.357      -0.52    -0.52  -0.444     0       -0.0031  -0.524  0.306  0.175 0      0.406  0.312 -0.35     0.15        0.492 0.254 0.254  0     419 0.181    -0.016 0.113    0.113    0.016
    10.0   0.046     0.708796298 -1.290203702 -0.193      -0.864100092 -0.864100092 1.364125851 -0.195874149  1.271671414 1.462671414 -0.473153721 -0.473153721 -1.676  0         0         0         0         0         0         1.69  -0.067 1.194  760 -0.395   -0.261    -0.321    -1.06    -0.302       -0.395   -0.42  -0.352     0       -0.0031  -0.327  0.182  0.121 0      0.345  0.265 -0.331    0.117       0.492 0.231 0.231  0     427 0.181     0.04  0.11     0.11     0.017
    """)



class ParkerEtAl2020SSlab(ParkerEtAl2020SInter):

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        return

    coeff = pd.read_csv("Table_E2_Slab_Coefficients_060720.csv", index_col=0, skiprows=1)

    b4 = 0.1
    Fp = coeff.c1 * math.log(R) + (b4 * M) * R_Rref + a0 * R
    Fp_pga = coeff_pga.c1 * math.log(R) + (b4 * M) * R_Rref + a0_pga * R

    # source depth scaling
    if subduction:
        Fd = _depth_scaling(hypocentre_depth, coeff)
        Fd_pga = _depth_scaling(hypocentre_depth, coeff_pga)

    # linear site term
    Flin = _linear_amplification(coeff, region, VS30)

    # non-linear site term
    if subduction:
        PGAr = math.exp(Fp_pga + Fm_pga + c0_pga + Fd_pga)
    else:
        PGAr = math.exp(Fp_pga + Fm_pga + c0_pga)
    f3 = 0.05
    Vb = 200
    Vref_Fnl = 760

    if period >= 3:
        Fnl = 0
    else:
        Fnl = coeff.f4 * (math.exp(coeff.f5 * (min(VS30, Vref_Fnl) - Vb)) \
            - math.exp(coeff.f5 * (Vref_Fnl - Vb)))
        Fnl *= math.log((PGAr + f3) / f3)

    # basin term
    Fb = _basin_term(Z2p5, region, VS30, coeff, basin)

    # mu as sum
    mu = Fp + Fnl + Fb + Flin + Fm + c0
    if subduction:
        mu += Fd
    return mu


def _depth_scaling(hypocentre_depth, coeff):
    if hypocentre_depth >= coeff["db (km)"]:
        return coeff.d
    elif hypocentre_depth <= 20:
        return coeff.m * (20 - coeff["db (km)"]) + coeff.d
    else:
        return coeff.m * (hypocentre_depth - coeff["db (km)"]) + coeff.d


def _linear_amplification(coeff, region, VS30):
    # site coefficients
    V1 = 270
    V2 = coeff["V2"]
    Vref = 760
    if region == "global" or region == "CAM":
        s2 = coeff.Global_s2
        s1 = s2
    elif region == "Taiwan" or region == "Japan":
        s2 = coeff[region + "_s2"]
        s1 = coeff[region + "_s1"]
    else:
        s2 = coeff[region + "_s2"]
        s1 = s2

    # linear site term
    if VS30 <= V1:
        return s1 * math.log(VS30 / V1) + s2 * math.log(V1 / Vref)
    elif VS30 <= V2:
        return s2 * math.log(VS30 / Vref)
    else:
        return s2 * math.log(V2 / Vref)


def _basin_term(Z2p5, region, VS30, coeff, basin):
    if Z2p5 == "default" or Z2p5 <= 0 \
            or region not in ["Japan", "Cascadia"]:
        return 0

    if region == "Cascadia":
        theta0 = 3.94
        theta1 = -0.42
        vmu = 200
        vsig = 0.2
        e1 = coeff.C_e1
        e2 = coeff.C_e2
        e3 = coeff.C_e3

        if basin == 0:
            e3 += coeff.del_None
            e2 += coeff.del_None
        elif basin == 1:
            e3 += coeff.del_Seattle
            e2 += coeff.del_Seattle

    elif region == "Japan":
        theta0 = 3.05
        theta1 = -0.8
        vmu = 500
        vsig = 0.33
        e1 = coeff.J_e1
        e2 = coeff.J_e2
        e3 = coeff.J_e3

    Z2p5_pred = 10 ** (theta0 + theta1 * (1 + math.erf((math.log10(VS30) - math.log10(vmu)) / (vsig * math.sqrt(2)))))
    del_Z2p5 = math.log(Z2p5) - math.log(Z2p5_pred)

    if del_Z2p5 <= (e1 / e3):
        return e1
    elif del_Z2p5 >= (e2 / e3):
        return e2
    else:
        return e3 * del_Z2p5


def Aleatory_Function(period, Rrup, VS30):
    """
    Generate tau, phi, and total sigma computed from both
    total and partitioned phi models.
    """

    # coefficients
    coeff = pd.read_csv("Table_E3_Aleatory_Coefficients.csv", index_col=0)
    if period == -1: # PGV
        coeff = coeff.loc[-1]
    elif period == 0: # PGA
        coeff = coeff.loc[0]
    else:
        coeff = coeff.loc[period]

    # define period-independent coefficients for phi models
    V1 = 200
    V2 = 500
    R1 = 200
    R2 = 500
    R3 = 200
    R4 = 500
    R5 = 500
    R6 = 800

    # total Phi
    PhiRV = np.zeros(len(VS30))

    for i in range(len(VS30)):
        if Rrup[i] <= R1:
            PhiRV[i] = coeff["ɸ21"]
        elif Rrup[i] >= R2:
            PhiRV[i] = coeff["ɸ22"]
        else:
            PhiRV[i] = ((coeff["ɸ22"] - coeff["ɸ21"]) \
                / (math.log(R2) - math.log(R1))) \
                * (math.log(Rrup[i]) - math.log(R1)) + coeff["ɸ21"]

        if VS30[i] <= V1:
            PhiRV[i] += coeff["ɸ2V"] * (math.log(R2 / max(R1, min(R2, Rrup[i]))) \
                / math.log(R2 / R1))
        elif VS30[i] < V2:
            PhiRV += coeff["ɸ2V"] * ((math.log(V2 / min(V2, VS30[i]))) \
                / (math.log(V2 / V1))) \
                * (math.log(R2 / max(R1, min(R2, Rrup[i]))) \
                / (math.log(R2 / R1)))

    Phi_tot = np.sqrt(PhiRV)  

    # partitioned Phi
    PhiS2SV = np.repeat(coeff["ɸ2S2S,0"], len(VS30))
    PhiSSR = np.zeros_like(PhiRV)
    PhiSSV = np.repeat(coeff.a2, len(VS30))

    for i in range(len(VS30)):
        if VS30[i] <= V1:
            PhiS2SV[i] += (coeff.a1 * math.log(V1 / coeff.VM)) \
                * (math.log(R4 / max(R3, min(R4, Rrup[i]))) / math.log(R4 / R3))
            PhiSSV[i] *= math.log(V1 / coeff.VM) \
                * (math.log(R4 / max(R3, min(R4, Rrup[i]))) / math.log(R4 / R3))
        elif VS30[i] >= V2:
            PhiS2SV[i] += (coeff.a1 * math.log(V2 / coeff.VM))
            PhiSSV[i] *= math.log(V2 / coeff.VM)
        elif VS30[i] > V1 and VS30[i] < coeff.VM:
            PhiS2SV[i] += (coeff["a1"] * math.log(VS30[i] / coeff.VM)) \
                * (math.log(R4 / max(R3, min(R4, Rrup[i]))) / math.log(R4 / R3))
            PhiSSV[i] *= math.log(VS30[i] / coeff.VM) \
                * (math.log(R4 / max(R3, min(R4, Rrup[i]))) / math.log(R4 / R3))
        elif VS30[i] >= coeff.VM and VS30[i] < V2:
            PhiS2SV[i] += (coeff.a1 * math.log(VS30[i] / coeff.VM))
            PhiSSV[i] *= math.log(VS30[i] / coeff.VM)

        if Rrup[i] <= R5:
            PhiSSR[i] = coeff["ɸ2SS,1"]
        elif Rrup[i] >= R6:
            PhiSSR[i] = coeff["ɸ2SS,2"]
        else:
            PhiSSR[i] = ((coeff["ɸ2SS,2"] - coeff["ɸ2SS,1"]) \
                / (math.log(R6) - math.log(R5))) \
                * (math.log(Rrup[i]) - math.log(R5)) + coeff["ɸ2SS,1"]

    PhiC = np.sqrt(PhiS2SV + PhiSSR + PhiSSV)

    # define output matrix
    return {"Tau": coeff.Tau,
            "Phi_total": Phi_tot,
            "Phi_SS": np.sqrt(PhiSSR + PhiSSV),
            "PhiS2S": np.sqrt(PhiS2SV),
            "Phi_partitioned": PhiC,
            "Sigma_total": np.sqrt(coeff.Tau ** 2 + Phi_tot ** 2),
            "Sigma_partitioned": np.sqrt(coeff.Tau ** 2 + PhiC ** 2)
        }
