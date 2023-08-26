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
rtgmpy module from the USGS.

Useful abbreviations:

- RTGM: Risk Targeted Ground Motion (for geometric mean)
- RTGM_max: Risk Targeted Ground Motion (for maximum component)
- MCE: Maximum Considered Earthquake
- ProbMCE: Probabilistic Maximum Considered Earthquake (UHGM for PGA)
- IMT: the list of IMTs as normalized strings
- UHGM: Uniform Hazard Spectra
- RiskCoeff: RTGM / UHGM_2475y
- DLL: Deterministic Lower Limit

T Site Class A B BC C CD D DE E
0.00 0.50 0.57 0.66 0.73 0.74 0.69 0.61 0.55
0.01 0.50 0.57 0.66 0.73 0.75 0.70 0.62 0.55
0.02 0.52 0.58 0.68 0.74 0.75 0.70 0.62 0.55
0.03 0.60 0.66 0.75 0.79 0.78 0.70 0.62 0.55
0.05 0.81 0.89 0.95 0.96 0.89 0.76 0.62 0.55
0.075 1.04 1.14 1.21 1.19 1.08 0.90 0.71 0.62
0.10 1.12 1.25 1.37 1.37 1.24 1.04 0.82 0.72
0.15 1.12 1.29 1.53 1.61 1.50 1.27 1.00 0.87
0.20 1.01 1.19 1.50 1.71 1.66 1.44 1.15 1.01
0.25 0.90 1.07 1.40 1.71 1.77 1.58 1.30 1.15
0.30 0.81 0.98 1.30 1.66 1.83 1.71 1.44 1.30
0.40 0.69 0.83 1.14 1.53 1.82 1.80 1.61 1.48
0.50 0.60 0.72 1.01 1.38 1.73 1.80 1.68 1.60
0.75 0.46 0.54 0.76 1.07 1.41 1.57 1.60 1.59
1.0 0.37 0.42 0.60 0.86 1.17 1.39 1.51 1.58
1.5 0.26 0.29 0.41 0.60 0.84 1.09 1.35 1.54
2.0 0.21 0.23 0.31 0.45 0.64 0.88 1.19 1.46
3.0 0.15 0.17 0.21 0.31 0.45 0.63 0.89 1.11
4.0 0.12 0.13 0.16 0.24 0.34 0.47 0.66 0.81
5.0 0.10 0.11 0.13 0.19 0.26 0.36 0.49 0.61
7.5 0.063 0.068 0.080 0.11 0.15 0.19 0.26 0.31
10 0.042 0.045 0.052 0.069 0.089 0.11 0.14 0.17
PGAG 0.37 0.43 0.50 0.55 0.56 0.53 0.46 0.42 

# PGA_G: PGA for Geometric Mean (no Risk Targeted)
# PGA: PGA for Maximum Component

"""
import logging
import numpy as np
import pandas as pd
from scipy import interpolate
try:
    import rtgmpy as rtg
except ImportError:
    rtg = None
from openquake.hazardlib.calc.mean_rates import to_rates


def _find_fact_maxC(T,code):
    # find the factor to convert to maximum component based on
    # ASCE7-16 and ASCE7-22
    if code == 'ASCE7-16':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.1
        elif T <= 1:
            f = interpolate.interp1d([0.2,1],[1.1, 1.3])
            fact_maxC = f(T)
        elif T <= 5:
            f = interpolate.interp1d([1,5],[1.3, 1.5])
            fact_maxC = f(T)
        else:
            fact_maxC = 1.5
    elif code == 'ASCE7-22':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.2
        elif T <= 1:
            f = interpolate.interp1d([0.2,1],[1.2, 1.25])
            fact_maxC = f(T)
        elif T <= 10:
            f = interpolate.interp1d([1,5],[1.25, 1.3])
            fact_maxC = f(T)
        else:
            fact_maxC = 1.5
    return fact_maxC


def calc_rtgm_df(rtgm_haz, oq):
    # Obtaining Risk-Targeted Ground Motions from hazard curves
    M = len(oq.imtls)
    export_rtgm = []
    riskCoeff = np.zeros(M)
    RTGM, UHGM, RTGM_max, MCE = (np.zeros(M), np.zeros(M),
                                 np.zeros(M), np.zeros(M))
    results = rtg.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')
    for m, imt in enumerate(oq.imtls):
        IMT = norm_imt(imt)
        rtgmCalc = results['RTGM'][IMT]['rtgmCalc']
        T = imt.period
        fact = _find_fact_maxC(T, 'ASCE7-16')
        RTGM[m] = rtgmCalc['rtgm'] / fact
        RTGM_max[m] = rtgmCalc['rtgm']
        UHGM[m] = rtgmCalc['uhgm'] / fact  # back to GM
        riskCoeff[m] = rtgmCalc['riskCoeff']
        # note that RTGM_max is the ProbMCEr, while RTGM is used for the
        # identification of the sources as the hazard curves are in
        # geometric mean
        if imt == 'PGA':
            RTGM[m] = UHGM[m]
            MCE[m] = RTGM[m]  # UHGM in terms of GM: MCEg   
        else:
            MCE[m] = RTGM_max[m]   
        # this is saved for the next step.
        export_rtgm.append(str(imt) + ': ' + str(RTGM[m]))
    print(export_rtgm)
    imts = np.array(['PGA', 'SA(0.2)','SA(1.0)']) # hard-coded for year 1
    limit_det = np.array([0.5, 1.5, 0.6])
    if (MCE < limit_det).all():
        dic =  {'IMT': [norm_imt(imt) for imt in oq.imtls],
                'UHGM_2475yr-GM': UHGM,
                'RTGM': RTGM_max,
                'ProbMCE': MCE,
                'RiskCoeff': riskCoeff,
                'DLL': limit_det,
                'MCE>DLL?': RTGM_max > limit_det,
                'GoverningMCE': MCE}
    else:
        raise NotImplementedError
    return pd.DataFrame(dic)

    
def norm_imt(imt):
    """
    Normalize the imt string to the USGS format, for instance SA(1.1) -> SA1P1
    """
    return imt.replace('(', '').replace(')', '').replace('.', '')


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
                      for m, imt in enumerate(imtls)}}
    return hazdic


def main(dstore):
    """
    :param dstore: datastore with the classical calculation
    """
    if not rtg:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
        return
    logging.info('Computing Risk Targeted Ground Motion')
    oq = dstore['oqparam']
    assert list(oq.hazard_stats()) == ['mean'], oq.hazard_stats()
    sitecol = dstore['sitecol']
    hcurves = dstore['hcurves-stats'][:, 0]  # shape NML1
    hazdic = get_hazdic(hcurves, oq.imtls, oq.investigation_time, sitecol)
    rtgm_haz = rtg.GroundMotionHazard.from_dict(hazdic)
    df = calc_rtgm_df(rtgm_haz, oq)
    dstore.create_df('rtgm', df)
