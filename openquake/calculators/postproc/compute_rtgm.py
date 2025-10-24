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
from openquake.baselib import hdf5, general, python3compat
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.calculators import postproc
from openquake.calculators.postproc.aelo_plots import (
    plot_mean_hcurves_rtgm, plot_disagg_by_src,
    plot_governing_mce_asce_7_16, plot_mce_spectra,
    plot_governing_mce, plot_sites, _find_fact_maxC, import_plt)

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
        ' since it is below the DLLs. Outputs specific to the deterministic'
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


def _get_hazdic(afe, imt, imtls, site):
    hazdic = {
        'site': {'name': 'site',
                 'lon': site.location.x,
                 'lat': site.location.y,
                 'Vs30': site.vs30},
        'hazCurves': {imt: {'iml': imtls, 'afe': afe}}}
    return hazdic


def calc_rtgm_df(hcurves, site, site_idx, oq, ASCE_version):
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    # FIXME: update docstring params and return values

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
    elif mean_rates.max() < MIN_AFE:
        # in this case all hazard curves for all SA are below 1/2475
        # for the lower IML
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


def to_array(dic):
    return np.array([hdf5.dumps(dic[sid]) for sid in sorted(dic)])


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
    ordinates = list(ordinates)
    periods = list(periods)
    # For sds, find periods from 0.2-5.0s, inclusive
    sds_indices = [index for index, period in enumerate(periods)
                   if 0.2 <= period <= 5]
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

    def get_mce(self, DLLs, rtgm, sid, vs30, low_haz=False):
        """
        Computes deterministic and probabilistic MCE and prepares the MCE
        DataFrame. The ASCE7 formatting is now separated into another method.

        :param DLLs: deterministic lower limits according to ASCE 7-22
        :param rtgm: dataframe with ProbMCE and RiskCoeff
        :param sid: site ID
        :param vs30: shear wave velocity
        :param low_haz: boolean specifying if the hazard is lower than DLLs
        :returns: dict (imt -> probabilistic MCE),
                  dict (imt -> governing MCE),
                  dict (imt -> deterministic MCE),
                  pandas DataFrame with MCEs
    """
        det_imt = self.det_imt
        job_imts = self.job_imts
        prob_mce = rtgm.ProbMCE.to_numpy()

        det_mce = {}
        mce = {}
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

        dic_mce = {
            'IMT': job_imts,
            'DLL': DLLs,
            'ProbMCE': prob_mce,
            'DetMCE': det_mce.values(),
            'MCE': mce.values(),
            'sid': [sid] * len(job_imts)
        }
        mce_df = pd.DataFrame(dic_mce)

        return prob_mce_out, mce, mce_df

    def calc_mce(dstore, csm, job_imts, DLLs, rtgm):
        """
        :yields: (sid, mag_dst_eps_sig, mce_df)
        """
        oq = dstore['oqparam']
        imls_by_sid = {sid: rtgm_df.ProbMCE.to_numpy() / rtgm_df.fact.to_numpy()
                       for sid, rtgm_df in rtgm.items() if rtgm_df}
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
            _prob_mce_out, mce, mce_df = mg.get_mce(
                DLLs[sid], rtgm_df, sid, vs30)
            logging.info('(%.1f,%.1f) Computed MCE: high hazard\n%s', lon, lat,
                         mce_df)
            logging.info(f'(%.1f,%.1f) {mce=}', lon, lat)
            yield sid, mag_dst_eps_sig, mce_df


def compute_mce_governing(dstore, sitecol, locs):
    """
    Note that for ASCE7-22 and default site class the site is multiplied
    3 times with different values of the vs30 and the MCE is computed as
    the maximum MCE across the sites for each IMT. For all other site class,
    the same mce computed before is used.
    """
    # fields IMT, DLL, ProbMCE, DetMCE, MCE, sid
    mce_df = dstore.read_df('mce')
    mce_df['period'] = [from_string(x).period for x in mce_df.IMT]
    del mce_df['IMT']
    out = []
    for sids in locs.values():
        csi = sitecol.custom_site_id[sids[0]].decode('ascii').split(':')[0]
        mcedf = mce_df[np.isin(mce_df.sid, sids)]
        df = mcedf.groupby('period').MCE.max().to_frame()  # MCE by period
        df['custom_site_id'] = csi
        out.append(df)
    return pd.concat(out).reset_index()


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
            logging.info('(%.1f,%.1f) Computed MCE: Zero hazard\n%s', loc.x,
                         loc.y, mce_df)
        elif notification_name in ['below_min', 'only_prob_mce']:
            _prob_mce_out, mce, mce_df = mg.get_mce(
                DLLs[sid], rtgm_df, sid, vs30, low_haz=True)
            logging.info('(%.1f,%.1f) Computed MCE: Only Prob\n%s', loc.x,
                         loc.y, mce_df)
        else:
            mce_df = None
        yield site, rtgm_df, mce_df, notification_name


