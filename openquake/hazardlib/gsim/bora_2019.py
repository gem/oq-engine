# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.


"""
Module exports :class:`BoraEtAl2019`, :class:`BoraEtAl2019Drvt`
"""

import os
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import FAS, DRVT
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

B_COEFFS = os.path.join(os.path.dirname(__file__),
                          "bora_2019.csv")

B_DVRT_COEFFS = os.path.join(os.path.dirname(__file__),
                          "bora_2019_DVRT.csv")

CONSTANTS = {"r0": 1,
             "r1": 50,
             "Mh": 5.0,
             "Vc": 1100.,
             "Vref": 800.,
             "Mref": 4.5}

CONST_DURATION = {"M": 5.3,
                  "Vs30": 450}


def _get_source_term_duration(C, ctx):
    above = ctx.mag > CONST_DURATION['M']
    below = ctx.mag <= CONST_DURATION['M']
    fsource = np.zeros_like(ctx.mag)
    if np.any(below):
        fsource[below] = C['d1'] * ctx.mag[below]
    if np.any(above):
        fsource[above] =  (C['d1'] * CONST_DURATION['M'] +
                           C['d2'] * (ctx.mag[above] - CONST_DURATION['M']))
    return fsource


def _get_path_term_duration(C, ctx):
    return (C['d3'] + C['d4'] * (ctx.mag - 6)) * np.log(ctx.rrup)


def _get_site_term_duration(C, ctx):
    fsite = np.ones_like(ctx.vs30)
    below = ctx.vs30 <= CONST_DURATION['Vs30']
    above = ctx.vs30 > CONST_DURATION['Vs30']
    fsite[below] = C['d5'] * np.log(ctx.vs30[below])
    fsite[above] = C['d5'] * np.log(CONST_DURATION['Vs30'])
    return fsite


def _get_source_term(C, ctx):
    above = ctx.mag > CONSTANTS['Mh']
    below = ctx.mag <= CONSTANTS['Mh']
    fsource = np.zeros_like(ctx.mag)
    if np.any(above):
        fsource[above] = (C['c3'] * (ctx.mag[above] - CONSTANTS['Mh']) +
                          C['c2'] * (8.5 - ctx.mag[above])**2)
    if np.any(below):
        fsource[below] = (C['c1'] * (ctx.mag[below] - CONSTANTS['Mh']) +
                          C['c2'] * (8.5 - ctx.mag[below])**2)
    return fsource


def _get_finite_fault_factor(C, ctx):
    h = np.ones_like(ctx.mag)
    h[ctx.mag <= 4] = 2
    selec = (ctx.mag > 4) & (ctx.mag <= 5)
    h[selec] = C['c4'] - (C['c4'] - 1)*(5 - ctx.mag[selec])
    h[ctx.mag > 5] = C['c4']
    return h


def _get_path_term(C, ctx):
    fff = _get_finite_fault_factor(C, ctx)
    t1 = np.sqrt(ctx.rrup**2 + fff**2)
    t2 = np.sqrt(CONSTANTS['r1']**2 + fff**2)
    m = ctx.mag - CONSTANTS['Mref']
    g = np.ones_like(ctx.rrup)
    dshort = ctx.rrup <= 50
    dlong = ctx.rrup > 50
    g[dshort] = ((C['b1'] + C['c7']*m[dshort]) *
                 np.log(t1[dshort] / CONSTANTS['r0']))
    g[dlong] = ((C['b1'] + C['c7']*m[dlong]) *
                np.log(t2[dlong] / CONSTANTS['r0']) +
                (C['b2'] + C['c7']*m[dlong]) *
                np.log(t1[dlong] / t2[dlong]))
    fpath = g + C['c5'] * (t1 - CONSTANTS['r0'])
    return fpath


def _get_site_term(C, ctx):
    fsite = np.ones_like(ctx.vs30)
    below = ctx.vs30 < CONSTANTS['Vc']
    above = ctx.vs30 >= CONSTANTS['Vc']
    fsite[below] = C['c6']*np.log(ctx.vs30[below]/CONSTANTS['Vref'])
    fsite[above] = C['c6']*np.log(CONSTANTS['Vc']/CONSTANTS['Vref'])
    return fsite


def _get_mean_stddevs(C, ctx):
    mean = C['c0'] \
           + _get_source_term(C, ctx) \
           + _get_path_term(C, ctx) \
           + _get_site_term(C, ctx)
    phi = np.sqrt(C['phiss']**2 + C['phis2s']**2)
    tau = C['tau']
    sigma = np.sqrt(C['phiss']**2 + C['tau']**2 + C['phis2s']**2)
    return mean, sigma, tau, phi


class BoraEtAl2019(GMPE):
    """
    Implements the Fourier amplitude spectra model proposed by Bora et al.,
    2019 as described in Bora, S.S., Cotton, F., & Scherbaum, F. (2019).
    NGA-West2 empirical Fourier and duration models to generate adjustable
    response spectra.  Earthquake Spectra, 35(1), 61-93.
    """

    #: Supported tectonic region type is active shallow crust, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {FAS}

    #: Supported intensity measure component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation types
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT}

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measures
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m], sigma[m], tau[m], phi[m] = _get_mean_stddevs(C, ctx)

    COEFFS = CoeffsTable(sa_damping=5, table=open(B_COEFFS).read(), opt=1)


def _get_mean_stddevs_dur(C, ctx):
    mean = (C['d0'] + _get_source_term_duration(C, ctx) +
            _get_path_term_duration(C, ctx) + _get_site_term_duration(C, ctx))
    phi = np.sqrt(C['phi']**2 + C['phis2s']**2)
    tau = C['tau']
    sigma = np.sqrt(C['phi']**2 + C['tau']**2 + C['phis2s']**2)
    return mean, sigma, tau, phi


class BoraEtAl2019Drvt(BoraEtAl2019):
    """
    Implements the duration model proposed by Bora et al.,
    2019 as described in Bora, S.S., Cotton, F., & Scherbaum, F. (2019).
    NGA-West2 empirical Fourier and duration models to generate adjustable
    response spectra.  Earthquake Spectra, 35(1), 61-93.
    """

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {DRVT}

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m], sigma[m], tau[m], phi[m] = _get_mean_stddevs_dur(C, ctx)

    COEFFS = CoeffsTable(sa_damping=5, table=open(B_DVRT_COEFFS).read(), opt=1)
