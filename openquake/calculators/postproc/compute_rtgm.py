# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Module to compute the Risk Targeted Ground Motion by using the
rtgmpy module from the USGS. The only calls performed are

1. trgm_haz = rtgmpy.GroundMotionHazard.from_dict(hazdic)  # from hazard rates
2. rtgm.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')  # returns RTGM

Useful abbreviations:

- RTGM: Risk Targeted Ground Motion (for geometric mean)
- RTGM_max: Risk Targeted Ground Motion (for maximum component)
- MCE: Maximum Considered Earthquake
- ProbMCE: Probabilistic Maximum Considered Earthquake (UHGM for PGA)
- IMT: the list of IMTs as normalized strings
- UHGM: Uniform Hazard Spectra
- RiskCoeff: RTGM / UHGM_2475y
- DLL: Deterministic Lower Limit
- PGA_G: PGA for Geometric Mean (no Risk Targeted)
- PGA: PGA for Maximum Component
"""
import io
import logging
import json
import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
from scipy import interpolate
from scipy.interpolate import RegularGridInterpolator
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
try:
    from PIL import Image
except ImportError:
    Image = None
from openquake.baselib import hdf5
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.calculators import postproc
from openquake.calculators.extract import get_info

DLL_df = pd.read_csv(io.StringIO('''\
imt,A,B,BC,C,CD,D,DE,E
PGA0,0.50,0.57,0.66,0.73,0.74,0.69,0.61,0.55
SA(0.01),0.50,0.57,0.66,0.73,0.75,0.70,0.62,0.55
SA(0.02),0.52,0.58,0.68,0.74,0.75,0.70,0.62,0.55
SA(0.03),0.60,0.66,0.75,0.79,0.78,0.70,0.62,0.55
SA(0.05),0.81,0.89,0.95,0.96,0.89,0.76,0.62,0.55
SA(0.075),1.04,1.14,1.21,1.19,1.08,0.90,0.71,0.62
SA(0.1),1.12,1.25,1.37,1.37,1.24,1.04,0.82,0.72
SA(0.15),1.12,1.29,1.53,1.61,1.50,1.27,1.00,0.87
SA(0.2),1.01,1.19,1.50,1.71,1.66,1.44,1.15,1.01
SA(0.25),0.90,1.07,1.40,1.71,1.77,1.58,1.30,1.15
SA(0.3),0.81,0.98,1.30,1.66,1.83,1.71,1.44,1.30
SA(0.4),0.69,0.83,1.14,1.53,1.82,1.80,1.61,1.48
SA(0.5),0.60,0.72,1.01,1.38,1.73,1.80,1.68,1.60
SA(0.75),0.46,0.54,0.76,1.07,1.41,1.57,1.60,1.59
SA(1.0),0.37,0.42,0.60,0.86,1.17,1.39,1.51,1.58
SA(1.5),0.26,0.29,0.41,0.60,0.84,1.09,1.35,1.54
SA(2.0),0.21,0.23,0.31,0.45,0.64,0.88,1.19,1.46
SA(3.0),0.15,0.17,0.21,0.31,0.45,0.63,0.89,1.11
SA(4.0),0.12,0.13,0.16,0.24,0.34,0.47,0.66,0.81
SA(5.0),0.10,0.11,0.13,0.19,0.26,0.36,0.49,0.61
SA(7.5),0.063,0.068,0.080,0.11,0.15,0.19,0.26,0.31
SA(10.0),0.042,0.045,0.052,0.069,0.089,0.11,0.14,0.17
PGA,0.37,0.43,0.50,0.55,0.56,0.53,0.46,0.42
'''), index_col='imt')

# hard-coded for year 1
# TODO: interpolate for vs30 != 760 and for different periods
# NOTE: for meanHCs_afe_RTGM and disaggr_by_src we want to display these
# three imts, that are mandatory in this context. For the plot of governing
# MCE we read imts from the imtls
IMTS = ['PGA', 'SA(0.2)', 'SA(1.0)']
D = DLL_df.BC.loc  # site class BC for vs30=760m/s
DLLs = [D[imt] for imt in IMTS]
assert DLLs == [0.5, 1.5, 0.6]


def norm_imt(imt):
    """
    Normalize the imt string to the USGS format, for instance SA(1.1) -> SA1P1
    """
    return imt.replace('(', '').replace(')', '').replace('.', 'P')


f1 = interpolate.interp1d([0.2, 1], [1.1, 1.3])
f2 = interpolate.interp1d([1, 5], [1.3, 1.5])
f3 = interpolate.interp1d([0.2, 1], [1.2, 1.25])
f4 = interpolate.interp1d([0.2, 1], [1.1, 1.3])


def _find_fact_maxC(T, code):
    # find the factor to convert to maximum component based on
    # ASCE7-16 and ASCE7-22
    if code == 'ASCE7-16':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.1
        elif T <= 1:
            fact_maxC = f1(T)
        elif T <= 5:
            fact_maxC = f2(T)
        else:
            fact_maxC = 1.5
    elif code == 'ASCE7-22':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.2
        elif T <= 1:
            fact_maxC = f3(T)
        elif T <= 10:
            fact_maxC = f4(T)
        else:
            fact_maxC = 1.5
    return fact_maxC


def calc_rtgm_df(rtgm_haz, facts, oq):
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    :param rtgm_haz: a dictionary containing the annual frequency losses
    :param facts: conversion factors from maximum component to geometric mean
    :param oq: OqParam instance
    """
    M = len(IMTS)
    assert len(oq.imtls) == M
    riskCoeff, RTGM, UHGM, RTGM_max, MCE = (
        np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M))
    results = rtgmpy.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')
    IMTs = []
    for m, imt in enumerate(IMTS):
        IMT = norm_imt(imt)
        IMTs.append(IMT)
        rtgmCalc = results['RTGM'][IMT]['rtgmCalc']
        RTGM_max[m] = rtgmCalc['rtgm']  # for maximum component
        UHGM[m] = rtgmCalc['uhgm'] / facts[m]  # for geometric mean
        riskCoeff[m] = rtgmCalc['riskCoeff']
        # note that RTGM_max is the ProbMCEr, while RTGM is used for the
        # identification of the sources as the hazard curves are in
        # geometric mean
        if IMT == 'PGA':
            RTGM[m] = UHGM[m]
            MCE[m] = RTGM[m]  # UHGM in terms of GM: MCEg
        else:
            RTGM[m] = rtgmCalc['rtgm'] / facts[m]  # for geometric mean
            MCE[m] = RTGM_max[m]
    dic = {'IMT': IMTs,
           'UHGM_2475yr-GM': UHGM,
           'RTGM': RTGM_max,
           'ProbMCE': MCE,
           'RiskCoeff': riskCoeff,
           'DLL': DLLs}
    return pd.DataFrame(dic)


