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
import sys
import logging
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
from openquake.baselib import hdf5, general
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.calculators import postproc
from openquake.calculators.postproc.aelo_plots import (
    plot_mean_hcurves_rtgm, plot_disagg_by_src, plot_governing_mce, plot_sites,
    _find_fact_maxC)

DLL_df = pd.read_csv(io.StringIO('''\
imt,A,B,BC,C,CD,D,DE,E
SA(0.0),0.50,0.57,0.66,0.73,0.74,0.69,0.61,0.55
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
'''))

MIN_AFE = 1/2475
ASCE_DECIMALS = 5

AELO_WARNINGS = {
    'zero_hazard': (
        'Zero hazard: there are no ruptures close to the site.'
        ' ASCE 7 and ASCE 41 parameters cannot be computed.'
        ' For further information, please refer to the user manual.'),
    'low_hazard': (
        'Very low hazard: ASCE 7 and ASCE 41'
        ' parameters cannot be computed.'
        ' For further information, please refer to the user manual.'),
    'below_min': (
        'The ASCE 7 and/or ASCE 41 parameter values at the site are very low.'
        ' User may need to increase the values to user-specified minimums'
        ' (e.g., Ss=0.11g and S1=0.04g).'
        ' For further information, please refer to the user manual.'),
}

AELO_NOTES = {
    'only_prob_mce': (
        'The final MCE is derived solely from the Probabilistic MCE,'
        ' which is below the DLLs. Outputs specific to the deterministic'
        ' analysis are not included.'
        ' For further information, please refer to the user manual.'),
}

notification_dtype = np.dtype([
    ('sid', np.int32),
    ('level', hdf5.vstr),
    ('name', hdf5.vstr),
    ('description', hdf5.vstr)
])


def get_DLLs(job_imts, vs30):

    if vs30 >= 1500:
        soil_class_asce = 'A'
    elif vs30 > 914:
        soil_class_asce = 'B'
    elif vs30 > 640:
        soil_class_asce = 'BC'
    elif vs30 > 442:
        soil_class_asce = 'C'
    elif vs30 > 305:
        soil_class_asce = 'CD'
    elif vs30 > 213:
        soil_class_asce = 'D'
    elif vs30 > 152:
        soil_class_asce = 'DE'
    else:
        soil_class_asce = 'E'

    D = DLL_df[soil_class_asce]
    imt_table = DLL_df.imt

    T_table = np.array([from_string(imt).period for imt in DLL_df.imt])
    T_job = [from_string(imt).period for imt in job_imts]
    DLLs = []

    for imt, t in zip(job_imts, T_job):
        if imt in imt_table.values:
            DLLs.append(D[imt_table == imt].values[0])
        else:  # interpolate for any IMT not included in the table
            up = np.where(T_table > t)[0][0]
            low = np.where(T_table < t)[0][-2]
            dll = np.interp(t, [T_table[low], T_table[up]], [D[low], D[up]])
            DLLs.append(dll)
    return DLLs


def norm_imt(imt):
    """
    Normalize the imt string to the USGS format, for instance SA(1.1) -> SA1P1
    """
    return imt.replace('(', '').replace(')', '').replace('.', 'P')