#class ASCE7Calculator:
def get_seismicity_class(mce_site, vs30):
        if vs30 == 760:
            sa02 = mce_site[mce_site.period==0.2]['SaM'].iloc[0]
            sa10 = mce_site[mce_site.period==1.0]['SaM'].iloc[0]
            Ss_seismicity = (
                "Low" if sa02 < 0.25 else
                "Moderate" if sa02 < 0.5 else
                "Moderately High" if sa02 < 1.0 else
                "High" if sa02 < 1.5 else
                "Very High"
            )
            S1_seismicity = (
                "Low" if sa10 < 0.1 else
                "Moderate" if sa10 < 0.2 else
                "Moderately High" if sa10 < 0.4 else
                "High" if sa10 < 0.6 else
                "Very High"
            )
        else:
            Ss_seismicity = "n.a."
            S1_seismicity = "n.a."
        return Ss_seismicity, S1_seismicity


def asce07_output_new(sid, vs30, dstore, mce_site):
    """
    Formats the final ASCE 7 dictionary including seismicity classification.
    """

    oq = dstore['oqparam']
    ASCE_version = oq.asce_version
    job_imts = list(oq.imtls)
    sitecol = dstore['sitecol']
    period_mce = mce_site["period"]
    mce = mce_site.SaM
    Ss_seismicity, S1_seismicity = get_seismicity_class(mce_site, vs30)
        
    if mce_site[mce_site.period==0]['SaM'].iloc[0] < min(oq.imtls['PGA']):
        pga_out = '<' + str(min(oq.imtls['PGA']))
    else:
        pga_out = mce_site[mce_site.period==0]['SaM'].iloc[0]
            
    if mce_site[mce_site.period==0.2]['SaM'].iloc[0] < min(oq.imtls['SA(0.2)']):
        sa02_out = '<' + str(min(oq.imtls['SA(0.2)']))
    else:
        sa02_out = mce_site[mce_site.period==0.2]['SaM'].iloc[0]
            
    if mce_site[mce_site.period==1.0]['SaM'].iloc[0] < min(oq.imtls['SA(1.0)']):
        sa1_out = '<' + str(min(oq.imtls['SA(1.0)']))
    else:
        sa1_out = mce_site[mce_site.period==1.0]['SaM'].iloc[0]
            
    if ASCE_version == 'ASCE7-16':

        asce07 = {
            'PGA': pga_out,
            'Ss': sa02_out, 'Ss_seismicity': Ss_seismicity,
            'S1': sa1_out,  'S1_seismicity': S1_seismicity
        }
    else:
        design = calc_sds_and_sd1(period_mce.tolist(), mce.tolist(), vs30)

        if design[2] < min(oq.imtls['SA(0.2)']):
            sms_out =  '<' + str(min(oq.imtls['SA(0.2)']))
            sds_out =  '<' + str(min(oq.imtls['SA(0.2)']))
        else:
            sms_out =  design[2]
            sds_out = design[0]

        if design[3] < min(oq.imtls['SA(0.2)']):
            sm1_out =  '<' + str(min(oq.imtls['SA(1.0)']))
            sd1_out =  '<' + str(min(oq.imtls['SA(1.0)']))
        else:
            sm1_out =  design[3]
            sd1_out = design[1]
                
        if vs30 == 760:
            asce07 = {
                'PGA_M': pga_out,
                'Ss': sa02_out, 'Sms': sms_out, 'Sds': sds_out,
                'Ss_seismicity': Ss_seismicity,
                'S1': sa1_out, 'Sm1': sm1_out, 'Sd1': sd1_out,
                'S1_seismicity': S1_seismicity
            }
        else:
            asce07 = {
                'PGA_M': pga_out,
                'Sms': sms_out, 'Sds': sds_out,
                'Ss_seismicity': 'n.a.',
                'Sm1': sm1_out, 'Sd1': sd1_out,
                'S1_seismicity': 'n.a.'
            }

    for key in asce07:
        if not isinstance(asce07[key], str):
            asce07[key] = smart_round(asce07[key])
    logging.info('ASCE 7=%s',  asce07)
    return asce07