def get_hazdic_facts(hcurves, imtls, invtime, sitecol):
    """
    Convert an array of mean hazard curves into a dictionary suitable
    for the rtgmpy library

    :param hcurves: array of PoEs of shape (N, M, L1)
    """
    new_imtls = {}
    facts = []
    for m, imt in enumerate(IMTS):
        T = from_string(imt).period
        fact = _find_fact_maxC(T, 'ASCE7-16')
        facts.append(fact)
        new_imtls[imt] = imtls[imt]*fact

    [site] = sitecol  # there must be a single site
    hazdic = {
        'site': {'name': 'site',
                 'lon': site.location.x,
                 'lat': site.location.y,
                 'Vs30': site.vs30},
        'hazCurves': {norm_imt(imt):
                      {'iml': new_imtls[imt],
                       # NB: minrate > 0 is needed to avoid NaNs in the RTGM
                       'afe': to_rates(hcurves[0, m], invtime, minrate=1E-12)}
                      for m, imt in enumerate(imtls) if imt in IMTS}}
    return hazdic, np.array(facts)


def get_deterministic(prob_mce, mag_dist_eps, sigma_by_src):
    """
    :returns: a dictionary imt -> deterministic MCE
    """
    srcs, imts, dets = [], [], []
    srcidx = {src: i for i, src in enumerate(sigma_by_src.source_id)}
    imtidx = {imt: i for i, imt in enumerate(sigma_by_src.imt)}
    mag_dist_eps_sig = []
    for src, imt, mag, dist, eps in mag_dist_eps:
        m = imtidx[imt]
        sig = sigma_by_src[srcidx[src], :, :, m]  # shape (Ma, D)
        sigma = RegularGridInterpolator((
            sigma_by_src.mag, sigma_by_src.dist), sig)((mag, dist))
        srcs.append(src)
        imts.append(imt)
        dets.append(prob_mce[m] * np.exp(sigma) / np.exp(eps*sigma))
        mag_dist_eps_sig.append((src, mag, dist, eps, sigma, imt))
    df = pd.DataFrame(dict(src=srcs, imt=imts, det=dets))
    det = df.groupby('imt').det.max()
    dt = [('src', hdf5.vstr), ('mag', float), ('dst', float),
          ('eps', float), ('sig', float), ('imt', hdf5.vstr)]
    return det.to_dict(), np.array(mag_dist_eps_sig, dt)


