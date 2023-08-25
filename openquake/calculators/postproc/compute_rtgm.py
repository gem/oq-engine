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

import logging
import numpy as np
from scipy import interpolate
try:
    import rtgmpy as rtg
except ImportError:
    rtg = None
from openquake.hazardlib.calc.mean_rates import to_rates


def _find_fact_maxC(T,code):
    # find the factor to convert to maximum component based on ASCE7-16  and ASCE7-22
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


def calc_rtgm(rtgm_haz, oq):
    # Obtaining Risk-Targeted Ground Motions from hazard curves
    M = len(oq.imtls)
    export_rtgm = []
    riskCoeff = np.zeros(M)
    RTGM, UHGM, RTGM_max, MCE = np.zeros(M), np.zeros(M), np.zeros(M), np.zeros(M)
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
        # identification of the sources as the hazard curves are in geometric mean
        if imt == 'PGA':
            RTGM[m] = UHGM[m]
            MCE[m] = RTGM[m]  # no RTGM for PGA! --> UHGM in terms of GM: MCEg   
        else:
            MCE[m] = RTGM_max[m]   
        # this is saved for the next step.
        export_rtgm.append(str(imt) + ': ' + str(RTGM[m]))
    print(export_rtgm)

    
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
    calc_rtgm(rtgm_haz, oq)