def smart_round(number):
    """
    Round the ASCE values (if they are floats)
    """
    if isinstance(number, pd.Series):
        return round(float(number.iloc[0]), ASCE_DECIMALS)
    elif isinstance(number, str):
        return number
    elif np.isnan(number):
        return 'n.a.'
    else:
        return round(number, ASCE_DECIMALS)


def get_zero_hazard_asce07(dstore,vs30):
    oq = dstore['oqparam'] 
    ASCE_version = oq.asce_version
    na = 'n.a.'

    if ASCE_version == 'ASCE7-16':
            asce07 = {
                'PGA': na,  
                'Ss': na, 'Ss_seismicity': 'Low',
                'S1': na,  'S1_seismicity': 'Low'
            }
    else:
        if vs30 == 760:
            asce07 = {
                'PGA_M': na, 
                'Ss': na, 'Sms': na, 'Sds': na,
                'Ss_seismicity': 'Low',
                'S1': na, 'Sm1': na, 'Sd1': na,
                'S1_seismicity': 'Low'
            }
        else:
            asce07 = {
                'PGA_M':na, 
                'Sms': na, 'Sds': na,
                'Ss_seismicity': na,
                'Sm1': na, 'Sd1': na,
                'S1_seismicity': na
            }

    return asce07


def get_spectra(dstore, sid, custom_id, mce, facts):
    hmap = dstore["hmaps-stats"][sid, 0]  # shape (M, P)
    oq = dstore['oqparam']
    poes = oq.poes
    imts = list(oq.imtls)
    periods = [from_string(imt).period for imt in imts]
    
    if int(oq.investigation_time) == 1:
        poe5_50 = poes.index(0.001025)
        poe20_50 = poes.index(0.004453)
        poe10_50 = poes.index(0.002105)
    elif int(oq.investigation_time) == 50:
        poe5_50 = poes.index(0.05)
        poe20_50 = poes.index(0.2)
        poe10_50 = poes.index(0.1)

    BSE2N = mce
    BSE1N = [2 / 3 * val for val in mce]
    BSE2E_uhs = [f * h for f, h in zip(facts, hmap[:, poe5_50])]
    BSE2E = [min(n, e) for n, e in zip(BSE2N, BSE2E_uhs)]
    BSE1E_uhs = [f * h for f, h in zip(facts, hmap[:, poe20_50])]
    BSE1E = [min(n, e) for n, e in zip(BSE1N, BSE1E_uhs)]
    uhs_475 = hmap[:, poe10_50]
    
    sa_data = {'custom_site_id': [custom_id] * len(imts),
               'sid': [sid] * len(imts),
               'IMT': imts,
               'period': periods,
               'BSE2N': BSE2N,
               'BSE2E': BSE2E,
               'BSE1N': BSE1N,
               'BSE1E': BSE1E,
               'uhs_475': uhs_475}
    
    return sa_data


def get_params(asce_version, vs30, asce_sa, ASCE_DECIMALS):
    if asce_version == 'ASCE7-16':
        return asce41_17(asce_sa, ASCE_DECIMALS)
    elif asce_version == 'ASCE7-22':
        return asce41_23(asce_sa, vs30, ASCE_DECIMALS)


def asce41_17(sa_data, ASCE_DECIMALS):
    period02 = sa_data[sa_data['period'] == 0.2]
    period1 = sa_data[sa_data['period'] == 1.0]
    return {
        "BSE2N_Ss": smart_round(period02['BSE2N']),
        "BSE2E_Ss": smart_round(period02["BSE2E"]),
        "BSE1N_Ss": smart_round(period02["BSE1N"]),
        "BSE1E_Ss": smart_round(period02["BSE1E"]),
        "BSE2N_S1": smart_round(period1["BSE2N"]),
        "BSE2E_S1": smart_round(period1["BSE2E"]),
        "BSE1N_S1": smart_round(period1["BSE1N"]),
        "BSE1E_S1": smart_round(period1["BSE1E"]),
    }