def get_mce_asce7(prob_mce, det_imt, DLLs, dstore, low=False):
    """
    :returns: a dictionary imt -> MCE
    :returns: a dictionary imt -> det MCE
    :returns: a dictionary all ASCE7 parameters
    """
    rtgm = dstore['rtgm']
    imts = rtgm['IMT']
    for i, imt in enumerate(imts):
        if imt == b'SA0P2':
            crs = rtgm['RiskCoeff'][i]
        elif imt == b'SA1P0':
            cr1 = rtgm['RiskCoeff'][i]

    det_mce = {}
    mce = {}  # imt -> MCE
    prob_mce_out = {}
    for i, imt in enumerate(det_imt):
        if low:
            det_mce[imt] = 'n.a.'
            mce[imt] = prob_mce[i] 
        else:
            det_mce[imt] = max(det_imt[imt], DLLs[i])
            mce[imt] = min(prob_mce[i], det_mce[imt]) 
        prob_mce_out[imt] = prob_mce[i]

    if mce['SA(0.2)'] < 0.25:
        SS_seismicity = "Low"
    elif mce['SA(0.2)'] < 0.5:
        SS_seismicity = "Moderate"
    elif mce['SA(0.2)'] < 1:
        SS_seismicity = "Moderately High"
    elif mce['SA(0.2)'] < 1.5:
        SS_seismicity = "High"
    else:
        SS_seismicity = "Very High"

    if mce['SA(1.0)'] < 0.1:
        S1_seismicity = "Low"
    elif mce['SA(1.0)'] < 0.2:
        S1_seismicity = "Moderate"
    elif mce['SA(1.0)'] < 0.4:
        S1_seismicity = "Moderately High"
    elif mce['SA(1.0)'] < 0.6:
        S1_seismicity = "High"
    else:
        S1_seismicity = "Very High"

    asce7 = {'PGA_2_50': prob_mce_out['PGA'],
             'PGA_84th': det_imt['PGA'],
             'PGA_det': det_mce['PGA'],
             'PGA': mce['PGA'],

             'SS_RT': prob_mce_out['SA(0.2)'],
             'CRS': crs,
             'SS_84th': det_imt['SA(0.2)'],
             'SS_det': det_mce['SA(0.2)'],
             'SS': mce['SA(0.2)'],
             'SS_seismicity': SS_seismicity,

             'S1_RT': prob_mce_out['SA(1.0)'],
             'CR1': cr1,
             'S1_84th': det_imt['SA(1.0)'],
             'S1_det': det_mce['SA(1.0)'],
             'S1': mce['SA(1.0)'],
             'S1_seismicity': S1_seismicity,
             }

    return prob_mce_out, mce, det_mce, asce7


