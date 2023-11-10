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
import numpy as np
import pandas as pd
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
from openquake.calculators.postproc.aelo_plots import (
    plot_mean_hcurves_afe_rtgm, plot_disagg_by_src, plot_governing_mce,
    _find_fact_maxC)

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
MIN_AFE = 1/2475
ASCE_DECIMALS = 5


def norm_imt(imt):
    """
    Normalize the imt string to the USGS format, for instance SA(1.1) -> SA1P1
    """
    return imt.replace('(', '').replace(')', '').replace('.', 'P')


def calc_rtgm_df(hcurves, sitecol, oq):
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    :param hcurves: array of hazard curves of shape (1, M, L1)
    :param sitecol: a SiteCollection instance with 1 site
    :param oq: OqParam instance

    :returns: pandas dataframe with RTGM and related parameters
    :returns: numpy array of conversion factors to max component
    """
    M = len(IMTS)
    riskCoeff, RTGM, UHGM, RTGM_max, MCE, rtgmCalc = (
        np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M),
        np.zeros(M), np.zeros(M))
    imtls = oq.imtls
    imts, facts = [], []
    for m, imt in enumerate(IMTS):
        afe = to_rates(hcurves[0, m], oq.investigation_time, minrate=1E-12)

        IMT = norm_imt(imt)
        imts.append(IMT)
        T = from_string(imt).period
        fact = _find_fact_maxC(T, 'ASCE7-16')
        facts.append(fact)

        if afe[0] < MIN_AFE:
            logging.warning('Hazard is too low for %s', imt)
            UHGM[m] = 0
            RTGM_max[m] = 0
            MCE[m] = 0
            riskCoeff[m] = 0
        elif afe[-1] > MIN_AFE:
            raise ValueError("the max iml is too low: change the job.ini")
        else:
            hazdic = _get_hazdic(afe, IMT, imtls[imt] * fact, sitecol)
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
    dic = {'IMT': imts,
           'UHGM_2475yr-GM': UHGM,
           'RTGM': RTGM_max,
           'ProbMCE': MCE,
           'RiskCoeff': riskCoeff,
           'DLL': DLLs}

    return pd.DataFrame(dic), np.array(facts)


def _get_hazdic(afe, imt, imtls, sitecol):
    [site] = sitecol  # there must be a single site
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
        sig = sigma_by_src[srcidx[src], :, :, m]  # shape (Ma, D)
        rgi = RegularGridInterpolator(
            (sigma_by_src.mag, sigma_by_src.dist), sig)
        sigma = rgi((np.round(mag, 3), np.round(dist, 3)))
        srcs.append(src)
        imts.append(imt)
        dets.append(prob_mce[m] * np.exp(sigma) / np.exp(eps*sigma))
        mag_dist_eps_sig.append((src, mag, dist, eps, sigma, imt))
    df = pd.DataFrame(dict(src=srcs, imt=imts, det=dets))
    det = df.groupby('imt').det.max()
    dt = [('src', hdf5.vstr), ('mag', float), ('dst', float),
          ('eps', float), ('sig', float), ('imt', hdf5.vstr)]
    return det.to_dict(), np.array(mag_dist_eps_sig, dt)


def get_mce_asce7(prob_mce, det_imt, DLLs, dstore, low_haz=False):
    """
    :param prob_mce: Probabilistic Maximum Considered Earthquake (UHGM for PGA)
    :param det_imt: deterministic ground motion for each IMT
    :param DLLs: deterministic lower limits according to ASCE7
    :param dstore: the datastore
    :param low_haz: boolean specifying if the hazard is lower than DLLs
    :returns: a dictionary imt -> probabilistic MCE
    :returns: a dictionary imt -> governing MCE
    :returns: a dictionary imt -> deterministic MCE
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
        if low_haz:
            det_mce[imt] = None
            det_imt[imt] = None
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
    for key in asce7:
        if key in ('PGA_2_50', 'PGA_84th', 'PGA_det', 'PGA', 'SS_RT', 'CRS',
                   'SS_84th', 'SS_det', 'SS', 'S1_RT', 'CR1', 'S1_84th',
                   'S1_det', 'S1'):
            asce7[key] = (
                round(asce7[key], ASCE_DECIMALS)
                if asce7[key] is not None else 'n.a.')

    return prob_mce_out, mce, det_mce, asce7


def get_asce41(dstore, mce, facts):
    """
    :param dstore: the datastore
    :param mce: governing MCE
    :param facts: conversion factors to max component
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
    asce41 = {'BSE2N_Ss': BSE2N_Ss,
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
              'BSE1N_S1': BSE1N_S1,
              }
    for key in asce41:
        asce41[key] = round(asce41[key], ASCE_DECIMALS)
    return asce41


def main(dstore, csm):
    """
    :param dstore: datastore with the classical calculation
    :param csm: a CompositeSourceModel instance
    """
    if not rtgmpy:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    if dstore['mean_rates_ss'][:].max() < MIN_AFE:
        logging.warning('Ultra-low hazard: skipping AELO calculation')
        return
    logging.info('Computing Risk Targeted Ground Motion')
    oq = dstore['oqparam']
    stats = list(oq.hazard_stats())
    assert stats[0] == 'mean', stats[0]
    hcurves = dstore['hcurves-stats'][:, 0]  # shape NML1
    sitecol = dstore['sitecol']
    rtgm_df, facts = calc_rtgm_df(hcurves, sitecol, oq)
    logging.info('Computed RTGM\n%s', rtgm_df)
    dstore.create_df('rtgm', rtgm_df)
    facts[0] = 1  # for PGA the Prob MCE is already geometric mean
    imls_disagg = rtgm_df.ProbMCE.to_numpy() / facts
    prob_mce = rtgm_df.ProbMCE.to_numpy()

    if (rtgm_df.ProbMCE < DLLs).all():  # do not disaggregate by rel sources
        logging.warning('Low hazard, do not disaggregate by source')
        dummy_det = {'PGA': '', 'SA(0.2)': '', 'SA(1.0)': ''}
        prob_mce_out, mce, det_mce, asce7 = get_mce_asce7(
            prob_mce, dummy_det, DLLs, dstore, low_haz=True)
        dstore['asce7'] = hdf5.dumps(asce7)
        asce41 = get_asce41(dstore, mce, facts)
        dstore['asce41'] = hdf5.dumps(asce41)
        if Image is None:  # missing PIL
            logging.warning('Missing module PIL: skipping plotting curves')
        else:
            plot_mean_hcurves_afe_rtgm(dstore, update_dstore=True)
            plot_governing_mce(dstore, update_dstore=True)
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
    logging.info('ASCE-41=%s' % asce41)
    logging.info('ASCE-7=%s' % asce7)

    if Image is None:  # missing PIL
        logging.warning('Missing module PIL: skipping plotting curves')
    else:
        plot_mean_hcurves_afe_rtgm(dstore, update_dstore=True)
        plot_disagg_by_src(dstore, update_dstore=True)
        plot_governing_mce(dstore, update_dstore=True)