def asce41_23(sa_data, Vs30, ASCE_DECIMALS):
    
    if (sa_data['BSE2N'] == 0).all():
        design_BSE2N = ['n.a.','n.a.','n.a.','n.a.']
    else:
        design_BSE2N = calc_sds_and_sd1(
            sa_data['period'], sa_data['BSE2N'], Vs30)
        
    if (sa_data['BSE1N'] == 0).all():
        design_BSE1N = ['n.a.','n.a.','n.a.','n.a.']
    else:    
        design_BSE1N = calc_sds_and_sd1(
            sa_data['period'], sa_data['BSE1N'], Vs30)
        
    if (sa_data['BSE2E'] == 0).all():
        design_BSE2E = ['n.a.','n.a.','n.a.','n.a.']
    else:
        design_BSE2E = calc_sds_and_sd1(
            sa_data['period'], sa_data['BSE2E'], Vs30)
        
    if (sa_data['BSE1E'] == 0).all():
        design_BSE1E = ['n.a.','n.a.','n.a.','n.a.']
    else:
        design_BSE1E = calc_sds_and_sd1(
            sa_data['period'], sa_data['BSE1E'], Vs30)

    return {
        'BSE2N_Sxs': smart_round(design_BSE2N[2]),
        'BSE2E_Sxs': smart_round(design_BSE2E[2]),
        'BSE1N_Sxs': smart_round(design_BSE1N[2]),
        'BSE1E_Sxs': smart_round(design_BSE1E[2]),
        'BSE2N_Sx1': smart_round(design_BSE2N[3]),
        'BSE2E_Sx1': smart_round(design_BSE2E[3]),
        'BSE1N_Sx1': smart_round(design_BSE1N[3]),
        'BSE1E_Sx1': smart_round(design_BSE1E[3])
    }


def get_zero_hazard_asce41(asce_version):
    na = 'n.a.'
    if asce_version == 'ASCE7-16':
        keys = [
            'BSE2N_Ss', 'BSE2E_Ss', 
            'BSE1N_Ss', 'BSE1E_Ss', 
            'BSE2N_S1', 'BSE2E_S1', 
            'BSE1N_S1', 'BSE1E_S1', 
        ]
    else:
        keys = [
            'BSE2N_Sxs', 'BSE2E_Sxs',
            'BSE1N_Sxs', 'BSE1E_Sxs',
            'BSE2N_Sx1', 'BSE2E_Sx1',
            'BSE1N_Sx1', 'BSE1E_Sx1'
        ]
    return {key: na for key in keys}

def compute_max_sa_asce41(dstore,sitecol,locs):
    # replace the maximum per each poe for sites in the default site class
    keys_asce41 = ['BSE2N','BSE2E','BSE1N','BSE1E','uhs_475']
    
    asce41_df = dstore.read_df('spectra_asce41')
    asce41_df['period'] = [from_string(x).period for x in asce41_df.IMT]
    del asce41_df['IMT']
    out = []
    for sids in locs.values():

        csi = sitecol.custom_site_id[sids[0]].decode('ascii').split(':')[0]
        asce41df = asce41_df[np.isin(asce41_df.sid, sids)]
        df = asce41df.groupby('period')[keys_asce41].max()
        df['custom_site_id'] = csi
        out.append(df)
    return pd.concat(out).reset_index()