def get_asce41(dstore, mce, facts, low=False):
    """
    :returns: a dictionary with the ASCE-41 parameters
    """
    fact = dict(zip(mce, facts))
    hmap = dstore["hmaps-stats"][0, 0]  # mean hazard on the site, shape (M, P)
    oq = dstore['oqparam']
    poes = oq.poes
    imts = list(oq.imtls)
    sa02 = imts.index('SA(0.2)')
    sa10 = imts.index('SA(1.0)')
    if int(oq.investigation_time) == 1:
        poe5_50 = poes.index(0.001025)
        poe20_50 = poes.index(0.004453)
    elif int(oq.investigation_time) == 50:
        poe5_50 = poes.index(0.05)
        poe20_50 = poes.index(0.2)

    BSE2N_Ss = mce['SA(0.2)']
    Ss_5_50 = hmap[sa02, poe5_50] * fact['SA(0.2)']
    BSE2E_Ss = min(Ss_5_50, BSE2N_Ss)
    BSE1N_Ss = 2/3 * BSE2N_Ss
    Ss_20_50 = hmap[sa02, poe20_50] * fact['SA(0.2)']
    BSE1E_Ss = min(Ss_20_50, BSE1N_Ss)

    BSE2N_S1 = mce['SA(1.0)']
    S1_5_50 = hmap[sa10, poe5_50] * fact['SA(1.0)']
    BSE2E_S1 = min(S1_5_50, BSE2N_S1)
    BSE1N_S1 = 2/3 * BSE2N_S1
    S1_20_50 = hmap[sa10, poe20_50] * fact['SA(1.0)']
    BSE1E_S1 = min(S1_20_50, BSE1N_S1)

    return {'BSE2N_Ss': BSE2N_Ss,
            'Ss_5_50': Ss_5_50,
            'BSE2E_Ss': BSE2E_Ss,
            'BSE1E_Ss': BSE1E_Ss,
            'Ss_20_50': Ss_20_50,
            'BSE1N_Ss': BSE1N_Ss,

            'BSE2N_S1': BSE2N_S1,
            'S1_5_50': S1_5_50,
            'BSE2E_S1': BSE2E_S1,
            'BSE1E_S1': BSE1E_S1,
            'S1_20_50': S1_20_50,
            'BSE1N_S1': BSE1N_S1}


def _get_label(imt):
    imtlab = imt if imt == 'PGA' else imt.replace(')', 's)')
    comp = 'Geom. mean' if imt == 'PGA' else 'Max. comp.'
    return imtlab + ' - ' + comp


def plot_meanHCs_afe_RTGM(imls, AFE, UHGM_RP, afe_RP, RTGM, afe_RTGM,
                          imts):
    plt.figure(figsize=(12, 9))
    plt.rcParams.update({'font.size': 16})
    colors = mpl.colormaps['viridis'].reversed()._resample(3)
    patterns = ['-', '--', ':']
    for m, imt in enumerate(imts):
        lab = _get_label(imt)
        plt.loglog(imls[m], AFE[m], color=colors(m), linestyle=patterns[m],
                   label=lab, linewidth=3, zorder=1)
        # plot the label only once but it must be at the end of the legend
        if imt == imts[-1]:
            plt.loglog([RTGM[m]], [afe_RTGM[m]], 'ko',
                       label='Probabilistic MCE',  linewidth=2,
                       markersize=10, zorder=3)
        else:
            plt.loglog([RTGM[m]], [afe_RTGM[m]], 'ko',
                       linewidth=2, markersize=10, zorder=3)
        plt.loglog([np.min(imls[m]), RTGM[m]], [afe_RTGM[m], afe_RTGM[m]],
                   'darkgray', linestyle='--', linewidth=1)
        plt.loglog([RTGM[m], RTGM[m]], [0, afe_RTGM[m]], 'darkgray',
                   linestyle='--', linewidth=1)

    plt.grid('both')
    plt.legend(fontsize=13)
    plt.xlabel('Acceleration (g)', fontsize=20)
    plt.ylabel('Annual frequency of exceedance', fontsize=20)
    plt.legend(loc="best", fontsize='16')
    plt.ylim([10E-6, 1.1])
    plt.xlim([0.01, 4])
    bio = io.BytesIO()
    plt.savefig(bio, format='png', bbox_inches='tight')
    plt.clf()
    return Image.open(bio)


def _find_afe_target(imls, afe, sa_target):
    # find the target afe (or poe) for a given acceleration
    if len(imls) != len(afe):
        afe.extend([1E-15] * (len(imls) - len(afe)))
    f = interpolate.interp1d(np.log(imls), np.log(afe))
    afe_target = np.exp(f(np.log(sa_target)))
    return afe_target


