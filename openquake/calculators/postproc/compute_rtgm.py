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
from scipy import interpolate
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import contexts
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.calculators import postproc

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
imts = ['PGA', 'SA(0.2)', 'SA(1.0)']
D = DLL_df.BC.loc  # site class BC for vs30=760m/s
DLLs = [D[imt] for imt in imts]
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

def _find_fact_maxC(T,code):
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


def calc_rtgm_df(rtgm_haz, oq):
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    :param rtgm_haz: a dictionary containing the annual frequency losses
    :param oq: OqParam instance
    """
    M = len(imts)
    riskCoeff, RTGM, UHGM, RTGM_max, MCE = (
        np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M))
    results = rtgmpy.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')
    IMTs = []
    for m, imt in enumerate(imts):
        IMT = norm_imt(imt)
        IMTs.append(IMT)
        T = from_string(imt).period
        rtgmCalc = results['RTGM'][IMT]['rtgmCalc']
        fact = _find_fact_maxC(T, 'ASCE7-16')
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
    dic =  {'IMT': IMTs,
            'UHGM_2475yr-GM': UHGM,
            'RTGM': RTGM_max,
            'ProbMCE': MCE,
            'RiskCoeff': riskCoeff,
            'DLL': DLLs,
            'MCE>DLL?': RTGM_max > DLLs}
    return pd.DataFrame(dic)


def get_hazdic(hcurves, imtls, invtime, sitecol):
    """
    Convert an array of mean hazard curves into a dictionary suitable
    for the rtgmpy library

    :param hcurves: array of PoEs of shape (N, M, L1)
    """
    [site] = sitecol  # there must be a single site
    hazdic = {
        'site': {'name': 'site',
                 'lon': site.location.x,
                 'lat': site.location.y,
                 'Vs30': site.vs30},
        'hazCurves': {norm_imt(imt): {'iml': imtls[imt],
                                      'afe': to_rates(hcurves[0, m], invtime)}
                      for m, imt in enumerate(imtls) if imt in imts}}
    return hazdic


def calc_deterministic(cmaker, msr, site, mag, dist, disagg, rtgm):
    """
    :param cmaker: a ContextMaker
    :param msr: a MSR instance
    :param site: a hazard site
    :param mag: a magnitude scalar
    :param dist: a vector of D distances
    :param disagg: an array of shape (D, E, M)
    :returns: an array of shape (G, M)
    """
    sigma = cmaker.get_att_curves(site, msr, mag)[1]
    sig = sigma(dist)  # shape (G, M, N)
    det= rtgm[m] * np.exp(sig[g, m]) / np.exp(eps[m]*sig[g, m])
    return det


def get_msr(sources, src_id):
    """
    :returns: the MSR of the first source named src_id
    """
    msrs = []
    for src in sources:
        if src.source_id.startswith(src_id):
            msrs.append(src.magnitude_scaling_relationship)
    return msrs[0]


def main(dstore, csm):
    """
    :param dstore: datastore with the classical calculation
    """
    if not rtgmpy:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    logging.info('Computing Risk Targeted Ground Motion')
    oq = dstore['oqparam']
    assert list(oq.hazard_stats()) == ['mean'], oq.hazard_stats()
    sitecol = dstore['sitecol']
    hcurves = dstore['hcurves-stats'][:, 0]  # shape NML1
    hazdic = get_hazdic(hcurves, oq.imtls, oq.investigation_time, sitecol)
    rtgm_haz = rtgmpy.GroundMotionHazard.from_dict(hazdic)
    rtgm_df = calc_rtgm_df(rtgm_haz, oq)
    rtgm = list(rtgm_df.RTGM)
    logging.info('Computed RTGM\n%s', rtgm_df)
    dstore.create_df('rtgm', rtgm_df)
    if (rtgm_df.ProbMCE < DLLs).all():  # do not disaggregate by rel sources
        return
    mean_disagg_by_src = postproc.disagg_by_rel_sources.main(
        dstore, csm, imts, rtgm)
    cmakers = contexts.read_cmakers(dstore, csm)
    info = dstore['source_info'][:][['source_id', 'grp_id']]
    grp_id = {src_id.decode('utf8'): grp_id for src_id, grp_id in info}
    [site] = sitecol
    for src_idx, src_id in enumerate(mean_disagg_by_src.source_id):
        cmaker = cmakers[grp_id[src_id]]
        msr = get_msr(csm.src_groups[grp_id[src_id]], src_id)
        for mag_idx, mag in enumerate(mean_disagg_by_src.mag):
            dist = mean_disagg_by_src.dist
            disagg = mean_disagg_by_src[src_idx, mag_idx]  # shape (D, E, M)
            # det = calc_deterministic(
            #     cmaker, msr, site, mag, dist, disagg, rtgm)
