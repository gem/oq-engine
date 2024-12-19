# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module exports :class:`BaylessAbrahamson2018`
"""
import os
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import EAS

BA_COEFFS = os.path.join(os.path.dirname(__file__),
                         "bayless_abrahamson_2018.csv")


def _magnitude_scaling(C, ctx):
    """ Compute the magnitude scaling term """
    t1 = C['c1']
    t2 = C['c2'] * (ctx.mag - 6.)
    tmp = np.log(1.0 + np.exp(C['cn']*(C['cM']-ctx.mag)))
    t3 = ((C['c2'] - C['c3']) / C['cn']) * tmp
    return t1 + t2 + t3


def _path_scaling(C, ctx):
    """ Compute path scaling term """
    tmp = np.maximum(ctx.mag-C['chm'], 0.)
    t1 = C['c4'] * np.log(ctx.rrup + C['c5'] * np.cosh(C['c6'] * tmp))
    tmp = (ctx.rrup**2 + 50.**2)**0.5
    t2 = (-0.5-C['c4'])*np.log(tmp)
    t3 = C['c7'] * ctx.rrup
    return t1 + t2 + t3


def _normal_fault_effect(C, ctx):
    """ Compute the correction coefficient for the normal faulting """
    idx = (ctx.rake > -150) & (ctx.rake < -30)
    fnm = np.zeros_like(ctx.rake)
    fnm[idx] = 1.0
    return C['c10'] * fnm


def _ztor_scaling(C, ctx):
    """ Compute top of rupture term """
    return C['c9'] * np.minimum(ctx.ztor, 20.)


def _get_ln_ir_outcrop(self, ctx):
    """
    Compute the natural logarithm of peak PGA at rock outcrop, Ir.
    See eq.10e page 2092.
    """
    # Set imt and cofficients. The value of frequency is consistent with
    # the one used in the matlab script - line 156
    im = EAS(5.0118725)
    tc = self.COEFFS[im]
    # Get mean
    mean = (_magnitude_scaling(tc, ctx) +
            _path_scaling(tc, ctx) +
            _ztor_scaling(tc, ctx) +
            _normal_fault_effect(tc, ctx))
    return 1.238 + 0.846 * mean


def _linear_site_response(C, ctx):
    """ Compute the site response term """

    tmp = np.minimum(ctx.vs30, 1000.)
    fsl = C['c8'] * np.log(tmp / 1000.)
    return fsl


def _get_basin_term(C, ctx, region=None):
    """ Compute the soil depth scaling term """
    # Set the c11 coefficient - See eq.13b at page 2093
    c11 = np.ones_like(ctx.vs30) * C['c11a']
    c11[(ctx.vs30 <= 300) & (ctx.vs30 > 200)] = C['c11b']
    c11[(ctx.vs30 <= 500) & (ctx.vs30 > 300)] = C['c11c']
    c11[(ctx.vs30 > 500)] = C['c11d']
    # Compute the Z1ref parameter
    tmp = (ctx.vs30**4 + 610**4) / (1360**4 + 610**4)
    z1ref = 1/1000. * np.exp(-7.67/4*np.log(tmp))
    # Return the fz1 parameter. The z1pt0 is converted from m (standard in OQ)
    # to km as indicated in the paper
    tmp = np.minimum(ctx.z1pt0/1000, np.ones_like(ctx.z1pt0)*2.0) + 0.01
    return c11 * np.log(tmp / (z1ref + 0.01))


def _get_stddevs(C, ctx):
    """
    Compute the standard deviations
    """
    # Set components of std
    tau = np.ones_like(ctx.mag) * C['s1']
    phi_s2s = np.ones_like(ctx.mag) * C['s3']
    phi_ss = np.ones_like(ctx.mag) * C['s5']
    above = ctx.mag > 6
    tau[above] = C['s2']
    phi_s2s[above] = C['s4']
    phi_ss[above] = C['s6']
    below = (ctx.mag > 4) & (ctx.mag <= 6)
    tau[below] = C['s1']+(C['s2']-C['s1'])/2.*(ctx.mag[below]-4)
    phi_s2s[below] = C['s3']+(C['s4']-C['s3'])/2.*(ctx.mag[below]-4)
    phi_ss[below] = C['s5']+(C['s6']-C['s5'])/2.*(ctx.mag[below]-4)

    # Collect the requested stds
    sigma = np.sqrt(tau**2+phi_s2s**2+phi_ss**2+C['c1a']**2)
    phi = np.sqrt(phi_s2s**2+phi_ss**2)

    sigma = np.ones_like(ctx.vs30) * sigma
    tau = np.ones_like(ctx.vs30) * tau
    phi = np.ones_like(ctx.vs30) * phi

    return sigma, tau, phi


def _get_nl_site_response(C, ctx, imt, ln_ir_outcrop, freq_nl, coeff_nl):
    """
    :param ln_ir_outcrop:
        The peak ground acceleration (PGA [g]) at rock outcrop
    :param freq_nl:
        Frequencies for the coefficients f3, f4 and f5 used to compute the
        non-linear term
    :param coeff_nl:
        A :class:`numpy.ndarray` instance of shape [# freq, 3] with the values
        of the coefficients f3, f4 and f5 which are used to compute the
        non-linear term
    """

    vsref = 760.0
    NSITES = len(ctx.vs30)
    NFREQS = coeff_nl.shape[0]

    # Updating the matrix with the coefficients. This has shape (number of
    # frequencies) x (number of coeffs) x (number of sites)
    coeff_nl = np.expand_dims(coeff_nl, 2)
    coeff_nl = np.repeat(coeff_nl, NSITES, 2)

    # Updating the matrix with Vs30 values. This has shape (number of
    # frequencies) x (number of sites)
    # vs30 = np.matlib.repmat(ctx.vs30, NFREQS, 1)
    # ln_ir_outcrop = np.matlib.repmat(ln_ir_outcrop, NFREQS, 1)
    vs30 = np.tile(ctx.vs30, (NFREQS, 1))
    ln_ir_outcrop = np.tile(ln_ir_outcrop, (NFREQS, 1))

    # Computing
    t1 = np.exp(coeff_nl[:, 2] * (np.minimum(vs30, vsref)-360.))
    t2 = np.exp(coeff_nl[:, 2] * (vsref-360.))
    f2 = coeff_nl[:, 1] * (t1 - t2)
    f3 = coeff_nl[:, 0]

    fnl_0 = f2 * np.log((np.exp(ln_ir_outcrop) + f3) / f3)
    idxs = np.argmin(fnl_0, axis=0)

    # Applying correction as described at page 2093 in BA18
    fnl = []
    for i, j in enumerate(idxs):
        fnl_0[j:, i] = min(fnl_0[:, i])
        tmp = np.interp(imt.frequency, freq_nl, fnl_0[:, i])
        fnl.append(tmp)
    return np.array(fnl)


def _get_dimunition_factor(ctx, imt):
    max_freq = 23.988321
    kappa = np.exp(-0.4*np.log(ctx.vs30/760)-3.5)
    D = np.exp(-np.pi * kappa * (imt.frequency - max_freq))
    return D


def _get_mean_linear(C, ctx):
    mean = (_magnitude_scaling(C, ctx) +
            _path_scaling(C, ctx) +
            _linear_site_response(C, ctx) +
            _ztor_scaling(C, ctx) +
            _normal_fault_effect(C, ctx) +
            _get_basin_term(C, ctx))
    return mean


def _get_mean(self, C, ctx, imt):
    if imt.frequency >= 24.:
        im = EAS(23.988321)
        C = self.COEFFS[im]
        t1 = np.exp(_get_mean_linear(C, ctx))
        mean = np.log(_get_dimunition_factor(ctx, imt) * t1)
    else:
        mean = _get_mean_linear(C, ctx)
    return mean


class BaylessAbrahamson2018(GMPE):
    """
    Implements the Bayless and Abrahamson (2018, 2019) model. References:
    - Bayless, J., and N. A. Abrahamson (2018b). An empirical model for Fourier
    amplitude spectra using the NGA-West2 database, PEER Rept. No. 2018/07,
    Pacific Earthquake Engineering Research Center, University of California,
    Berkeley, California.
    - Bayless, J. and N.A. Abrahamson (2019). Summary of the BA18
    Ground-Motion Model for Fourier Amplitude Spectra for Crustal Earthquakes
    in California.  Bull. Seism. Soc. Am., 109(5): 2088–2105

    Disclaimer: The authors describe a smoothing technique that needs to be
    applied to the non linear component of the site response. We did not
    implement these smoothing functions in this initial versions since the
    match with the values in the verification tables is good even without it.
    """

    #: Supported tectonic region type is active shallow crust, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {EAS}

    #: Supported intensity measure component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation types
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    }

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'ztor'}

    #: Required distance measures
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        freq_nl, coeff_nl = self.COEFFS.get_coeffs(['f3', 'f4', 'f5'])
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            ln_ir_outcrop = _get_ln_ir_outcrop(self, ctx)
            lin_component = _get_mean(self, C, ctx, imt)
            nl_component = _get_nl_site_response(C, ctx, imt, ln_ir_outcrop,
                                                 freq_nl, coeff_nl)
            mean[m] = (lin_component + nl_component)
            sigma[m], tau[m], phi[m] = _get_stddevs(C, ctx)

    with open(BA_COEFFS) as f:
        COEFFS = CoeffsTable(table=f.read())