def calc_rtgm_df(hcurves, site, site_idx, oq, ASCE_version):
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    :param hcurves: array of hazard curves of shape (M, L1)
    :param site: a Site object
    :param oq: OqParam instance
    :returns: pandas dataframe with RTGM and related parameters
    :returns: numpy array of conversion factors to max component
    """
    job_imts = list(oq.imtls)
    M = len(job_imts)
    DLLs = get_DLLs(job_imts, site.vs30)
    riskCoeff, RTGM, UHGM, RTGM_max, MCE, rtgmCalc = (
        np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M),
        np.zeros(M), np.zeros(M))
    imtls = oq.imtls
    imts, facts = [], []
    for m, imt in enumerate(job_imts):
        afe = to_rates(hcurves[m], oq.investigation_time, minrate=1E-12)
        IMT = norm_imt(imt)
        imts.append(IMT)
        T = from_string(imt).period
        fact = 1 if imt == "PGA" else _find_fact_maxC(T, ASCE_version)
        facts.append(fact)
        if afe[0] < MIN_AFE:
            UHGM[m] = 0
            RTGM_max[m] = 0
            MCE[m] = 0
            riskCoeff[m] = 0
        elif afe[-1] > MIN_AFE:
            raise ValueError("the max iml is too low: change the job.ini")
        else:
            hazdic = _get_hazdic(afe, IMT, imtls[imt] * fact, site)
            rtgm_haz = rtgmpy.GroundMotionHazard.from_dict(hazdic)
            results = rtgmpy.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')
            rtgmCalc = results['RTGM'][IMT]['rtgmCalc']
            RTGM_max[m] = rtgmCalc['rtgm']  # for maximum component
            UHGM[m] = rtgmCalc['uhgm'] / fact  # for geometric mean
            riskCoeff[m] = rtgmCalc['riskCoeff']
            # note that RTGM_max is the ProbMCEr, while RTGM is used for the
            # identification of the sources as the hazard curves are in
            # geometric mean
            if IMT == 'PGA':
                RTGM[m] = UHGM[m]
                MCE[m] = RTGM[m]  # UHGM in terms of GM: MCEg
            else:
                RTGM[m] = rtgmCalc['rtgm'] / fact  # for geometric mean
                MCE[m] = RTGM_max[m]
    facts[0] = 1.  # for PGA the Prob MCE is already geometric mean
    dic = {'IMT': imts,
           'UHGM_2475yr-GM': UHGM,
           'RTGM': RTGM_max,
           'ProbMCE': MCE,
           'RiskCoeff': riskCoeff,
           'DLL': DLLs,
           'fact': np.array(facts),
           'sid': [site_idx]*len(imts)}
    rtgm_df = pd.DataFrame(dic)
    return rtgm_df


def _get_hazdic(afe, imt, imtls, site):
    hazdic = {
        'site': {'name': 'site',
                 'lon': site.location.x,
                 'lat': site.location.y,
                 'Vs30': site.vs30},
        'hazCurves': {imt: {'iml': imtls, 'afe': afe}}}
    return hazdic


def get_deterministic(prob_mce, mag_dist_eps, sigma_by_src):
    """
    :param prob_mce: Probabilistic Maximum Considered Earthquake (UHGM for PGA)
    :param mag_dist_eps: disaggregation MDE by source
    :param sigma_by_src: weighted GMPE sigma
    :returns: a dictionary imt -> deterministic MCE
    :returns: a numpy array specifying (src, mag, dist, eps, sigma, imt)
    """
    srcs, imts, dets = [], [], []
    srcidx = {src: i for i, src in enumerate(sigma_by_src.source_id)}
    imtidx = {imt: i for i, imt in enumerate(sigma_by_src.imt)}
    mag_dist_eps_sig = []
    for src, imt, mag, dist, eps in mag_dist_eps:
        m = imtidx[imt]
        if np.isnan(mag):
            srcs.append(src)
            imts.append(imt)
            dets.append(np.nan)
            mag_dist_eps_sig.append((imt, src, mag, dist, eps, np.nan))
        else:
            sig = sigma_by_src[srcidx[src], :, :, m]  # shape (Ma, D)
            rgi = RegularGridInterpolator(
                (sigma_by_src.mag, sigma_by_src.dist), sig)
            sigma = rgi((np.round(mag, 3), np.round(dist, 3)))
            srcs.append(src)
            imts.append(imt)
            dets.append(prob_mce[m] * np.exp(sigma) / np.exp(eps*sigma))
            mag_dist_eps_sig.append((imt, src, mag, dist, eps, sigma))
    df = pd.DataFrame(dict(imt=imts, source_id=srcs, det=dets))
    det = {}
    for imt in df.imt.values:
        df_sub = df[df.imt == imt]
        val = max(df_sub.det)
        det[imt] = val
    dt = [('imt', hdf5.vstr), ('source_id', hdf5.vstr), ('mag', float),
          ('dist', float), ('eps', float), ('sig', float)]
    return det, np.array(mag_dist_eps_sig, dt)


def get_zero_hazard_asce07(ASCE_version, vs30):
    na = 'n.a.'

    if ASCE_version == 'ASCE7-16':
        asce07 = {
             'PGA': 0, 'PGA_2_50': 0,
             'PGA_84th': na, 'PGA_det': na,

             'Ss': na, 'Ss_RT': na,
             'CRs': na, 'Ss_84th': na,
             'Ss_det': na,
             'Ss_seismicity': 'Low',

             'S1': na, 'S1_RT': na,
             'CR1': na, 'S1_84th': na,
             'S1_det': na,
             'S1_seismicity': 'Low'
             }
    else:

        if vs30 == 760:
            asce07 = {
                'PGA': 0, 'PGA_2_50': 0,
                'PGA_84th': na, 'PGA_det': na,
                'Ss': na, 'Sms': na,
                'Sds': na, 'Ss_RT': na,
                'CRs': na, 'Ss_84th': na,
                'Ss_det': na,
                'Ss_seismicity': 'Low',
                'S1': na, 'Sm1': na,
                'Sd1': na, 'S1_RT': na,
                'CR1': na, 'S1_84th': na,
                'S1_det': na,
                'S1_seismicity': 'Low'
            }
        else:
            asce07 = {
                'PGA': 0, 'PGA_2_50': 0,
                'PGA_84th': na, 'PGA_det': na,
                'Sms': na,
                'Sds': na, 'Ss_RT': na,
                'CRs': na, 'Ss_84th': na,
                'Ss_det': na,
                'Ss_seismicity': 'Low',
                'Sm1': na,
                'Sd1': na, 'S1_RT': na,
                'CR1': na, 'S1_84th': na,
                'S1_det': na,
                'S1_seismicity': 'Low'
            }

    return asce07


def get_zero_hazard_asce41(ASCE_version):
    na = 'n.a.'
    if ASCE_version == 'ASCE7-16':
        asce41 = {'BSE2N_Ss': na,
                  'BSE2E_Ss': na,
                  'Ss_5_50': na,
                  'BSE1N_Ss': na,
                  'BSE1E_Ss': na,
                  'Ss_20_50': na,
                  'BSE2N_S1': na,
                  'BSE2E_S1': na,
                  'S1_5_50': na,
                  'BSE1N_S1': na,
                  'BSE1E_S1': na,
                  'S1_20_50': na,
                  }
    else:
        asce41 = {'BSE2N_Ss': na,
                  'BSE2E_Ss': na,
                  'Ss_5_50': na,
                  'BSE1N_Ss': na,
                  'BSE1E_Ss': na,
                  'Ss_20_50': na,
                  'BSE2N_S1': na,
                  'BSE2E_S1': na,
                  'S1_5_50': na,
                  'BSE1N_S1': na,
                  'BSE1E_S1': na,
                  'S1_20_50': na,
                  }
    return asce41


def get_seismicity_class(mce, vs30):

    if vs30 == 760:
        if mce['SA(0.2)'] < 0.25:
            Ss_seismicity = "Low"
        elif mce['SA(0.2)'] < 0.5:
            Ss_seismicity = "Moderate"
        elif mce['SA(0.2)'] < 1:
            Ss_seismicity = "Moderately High"
        elif mce['SA(0.2)'] < 1.5:
            Ss_seismicity = "High"
        else:
            Ss_seismicity = "Very High"

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
    else:
        Ss_seismicity = "n.a."
        S1_seismicity = "n.a."
    return Ss_seismicity, S1_seismicity


class MCEGetter:
    """
    :param job_imts: the IMTs run in the job
    :param det_imt: deterministic ground motion for each IMT
    :param ASCE_version: ASCE version string
    """
    def __init__(self, job_imts, det_imt, ASCE_version):
        self.job_imts = job_imts
        self.det_imt = det_imt
        self.ASCE_version = ASCE_version

    def get_mce_asce07(self, DLLs, rtgm, sid, vs30, low_haz=False):
        """
        :param DLLs: deterministic lower limits according to ASCE 7-22
        :param rtgm: dataframe
        :param sid: the site ID
        :param low_haz: boolean specifying if the hazard is lower than DLLs
        :returns: a dictionary imt -> probabilistic MCE
        :returns: a dictionary imt -> governing MCE
        :returns: a dictionary all ASCE 7-16 parameters
        :returns: pandas dataframe with three MCEs and related parameters
        """
        det_imt = self.det_imt
        job_imts = self.job_imts
        prob_mce = rtgm.ProbMCE.to_numpy()
        imts = rtgm['IMT']
        for i, imt in enumerate(imts):
            if imt == 'SA0P2':
                crs = rtgm['RiskCoeff'][i]
            elif imt == 'SA1P0':
                cr1 = rtgm['RiskCoeff'][i]

        det_mce = {}
        mce = {}  # imt -> MCE
        prob_mce_out = {}
        for i, imt in enumerate(det_imt):
            if low_haz:
                det_mce[imt] = np.nan
                det_imt[imt] = np.nan
                mce[imt] = prob_mce[i]
            else:
                det_mce[imt] = max(det_imt[imt], DLLs[i])
                mce[imt] = min(prob_mce[i], det_mce[imt])
            prob_mce_out[imt] = prob_mce[i]
        dic_mce = {'IMT': job_imts,
                   'DLL': DLLs,
                   'ProbMCE': prob_mce,
                   'DetMCE': det_mce.values(),
                   'MCE': mce.values(),
                   'sid': [sid]*len(job_imts)}
        mce_df = pd.DataFrame(dic_mce)

        Ss_seismicity, S1_seismicity = get_seismicity_class(mce, vs30)
        period_mce = [from_string(imt).period for imt in job_imts]
        if self.ASCE_version == 'ASCE7-16':
            asce07 = {
                 'PGA': mce['PGA'], 'PGA_2_50': prob_mce_out['PGA'],
                 'PGA_84th': det_imt['PGA'], 'PGA_det': det_mce['PGA'],

                 'Ss': mce['SA(0.2)'], 'Ss_RT': prob_mce_out['SA(0.2)'],
                 'CRs': crs, 'Ss_84th': det_imt['SA(0.2)'],
                 'Ss_det': det_mce['SA(0.2)'],
                 'Ss_seismicity': Ss_seismicity,

                 'S1': mce['SA(1.0)'], 'S1_RT': prob_mce_out['SA(1.0)'],
                 'CR1': cr1, 'S1_84th': det_imt['SA(1.0)'],
                 'S1_det': det_mce['SA(1.0)'],
                 'S1_seismicity': S1_seismicity
                 }
        else:
            design = calc_sds_and_sd1(period_mce, mce_df.MCE, vs30)
            if vs30 == 760:
                asce07 = {
                    'PGA': mce['PGA'], 'PGA_2_50': prob_mce_out['PGA'],
                    'PGA_84th': det_imt['PGA'], 'PGA_det': det_mce['PGA'],
                    'Ss': mce['SA(0.2)'], 'Sms': design[2],
                    'Sds': design[0], 'Ss_RT': prob_mce_out['SA(0.2)'],
                    'CRs': crs, 'Ss_84th': det_imt['SA(0.2)'],
                    'Ss_det': det_mce['SA(0.2)'],
                    'Ss_seismicity': Ss_seismicity,
                    'S1': mce['SA(1.0)'], 'Sm1': design[3],
                    'Sd1': design[1], 'S1_RT': prob_mce_out['SA(1.0)'],
                    'CR1': cr1, 'S1_84th': det_imt['SA(1.0)'],
                    'S1_det': det_mce['SA(1.0)'],
                    'S1_seismicity': S1_seismicity
                }
            else:
                asce07 = {
                    'PGA': mce['PGA'], 'PGA_2_50': prob_mce_out['PGA'],
                    'PGA_84th': det_imt['PGA'], 'PGA_det': det_mce['PGA'],
                    'Sms': design[2], 'Sds': design[0],
                    'Ss_RT': prob_mce_out['SA(0.2)'],
                    'CRs': crs, 'Ss_84th': det_imt['SA(0.2)'],
                    'Ss_det': det_mce['SA(0.2)'],
                    'Ss_seismicity': Ss_seismicity,
                    'Sm1': design[3], 'Sd1': design[1],
                    'S1_RT': prob_mce_out['SA(1.0)'],
                    'CR1': cr1, 'S1_84th': det_imt['SA(1.0)'],
                    'S1_det': det_mce['SA(1.0)'],
                    'S1_seismicity': S1_seismicity
                }
        for key in asce07:
            if not isinstance(asce07[key], str):
                asce07[key] = (round(asce07[key], ASCE_DECIMALS)
                               if asce07[key] is not np.nan
                               else 'n.a.')
        return prob_mce_out, mce, asce07, mce_df


def get_asce41(dstore, mce, facts, sid):
    """
    :param dstore: the datastore
    :param mce: governing MCE
    :param facts: conversion factors to max component
    :param sid: the site ID
    :returns: a dictionary with the ASCE-41 parameters
    """
    fact = dict(zip(mce, facts))
    hmap = dstore["hmaps-stats"][sid, 0]  # mean hazard, shape (M, P)
    oq = dstore['oqparam']
    ASCE_version = oq.asce_version
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
    if ASCE_version == 'ASCE7-16':
        asce41 = {
            'BSE2N_Ss': BSE2N_Ss,
            'BSE2E_Ss': BSE2E_Ss,
            'Ss_5_50': Ss_5_50,
            'BSE1N_Ss': BSE1N_Ss,
            'BSE1E_Ss': BSE1E_Ss,
            'Ss_20_50': Ss_20_50,
            'BSE2N_S1': BSE2N_S1,
            'BSE2E_S1': BSE2E_S1,
            'S1_5_50': S1_5_50,
            'BSE1N_S1': BSE1N_S1,
            'BSE1E_S1': BSE1E_S1,
            'S1_20_50': S1_20_50,
        }
    else:  # the below needs to be changed
        asce41 = {
            'BSE2N_Ss': BSE2N_Ss,
            'BSE2E_Ss': BSE2E_Ss,
            'Ss_5_50': Ss_5_50,
            'BSE1N_Ss': BSE1N_Ss,
            'BSE1E_Ss': BSE1E_Ss,
            'Ss_20_50': Ss_20_50,
            'BSE2N_S1': BSE2N_S1,
            'BSE2E_S1': BSE2E_S1,
            'S1_5_50': S1_5_50,
            'BSE1N_S1': BSE1N_S1,
            'BSE1E_S1': BSE1E_S1,
            'S1_20_50': S1_20_50,
        }
    for key in asce41:
        asce41[key] = round(asce41[key], ASCE_DECIMALS)
    return asce41


def get_rtgm_notification(site, oq, sa02, sa10, DLLs, ASCE_version,
                          mrs_all, hcurves_all):
    """
    :returns: (rtgm_df, notification_name)
    """
    sid = site.id
    mrs = mrs_all[sid]
    hcurves = hcurves_all[sid, 0]  # shape ML1
    mean_rates = to_rates(hcurves)
    loc = site.location

    if mrs.sum() == 0:
        return None, 'zero_hazard'
    elif mean_rates.max() < MIN_AFE or hcurves[0, 0] < min(oq.poes):
        # PGA curve too low
        return None, 'low_hazard'
    try:
        rtgm_df = calc_rtgm_df(hcurves, site, sid, oq, ASCE_version)
    except ValueError as err:
        # happens for site (24.96, 60.16) in EUR, the curve is too low
        if 'below the interpolation range' in str(err):
            return None, 'low_hazard'
        else:
            print(f'on site({loc.x}, {loc.y}): {err}', file=sys.stderr)
            raise
    logging.info('(%.1f,%.1f) Computed RTGM\n%s', loc.x, loc.y, rtgm_df)

    if (rtgm_df.ProbMCE.to_numpy()[sa02] < 0.11) or \
            (rtgm_df.ProbMCE.to_numpy()[sa10] < 0.04):
        return rtgm_df, 'below_min'
    elif (rtgm_df.ProbMCE < DLLs[site.id]).all():
        # do not disagg by rel sources
        return rtgm_df, 'only_prob_mce'
    else:
        return rtgm_df, None


def process_sites(dstore, csm, DLLs, ASCE_version):
    """
    :yields: (site, rtgm_df, notification_name)
    """
    oq = dstore['oqparam']
    imts = list(oq.imtls)
    sa02 = imts.index('SA(0.2)')
    sa10 = imts.index('SA(1.0)')
    stats = list(oq.hazard_stats())
    assert stats[0] == 'mean', stats[0]
    hcurves_all = dstore['hcurves-stats'][:]
    mrs_all = dstore['mean_rates_by_src'][:]
    mg = MCEGetter(imts, {imt: '' for imt in imts}, ASCE_version)
    for site in dstore['sitecol']:
        rtgm_df, notification_name = get_rtgm_notification(
            site, oq, sa02, sa10, DLLs, ASCE_version, mrs_all, hcurves_all)
        sid = site.id
        vs30 = site.vs30
        loc = site.location
        if notification_name in ['zero_hazard', 'low_hazard']:
            mce_df = pd.DataFrame({'IMT': imts,
                                   'ProbMCE': [np.nan]*len(imts),
                                   'DetMCE': [np.nan]*len(imts),
                                   'MCE': [np.nan]*len(imts),
                                   'sid': [sid]*len(imts)})
            a07 = hdf5.dumps(get_zero_hazard_asce07(ASCE_version, vs30))
            a41 = hdf5.dumps(get_zero_hazard_asce41(ASCE_version))
            logging.info('(%.1f,%.1f) Computed MCE: Zero hazard\n%s', loc.x,
                         loc.y, mce_df)
        elif notification_name in ['below_min', 'only_prob_mce']:
            _prob_mce_out, mce, a07, mce_df = mg.get_mce_asce07(
                DLLs[sid], rtgm_df, sid, vs30, low_haz=True)
            logging.info('(%.1f,%.1f) Computed MCE: Only Prob\n%s', loc.x,
                         loc.y, mce_df)
            a41 = get_asce41(dstore, mce, rtgm_df.fact.to_numpy(), sid)
            a07 = hdf5.dumps(a07)
            a41 = hdf5.dumps(a41)
        else:
            mce_df = None
            a07 = None
            a41 = None
        yield site, rtgm_df, mce_df, a07, a41, notification_name


def calc_sds_and_sd1(periods: list, ordinates: list, vs30: float) -> tuple:
    """
    Calculates sds and sd1 from multiperiod response spectrum according
    to section 21.4 in ASCE7-22

    Args:
        periods: A list of periods for the multiperiod response spectrum.
        ordinates: A list of ordinates (accelerations) for the multiperiod
        response spectrum multiplied by 2/3 as shown in eq. 21.3-1 in ASCE7-22
        vs30: A float representing the vs30 in m/s

    Returns:
        A tuple (sds, sd1) where sds is the spectral response acceleration for
        short periods, and sd1 is the
        spectral response acceleration for 1 second.
    """

    # For sds, find periods from 0.2-5.0s, inclusive
    sds_indices = [
        index for index, period in enumerate(periods) if 0.2 <= period <= 5]

    # sds is 90% of the maximum from 0.2-5.0s
    sds = 90 / 100 * max([ordinates[i] * 2/3 for i in sds_indices])

    # For sd1, depending on vs30, take periods from 1-2s or 1-5s
    # vs30 in m/s
    if vs30 > 442:
        sd1_indices = [
            index for index, period in enumerate(periods) if 1 <= period <= 2]
    else:
        sd1_indices = [
            index for index, period in enumerate(periods) if 1 <= period <= 5]

    sd1_periods = [periods[i] for i in sd1_indices]
    sd1_ordinates = [ordinates[i] * 2/3 for i in sd1_indices]

    # sd1 is 90% of the maximum of T * Sa across the period range,
    # but not less than 100% of the value of Sa at 1.0s
    maxp = max(period * sd1_ordinates[i]
               for i, period in enumerate(sd1_periods))
    sd1 = max(90 / 100 * maxp, 100 / 100 * sd1_ordinates[0])
    sms = 1.5 * sds
    sm1 = 1.5 * sd1

    design = [sds, sd1, sms, sm1]

    return design


# this is spawning disagg_by_rel_sources
def calc_asce(dstore, csm, job_imts, DLLs, rtgm, ASCE_version):
    """
    :yields: (sid, mag_dst_eps_sig, asce07, asce41, mce_df)
    """
    oq = dstore['oqparam']
    imls_by_sid = {sid: rtgm_df.ProbMCE.to_numpy() / rtgm_df.fact.to_numpy()
                   for sid, rtgm_df in rtgm.items()}
    out = postproc.disagg_by_rel_sources.main(
        dstore, csm, job_imts, imls_by_sid)
    sitecol = dstore['sitecol']
    for sid, (mag_dist_eps, sigma_by_src) in out.items():
        lon = sitecol.lons[sid]
        lat = sitecol.lats[sid]
        vs30 = sitecol.vs30[sid]
        rtgm_df = rtgm[sid]
        det_imt, mag_dst_eps_sig = get_deterministic(
            rtgm_df.ProbMCE.to_numpy(), mag_dist_eps, sigma_by_src)
        logging.info(f'(%.1f,%.1f) {det_imt=}', lon, lat)
        mg = MCEGetter(job_imts, det_imt, oq.asce_version)
        _prob_mce_out, mce, asce07, mce_df = mg.get_mce_asce07(
            DLLs[sid], rtgm_df, sid, vs30)
        logging.info('(%.1f,%.1f) Computed MCE: high hazard\n%s', lon, lat,
                     mce_df)
        logging.info(f'(%.1f,%.1f) {mce=}', lon, lat)
        asce41 = get_asce41(dstore, mce, rtgm_df.fact.to_numpy(), sid)

        logging.info('(%.1f,%.1f) ASCE 7=%s', lon, lat, asce07)
        logging.info('(%.1f,%.1f) ASCE 41=%s', lon, lat, asce41)

        yield (sid, mag_dst_eps_sig, hdf5.dumps(asce07), hdf5.dumps(asce41),
               mce_df)


def to_array(dic):
    return np.array([dic[sid] for sid in sorted(dic)])


# tested in test_rtgm
def compute_mce_max(dstore, sids):
    """
    For ASCE7-22 the site is multiplied 3 times with different
    values of the vs30 and the MCE is computed as the maximum MCE
    across the sites
    """
    # fields IMT, DLL, ProbMCE, DetMCE, MCE, sid
    mce_df = dstore.read_df('mce')
    # TODO: create an output 'mce7-22'


def main(dstore, csm):
    """
    :param dstore: datastore with the classical calculation
    :param csm: a CompositeSourceModel instance
    """
    oq = dstore['oqparam']
    ASCE_version = oq.asce_version
    job_imts = list(oq.imtls)
    DLLs = {
        site.id: get_DLLs(job_imts, site.vs30) for site in dstore['sitecol']
    }
    if not rtgmpy:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    asce07 = {}
    asce41 = {}
    notification_items = []
    rtgm_dfs = []
    mce_dfs = []
    rtgm = {}
    locs = general.AccumDict(accum=[])  # lon, lat -> sids
    for site, rtgm_df, mce_df, a07, a41, notification_name in process_sites(
            dstore, csm, DLLs, ASCE_version):
        sid = site.id
        loc = site.location
        locs[loc.x, loc.y].append(sid)
        if mce_df is None:  # high hazard site requiring calc_asce
            rtgm[sid] = rtgm_df
        else:  # low hazard
            mce_dfs.append(mce_df)
            asce07[sid] = a07
            asce41[sid] = a41
        if notification_name:
            if notification_name in AELO_WARNINGS:
                level = 'warning'
                description = AELO_WARNINGS[notification_name]
                logging.warning('(%.1f,%.1f) ' + description, loc.x, loc.y)
            elif notification_name in AELO_NOTES:
                level = 'info'
                description = AELO_NOTES[notification_name]
                logging.info('(%.1f,%.1f) ' + description, loc.x, loc.y)
            else:
                raise NotImplementedError(
                    f'Unexpected notification name: {notification_name}')
            notification_items.append((sid, level, notification_name, description))
        if rtgm_df is not None:
            rtgm_dfs.append(rtgm_df)
    notifications = np.array(notification_items, dtype=notification_dtype)

    for sid, mdes, a07, a41, mce_df in calc_asce(
            dstore, csm, job_imts, DLLs, rtgm, ASCE_version):
        asce07[sid] = a07
        asce41[sid] = a41
        dstore[f'mag_dst_eps_sig/{sid}'] = mdes
        mce_dfs.append(mce_df)

    dstore['asce07'] = to_array(asce07)
    dstore['asce41'] = to_array(asce41)

    if mce_dfs:
        dstore.create_df('mce', pd.concat(mce_dfs))

    if rtgm_dfs:
        dstore.create_df('rtgm', pd.concat(rtgm_dfs))

    plot_sites(dstore, update_dstore=True)
    if rtgm_dfs and len(locs) == 1:
        [sids] = locs.values()
        for sid in sids:
            sid_notifications = notifications[notifications['sid'] == sid]
            if not sid_notifications:
                plot_mean_hcurves_rtgm(dstore, sid, update_dstore=True)
                plot_governing_mce(dstore, sid, update_dstore=True)
                plot_disagg_by_src(dstore, sid, update_dstore=True)
            elif sid_notifications['name'][0] not in ['zero_hazard', 'low_hazard']:
                plot_mean_hcurves_rtgm(dstore, sid, update_dstore=True)
                plot_governing_mce(dstore, sid, update_dstore=True)

    if notifications:
        dstore['notifications'] = notifications

    for sids in locs.values():
        if len(sids) > 1:
            compute_mce_max(dstore, sids)