# NOTE: run pytest openquake/engine -k KOR to debug this
def disaggr_by_src(dstore, imtls):
    # get info : specific to disagg by src
    df = dstore['mean_rates_by_src'].to_dframe().set_index('src_id')
    grouped_m = df.groupby(['src_id', 'site_id', 'imt']).agg(
        {"value": list}).reset_index()
    # remove the sources that aren't contributing at all to the hazard
    mask = grouped_m.value.apply(lambda x: sum(x) > 0)
    gm = grouped_m[mask].reset_index()
    grouped_2 = gm.groupby(['imt', 'src_id']).agg(
        {"value": np.array}).reset_index()
    total_poe = []
    for wp in grouped_2.value.values:
        wsp = []
        if isinstance(wp, list):
            total_poe.append(wp)
        else:  # array
            for wp_i in wp:
                wsp.append(wp_i)
            total_poe.append([sum(t) for t in np.array(wsp).T])
    grouped_2['poes'] = total_poe
    return grouped_2


def _find_sources(df, imtls_dict, imts, rtgm_probmce, mean_hcurve, dstore):

    fig, ax = plt.subplots(3, figsize=(8, 15))

    # identify the sources that have a contribution > than fact (here 10%) of
    # the largest contributor;
    fact = 0.1

    for m, imt in enumerate(imts):
        out_contr_all = []
        fig1, ax1 = plt.subplots()

        dms = df[(df['imt'] == imt)]
        # annual frequency of exceedance:
        T = from_string(imt).period
        f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
        imls_o = imtls_dict[imt]
        imls = [iml*f for iml in imls_o]
        # have to compute everything for max comp. and for geom. mean
        RTGM = rtgm_probmce[m]
        RTGM_o = rtgm_probmce[m]/f
        afe_target = _find_afe_target(imls, mean_hcurve[m], RTGM)
        afe_target_o = _find_afe_target(imls_o, mean_hcurve[m], RTGM_o)

        # populate 3-panel plot
        ax[m].loglog(imls, mean_hcurve[m], 'k', label=_get_label(imt),
                     linewidth=2, zorder=3)
        ax[m].loglog([np.min(imls), RTGM], [afe_target, afe_target], 'k--',
                     linewidth=2, zorder=3)
        ax[m].loglog([RTGM, RTGM], [0, afe_target], 'k--', linewidth=2,
                     zorder=3)
        ax[m].loglog([RTGM], [afe_target], 'ko', label='Probabilistic MCE',
                     linewidth=2, zorder=3)
        # populate individual plots
        ax1.loglog(imls_o, mean_hcurve[m], 'k', label=imt + ' - Geom. mean',
                   linewidth=2, zorder=3)
        ax1.loglog([np.min(imls_o), RTGM_o], [afe_target_o, afe_target_o],
                   'k--', linewidth=2, zorder=3)
        ax1.loglog([RTGM_o, RTGM_o], [0, afe_target_o], 'k--', linewidth=2,
                   zorder=3)
        ax1.loglog([RTGM_o], [afe_target_o], 'ko', label='Probabilistic MCE',
                   linewidth=2, zorder=3)

        # poes from dms are now rates
        for ind, (afes, src) in enumerate(zip(dms.poes, dms.src_id)):
            # get contribution at target level for that source
            afe_uhgm = _find_afe_target(imls, afes, rtgm_probmce[m])
            # get % contribution of that source
            contr_source = afe_uhgm/afe_target
            out_contr_all.append(contr_source * 100)

        # identify contribution of largest contributor, make color scale
        largest_contr = np.max(out_contr_all)
        sample = sum(out_contr_all > fact*largest_contr)
        viridis = mpl.colormaps['viridis'].reversed()._resample(sample)

        # find and plot the sources, highlighting the ones that contribute more
        # than 10% of largest contributor
        # use j to only add the "other sources" label once 
        # use i to cycle through the colors for the major source contributors
        i = j = 0
        for ind, (afes, src) in enumerate(zip(dms.poes, dms.src_id)):
            # pad to have the same length of imls and afes
            afe_pad = afes + [0] * (len(imls) - len(afes))
            # if it's not a big contributor, plot in silver
            if out_contr_all[ind] <= fact*largest_contr:
                if j == 0:
                    ax[m].loglog(imls, afe_pad, 'silver', linewidth=0.7,
                                 label='other sources')
                    ax1.loglog(imls_o, afe_pad, 'silver', linewidth=0.7,
                               label='other source')
                    j += 1
                else:
                    ax[m].loglog(imls, afe_pad, 'silver', linewidth=0.7)
                    ax1.loglog(imls_o, afe_pad, 'silver', linewidth=0.7)
            # if it is, plot in color
            else:
                ax[m].loglog(imls, afe_pad, c=viridis(i), label=str(src))
                ax1.loglog(imls_o, afe_pad, c=viridis(i), label=str(src))
                i += 1
        # populate subplot - maximum component
        ax[m].grid('both')
        ax[m].set_xlabel(imt+' (g)', fontsize=16)
        ax[m].set_ylabel('Annual Freq. Exceedance', fontsize=16)
        ax[m].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
        ax[m].set_ylim([10E-6, 1.1])
        ax[m].set_xlim([0.01, 4])

        # populate single imt plots - geometric mean
        ax1.grid('both')
        ax1.set_xlabel(imt+' (g)', fontsize=16)
        ax1.set_ylabel('Annual Freq. Exceedance', fontsize=16)
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
        ax1.set_ylim([10E-6, 1.1])
        ax1.set_xlim([0.01, 4])

        # save single imt plot
        bio1 = io.BytesIO()
        fig1.savefig(bio1, format='png', bbox_inches='tight')
        # keep these in webui until we finish checks and have a command line
        # exporter, then we can change the name to _{imt} and they will not
        # appear in the webui
        dstore[f'png/disagg_by_src-{imt}.png'] = Image.open(bio1)

    # save triple plot
    bio = io.BytesIO()
    fig.savefig(bio, format='png', bbox_inches='tight')
    logging.info('Storing png/disagg_by_src.png')
    dstore['png/disagg_by_src-All-IMTs.png'] = Image.open(bio)


