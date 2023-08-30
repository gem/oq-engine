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
- PGA_G: PGA for Geometric Mean (no Risk Targeted)
- PGA: PGA for Maximum Component
"""
import os
import logging
import numpy as np
import pandas as pd
from scipy import interpolate
try:
    import rtgmpy as rtg
except ImportError:
    rtg = None
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.calculators import postproc

def norm_imt(imt):
    """
    Normalize the imt string to the USGS format, for instance SA(1.1) -> SA1P1,
    PGAG -> PGA
    """
    return imt.replace('(', '').replace(')', '').replace('.', '').replace(
        'G', '')

# hard-coded for year 1
# TODO: interpolate for vs30 != 760 and for different periods
imts = ['PGAG', 'SA(0.2)', 'SA(1.0)']
IMTs = [norm_imt(im) for im in imts]
Ts = [0, 0.2, 1.0]

DLL_csv = os.path.join(os.path.dirname(__file__),
                       'deterministic_lower_limit.csv')
DLL_df = pd.read_csv(DLL_csv, index_col='imt')
D = DLL_df.BC.loc  # site class BC for vs30=760m/s
DLLs = np.array([D[imt] for imt in imts])  # [0.5, 1.5, 0.6]


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
    """
    Obtaining Risk-Targeted Ground Motions from the hazard curves.

    :param rtgm_haz: a dictionary containing the annual frequency losses
    :param oq: OqParam instance
    """
    M = len(IMTs)
    riskCoeff, RTGM, UHGM, RTGM_max, MCE = (
        np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M))
    results = rtg.BuildingCodeRTGMCalc.calc_rtgm(rtgm_haz, 'ASCE7')
    for m, IMT in enumerate(IMTs):
        rtgmCalc = results['RTGM'][IMT]['rtgmCalc']
        T = Ts[m]
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
                      for m, imt in enumerate(imtls) if norm_imt(imt) in IMTs}}
    return hazdic


def main(dstore, csm):
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
    if (df.ProbMCE < DLLs).all():  # do not disaggregate by relevant sources
        return
    postproc.disagg_by_rel_sources.main(dstore, csm, IMTs, list(df.RTGM))
