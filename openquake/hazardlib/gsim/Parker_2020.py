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

import pandas as pd


def GMM_at_VS30_IF_v4(event_type, region, saturation_region, Rrup, M, period, \
        VS30, Z2p5, basin):
    """
    
    """

    # SUBDUCTION_INTERFACE only

    # coefficients
    coeff = read.csv("Table_E1_Interface_Coefficients_051920.csv", index_col=0)
    coeff_pga = coeff.loc[0]
    if period == -1: # PGV
        coeff = coeff.loc[-1]
    else if period == 0: # PGA
        coeff = coeff_pga
    else:
        coeff = coeff.loc[period]

    # Mb
    if saturation_region == "global":
        Mb = 7.9
    else:
        Mb = {"Aleutian": 8, "Alaska": 8.6, "-999": np.nan, \
            "Cascadia": 7.7, "CAM_S": 7.4, "CAM_N": 7.4, "Japan_Pac": 8.5, \
            "Japan_Phi": 7.7, "New_Zealand_N": np.nan, \
            "New_Zealand_S": np.nan, "SA_N": 8.5, "SA_S": 8.6, \
            "Taiwan_W": 7.1, "Taiwan_E": 7.1}[saturation_region]
        if np.isnan(Mb):
            Mb = 7.9

    # c0
    if region == "global":
        c0 = coeff.Global_c0
        c0_pga = coeff_pga.Global_c0
    else:
        c0 = coeff[saturation_region + "_c0"]
        c0_pga = coeff_pga[saturation_region + "_c0"]

    # path term
    h = 10 ** (-0.82 + 0.252 * M)
    R = math.sqrt(Rrup ** 2 + h ** 2)
    # log(R / Rref)
    R_Rref = math.log(R / math.sqrt(1 + h ** 2))

    # isolate regional anelastic coefficient, a0
    if region == "global" or region == "Cascadia":
        a0 = coeff.Global_a0
        a0_pga = coeff_pga.Global_a0
    else:
        a0 = coeff[region + "_a0"]
        a0 = coeff_pga[region + "_a0"]
        # this shouldn't happen with given dataset
        if np.isnan(a0):
            a0 = coeff.Global_a0
        if np.isnan(a0_pga):
            a0_pga = coeff_pga.Global_a0

    Fp = coeff.c1 * math.log(R) + (coeff.b4 * M) * R_Rref + a0 * R
    Fp_pga = coeff_pga.c1 * math.log(R) + (coeff_pga.b4 * M) * R_Ref + a0_pga * R

    # magnitude scaling
    m_diff = M - Mb
    if m_diff > 0:
        Fm = coeff.c6 * m_diff
        Fm_pga = coeff_pga.c6 * m_diff
    else:
        Fm = coeff.c4 * m_diff + coeff.c5 * m_diff ** 2
        Fm_pga = coeff_pga.c4 * m_diff + coeff_pga.c5 * m_diff ** 2

    ## linear site amplification

    # site coefficients
    V1 = coeff["V1 (m/s)"]
    V2 = coeff["V2 (m/s)"]
    Vref = coeff["Vref (m/s)"]
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
        Flin = s1 * math.log(VS30 / V1) + s2 * math.log(V1 / Vref)
    elif VS30 <= V2:
        Flin = s2 * math.log(VS30 / Vref)
    else:
        Flin = s2 * math.log(V2 / Vref)

    # non-linear site term
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
    Fb = _basin_term(Z2p5, region, VS30, coeff)

    # mu as sum
    mu = Fp + Fnl + Fb + Flin + Fm + c0
    return mu


def _basin_term(Z2p5, region, VS30, coeff):
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

    # TODO: find out what erf is
    Z2p5_pred = 10 ** (theta0 + theta1 * (1 + erf((math.log10(VS30) - math.log10(vmu)) / (vsig * math.sqrt(2)))))
    del_Z2p5 = math.log(Z2p5) - math.log(Z2p5_pred)

    if del_Z2p5 <= (e1 / e3):
        return e1
    elif del_Z2p5 >= (e2 / e3):
        return e2
    else:
        return e3 * del_Z2p5