def plot_governing_mce(dstore, imtls):
    imt_list = []
    imls = []
    for imt, iml in imtls.items():
        imls.append([im for im in iml])
        imt_list.append(imt)
    js = dstore['asce7'][()].decode('utf8')
    dic = json.loads(js)
    MCEr_det = [dic['PGA_84th'], dic['SS_84th'], dic['S1_84th']]
    MCEr = [dic['PGA'], dic['SS'], dic['S1']]
    T = [from_string(imt).period for imt in imt_list]

    limit_det = [0.5, 1.5, 0.6]
    # presenting as maximum component -> do not need conversion facts
    RTGM = dstore.read_df('rtgm')['ProbMCE']
    plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 15})
    plt.plot(T, limit_det, 'kx', markersize=15, label='DLL', linewidth=1)
    plt.plot(T[0], RTGM[0], 'bX', markersize=12, label='$PGA_{GM}$',
             linewidth=3)
    plt.plot(T[1:], RTGM[1:], 'bs', markersize=12,
             label='$S_{S,RT}$ and $S_{1,RT}$', linewidth=3)
    plt.plot(T[0], MCEr_det[0], 'c^', markersize=10, label='$PGA_{84th}$',
             linewidth=3)
    plt.plot(T[1:], MCEr_det[1:], 'cd', markersize=10,
             label='$S_{S,84th}$ and $S_{1,84th}$', linewidth=3)
    plt.scatter(T[0], MCEr[0], s=200, label='Governing $MCE_G$',
                linewidth=2, facecolors='none', edgecolors='r')
    plt.scatter(T[1:], MCEr[1:], s=200, marker='s',
                label='Governing $MCE_R$', linewidth=2,
                facecolors='none', edgecolors='r')
    plt.grid('both')
    plt.ylabel('Spectral Acceleration (g)', fontsize=20)
    plt.xlabel('Period (s)', fontsize=20)
    plt.legend(loc="upper right", fontsize='13')
    plt.ylim([0, np.max([RTGM, MCEr_det, MCEr, limit_det]) + 0.2])
    plt.xlim([-0.02, 1.2])
    bio = io.BytesIO()
    plt.savefig(bio, format='png', bbox_inches='tight')
    plt.clf()
    return Image.open(bio)