def calc_mce(dstore, csm, job_imts, DLLs, rtgm, ASCE_version):
    """
    :yields: (sid, mag_dst_eps_sig, mce_df)
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
        _prob_mce_out, mce, mce_df = mg.get_mce(
            DLLs[sid], rtgm_df, sid, vs30)
        logging.info('(%.1f,%.1f) Computed MCE: high hazard\n%s', lon, lat,
                     mce_df)
        logging.info(f'(%.1f,%.1f) {mce=}', lon, lat)

        yield (sid, mag_dst_eps_sig, mce_df)


def save_figure_to_dstore(fig, dstore, key):
    """
    Save a matplotlib figure to the datastore as a PNG image.

    :param fig: The matplotlib figure object
    :param dstore: The datastore to write to
    :param key: The key under which to store the PNG (e.g., 'png/fig1.png')
    """
    from PIL import Image
    bio = io.BytesIO()
    fig.savefig(bio, format='png', bbox_inches='tight')
    bio.seek(0)
    dstore[key] = Image.open(bio)


def add_footer_referencing_user_guide(fig):
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.text(0.5, 0.015,  # y = 0.015 is the vertical position of the footer
             'See WebUI User Guide for complete explanation of plot contents.',
             ha='center', fontsize='small', color='black', alpha=0.85)


def display_vs30_in_subplot_title(axes, n_rows, sid_idx, vs30):
    for row in range(n_rows):
        axes[row, sid_idx].set_title("$V_{S30}$ = %s m/s" % vs30, fontsize=13)


def make_figure_hcurves(plt, sids, dstore, notifications, vs30s):
    n_rows = 1
    n_sids = len(sids)
    fig, axes = plt.subplots(
        n_rows, n_sids, figsize=(7 * n_sids, 6), squeeze=False)
    for i, sid in enumerate(sids):
        vs30 = vs30s[i]
        plot_mean_hcurves_rtgm(dstore, sid, axes=axes[0, i])
        display_vs30_in_subplot_title(axes, n_rows, i, vs30)
    add_footer_referencing_user_guide(fig)
    save_figure_to_dstore(fig, dstore, 'png/hcurves.png')
    plt.close(fig)


def make_figure_disagg_by_src(plt, sids, dstore, vs30s):
    n_rows = 3  # 3 imts: [PGA, SA(0.2), SA(1.0)]
    n_sids = len(sids)
    fig, axes = plt.subplots(
        n_rows, n_sids, figsize=(7 * n_sids, 15), squeeze=False)
    for i, sid in enumerate(sids):
        vs30 = vs30s[i]
        plot_disagg_by_src(
            dstore, sid, axes=[axes[0, i], axes[1, i], axes[2, i]])
        display_vs30_in_subplot_title(axes, n_rows, i, vs30)
    has_data = any(ax.has_data() for row in axes for ax in row)
    if has_data:
        add_footer_referencing_user_guide(fig)
        fig.subplots_adjust(hspace=0.3)  # avoid overlapping titles and xlabels
        save_figure_to_dstore(fig, dstore, 'png/disagg_by_src-All-IMTs.png')
    plt.close(fig)


def make_figure_sites(dstore, oq, locs, sitecol, notifications):
    [sids] = locs.values()
    n_sids = len(sids)
    vs30s = list(sitecol['vs30'])
    assert n_sids == len(vs30s), (
        f'The number of sites ({n_sids}) must be equal to'
        f' the number of values of vs30 ({len(vs30s)})')
    plt = import_plt()
    # Mean Hazard Curves (1 row, n_sids columns)
    mask = np.isin(notifications['name'], ['zero_hazard', 'low_hazard'])
    sids_to_exclude = notifications['sid'][mask].tolist()
    sids_to_plot = [sid for sid in sids if sid not in sids_to_exclude]
    if sids_to_plot:
        make_figure_hcurves(plt, sids_to_plot, dstore, notifications, vs30s)
        # Governing MCE
        if oq.asce_version == 'ASCE7-16':
            plot_governing_mce_asce_7_16(dstore, update_dstore=True)
        elif n_sids == 1:
            plot_mce_spectra(dstore, update_dstore=True)
            plot_governing_mce(dstore, update_dstore=True)
            # in simplified page
        else:
            plot_governing_mce(dstore, update_dstore=True)
        # Disaggregation by Source (3 rows, n_sids columns)
        make_figure_disagg_by_src(plt, sids_to_plot, dstore, vs30s)

def define_unique_csi(custom_ids):
    unique_custom_ids = []
    seen = set()
    
    for item in custom_ids:
        key = item.split(':')[0]
        if key not in seen:
            seen.add(key)
            unique_custom_ids.append(key)
    return unique_custom_ids

def compute_asce07(dstore, mce_df, sitecol, custom_ids):
    # FIXME: in case of multiple sites on the same location
    # there will be duplications
    asce07 = {}
    unique_custom_ids = define_unique_csi(custom_ids)
    for s, custom_id in enumerate(unique_custom_ids):
        csi = custom_id.split(':')[0]
        mce_site = mce_df[mce_df['custom_site_id'] == csi]
        Vs30 = sitecol["vs30"][s]
        if np.all(mce_site.SaM == 0) or mce_site['SaM'].isna().all():
            result = get_zero_hazard_asce07(dstore,Vs30)
        else:
            result = asce07_output_new(custom_id, Vs30, dstore, mce_site)
        #result['custom_site_id'] = custom_id
        asce07[s] = result
    return asce07


def compute_asce41(dstore, mce_dfs, sitecol, facts, locs, custom_ids,
                   ASCE_version):
     # 1) get spectra asce41 for each sid and each Vs30
    asce41 = {}
    if mce_dfs:
        mce_df = dstore.read_df('mce')
    sa_asce41 = []  # list to collect DataFrames for each site
    for sid in sitecol['sids']:
        mce_df_site = mce_df[mce_df['sid'] == sid]['MCE']
        custom_id = sitecol[sitecol['sids'] == sid]['custom_site_id']
        # get single value
        # Get the spectra for this site
        uhs_asce41 = get_spectra(dstore, sid, custom_id, mce_df_site, facts)
        
        # Convert to DataFrame and reset index
        df_out = pd.DataFrame(uhs_asce41).reset_index(drop=True)
        sa_asce41.append(df_out)
        
        logging.info(f'{df_out=}')  # optional
    
    df_final = pd.concat(sa_asce41, ignore_index=True)
    df_final = df_final.astype(
        {col: "string" for col in df_final.select_dtypes("object").columns})
    df_final = df_final.reset_index(drop=True)
    dstore.create_df("spectra_asce41", df_final)

    # 2) compute max of asce41 spectra for default site class:
    asce41_spectra = compute_max_sa_asce41(dstore, sitecol, locs)
    asce41_spectra.columns = [
        'period', 'BSE2N', 'BSE2E', 'BSE1N', 'BSE1E', 'uhs_475',
        'custom_site_id']
    dstore.create_df('asce41_sa_final', asce41_spectra)

    # 3) compute asce41 parameters:
    keys_asce41 = ['BSE2N', 'BSE2E', 'BSE1N', 'BSE1E', 'uhs_475']
    asce41 = {}
    unique_custom_ids = define_unique_csi(custom_ids)
    for s, custom_id in enumerate(unique_custom_ids):
        csi = custom_id.split(':')[0]
        Vs30 = sitecol["vs30"][s]
        asce_sa = asce41_spectra[asce41_spectra['custom_site_id'] == csi]
        if asce_sa[keys_asce41].sum().any():
            result = get_params(ASCE_version, Vs30, asce_sa, ASCE_DECIMALS)
        else:
            result = get_zero_hazard_asce41(ASCE_version)
        result['custom_site_id'] = custom_id
        asce41[s] = result

    return asce41


def main(dstore, csm):
    """
    :param dstore: datastore with the classical calculation
    :param csm: a CompositeSourceModel instance
    """
    oq = dstore['oqparam']
    ASCE_version = oq.asce_version
    job_imts = list(oq.imtls)
    facts = []
    for m, imt in enumerate(job_imts):
        T = from_string(imt).period
        fact = 1 if imt == "PGA" else _find_fact_maxC(T, ASCE_version)
        facts.append(fact)
    sitecol = dstore['sitecol']
    DLLs = {site.id: get_DLLs(job_imts, site.vs30) for site in sitecol}
    if not rtgmpy:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    notification_items = []
    rtgm_dfs = []
    mce_dfs = []
    rtgm = {}
    locs = general.AccumDict(accum=[])  # lon, lat -> sids
    for site, rtgm_df, mce_df, notification_name in process_sites(
            dstore, csm, DLLs, ASCE_version):
        sid = site.id
        loc = site.location
        locs[loc.x, loc.y].append(sid)
        if mce_df is None:  # high hazard site requiring calc_mce
            rtgm[sid] = rtgm_df
        else:  # low hazard
            mce_dfs.append(mce_df)
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
            notification_items.append(
                (sid, level, notification_name, description))
        if rtgm_df is not None:
            rtgm_dfs.append(rtgm_df)
    notifications = np.array(notification_items, dtype=notification_dtype)

    for sid, mag_dst_eps_sig, mce_df in calc_mce(
            dstore, csm, job_imts, DLLs, rtgm, ASCE_version):
        dstore[f'mag_dst_eps_sig/{sid}'] = mag_dst_eps_sig
        mce_dfs.append(mce_df)

    if mce_dfs:
        dstore.create_df('mce', pd.concat(mce_dfs))
    if rtgm_dfs:
        dstore.create_df('rtgm', pd.concat(rtgm_dfs))

    # final MCE spectra
    df = compute_mce_governing(dstore, sitecol, locs)
    df.columns = ["period", "SaM", "custom_site_id"]
    dstore.create_df('mce_governing', df)
    sitecol = dstore['sitecol']
    custom_ids = python3compat.decode(sitecol['custom_site_id'])
    
    asce07 = compute_asce07(dstore, df, sitecol, custom_ids)
    dstore["asce07"] = to_array(asce07)

    asce41 = compute_asce41(dstore, mce_dfs, sitecol, facts, locs,
                            custom_ids, ASCE_version)
    dstore["asce41"] = to_array(asce41)
    if len(notifications):
        dstore['notifications'] = notifications

    plot_sites(dstore, update_dstore=True)
    if rtgm_dfs and len(locs) == 1:
        make_figure_sites(dstore, oq, locs, sitecol, notifications)