def plot_curves(dstore, hc_only=False):
    dinfo = get_info(dstore)
    # site is always 0 for a single-site calculation
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    # separate imts and imls
    AFE, afe_target, imls = [], [], []
    for imt in IMTS:
        # get periods and factors for converting btw geom mean and
        # maximum component
        T = from_string(imt).period
        f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
        imls.append([im*f for im in imtls[imt]])
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm')
    # get the IML for the 2475 RP
    UHGM_RP = rtgm_df['UHGM_2475yr-GM']
    rtgm_probmce = rtgm_df['ProbMCE']
    # get investigation time
    itime = dinfo['investigation_time']
    # get hazard curves, put into rates
    mean_hcurve = dstore['hcurves-stats'][0, 0]  # shape(M, L1)
    for m, hcurve in enumerate(mean_hcurve):
        AFE.append(to_rates(hcurve, itime))
        # get the AFE of the iml that will be disaggregated for each IMT
        afe_target.append(_find_afe_target(imls[m], AFE[m], rtgm_probmce[m]))
    # make plot
    img = plot_meanHCs_afe_RTGM(
        imls, AFE, UHGM_RP, 1/2475, rtgm_probmce, afe_target, IMTS)
    logging.info('Storing png/hcurves.png')
    dstore['png/hcurves.png'] = img

    if hc_only==False:
        df = disaggr_by_src(dstore, imtls)
        _find_sources(df, imtls, IMTS, rtgm_probmce, mean_hcurve, dstore)

        img = plot_governing_mce(dstore, imtls)
        logging.info('Storing png/governing_mce.png')
        dstore['png/governing_mce.png'] = img


def main(dstore, csm):
    """
    :param dstore: datastore with the classical calculation
    """
    if not rtgmpy:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    if dstore['mean_rates_ss'][:].max() < 1E-3:
        logging.warning('Ultra-low hazard: skipping AELO calculation')
        return
    logging.info('Computing Risk Targeted Ground Motion')
    oq = dstore['oqparam']
    stats = list(oq.hazard_stats())
    assert stats[0] == 'mean', stats[0]
    hcurves = dstore['hcurves-stats'][:, 0]  # shape NML1
    sitecol = dstore['sitecol']
    hazdic, facts = get_hazdic_facts(
        hcurves, oq.imtls, oq.investigation_time, sitecol)
    rtgm_haz = rtgmpy.GroundMotionHazard.from_dict(hazdic)
    rtgm_df = calc_rtgm_df(rtgm_haz, facts, oq)
    logging.info('Computed RTGM\n%s', rtgm_df)
    dstore.create_df('rtgm', rtgm_df)
    facts[0] = 1 # for PGA the Prob MCE is already geometric mean
    imls_disagg = rtgm_df.ProbMCE.to_numpy() / facts
    prob_mce = rtgm_df.ProbMCE.to_numpy()

    if (rtgm_df.ProbMCE < DLLs).all():  # do not disaggregate by rel sources
        logging.warning('Low hazard, do not disaggregate by source')
        dummy_det = {'PGA': '', 'SA(0.2)': '', 'SA(1.0)': ''}
        prob_mce_out, mce, det_mce, asce7 = get_mce_asce7(
            prob_mce, dummy_det, DLLs, dstore, low=True)
        dstore['asce7'] = hdf5.dumps(asce7)
        asce41 = get_asce41(dstore, mce, facts, low=True)
        dstore['asce41'] = hdf5.dumps(asce41)
        return

    mag_dist_eps, sigma_by_src = postproc.disagg_by_rel_sources.main(
        dstore, csm, IMTS, imls_disagg)
    det_imt, mag_dst_eps_sig = get_deterministic(
        prob_mce, mag_dist_eps, sigma_by_src)
    dstore['mag_dst_eps_sig'] = mag_dst_eps_sig
    logging.info(f'{det_imt=}')
    prob_mce_out, mce, det_mce, asce7 = get_mce_asce7(
        prob_mce, det_imt, DLLs, dstore)
    logging.info(f'{mce=}')
    logging.info(f'{det_mce=}')
    dstore['asce7'] = hdf5.dumps(asce7)
    asce41 = get_asce41(dstore, mce, facts)
    dstore['asce41'] = hdf5.dumps(asce41)
    logging.info(asce41)
    logging.info(asce7)

    if Image is None:  # missing PIL
        logging.warning('Missing module PIL: skipping plotting curves')
    else:
        plot_curves(dstore)
