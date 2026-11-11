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

BA_COEFFS = os.path.join(os.path.dirname(__file__), "bayless_abrahamson_2018",
                         "bayless_abrahamson_2018.csv")

METRES_PER_KM = 1000.


def _magnitude_scaling(C, ctx):
    """
    Compute magnitude scaling; equation (8), p. 2091.
    """
    t1 = C['c1']
    t2 = C['c2'] * (ctx.mag - 6.)
    tmp = np.log(1.0 + np.exp(C['cn']*(C['cM']-ctx.mag)))
    t3 = ((C['c2'] - C['c3']) / C['cn']) * tmp
    return t1 + t2 + t3


def _path_scaling(C, ctx):
    """
    Compute path scaling; equation (9), p. 2091.
    """
    tmp = np.maximum(ctx.mag-C['chm'], 0.)
    t1 = C['c4'] * np.log(ctx.rrup + C['c5'] * np.cosh(C['c6'] * tmp))
    tmp = (ctx.rrup**2 + 50.**2)**0.5
    t2 = (-0.5-C['c4'])*np.log(tmp)
    t3 = C['c7'] * ctx.rrup
    return t1 + t2 + t3


def _normal_fault_effect(C, ctx):
    """
    Compute the normal-faulting term; equation (12), p. 2093.
    """
    idx = (ctx.rake > -150) & (ctx.rake < -30)
    fnm = np.zeros_like(ctx.rake)
    fnm[idx] = 1.0
    return C['c10'] * fnm


def _ztor_scaling(C, ctx):
    """
    Compute depth-to-top-of-rupture scaling; equation (11), p. 2093.
    """
    return C['c9'] * np.minimum(ctx.ztor, 20.)


def _get_ln_ir_outcrop(self, ctx):
    """
    Compute the natural logarithm of rock PGA, Ir, in g;
    equation (10e), p. 2092.

    NOTE: "The EAS at 5 Hz is used to estimate PGA because this is
    approximately the predominant frequency of the ground motions
    (response spectra generally "peak at T= 0.2 s) and should correlate
    strongly with the PGA" - p. 2093
    """
    # 5 Hz in paper but use exact value in matlab script (line 156)
    im = EAS(5.0118725)
    tc = self.COEFFS[im]

    # Get mean
    mean = (_magnitude_scaling(tc, ctx) +
            _path_scaling(tc, ctx) +
            _ztor_scaling(tc, ctx) +
            _normal_fault_effect(tc, ctx))
    
    return 1.238 + 0.846 * mean


def _linear_site_response(C, ctx):
    """
    Compute linear site response; equation (10b), p. 2092.
    """
    tmp = np.minimum(ctx.vs30, 1000.)
    fsl = C['c8'] * np.log(tmp / 1000.)
    return fsl


def _get_basin_term(C, ctx, region=None):
    """
    Compute soil-depth scaling; equations (13a)-(13c), p. 2093.
    """
    # Set the c11 coefficient - See eq.13b at page 2093
    c11 = np.ones_like(ctx.vs30) * C['c11a']
    c11[(ctx.vs30 <= 300) & (ctx.vs30 > 200)] = C['c11b']
    c11[(ctx.vs30 <= 500) & (ctx.vs30 > 300)] = C['c11c']
    c11[(ctx.vs30 > 500)] = C['c11d']
    
    # Compute the Z1ref parameter
    tmp = (ctx.vs30**4 + 610**4) / (1360**4 + 610**4)
    z1ref = np.exp(-7.67/4*np.log(tmp)) # in metres
    
    # Get z1pt0 (already in metres)
    z1pt0 = ctx.z1pt0.copy()
    
    # Use GMM's vs30 to z1pt0 for none-measured values
    mask = z1pt0 == -999
    z1pt0[mask] = z1ref[mask]
    
    # Return the fz1 parameter. The z1pt0 is converted from m (standard in OQ)
    # to km as indicated in the paper
    tmp = np.minimum(z1pt0/METRES_PER_KM, np.ones_like(z1pt0)*2.0) + 0.01
    return c11 * np.log(tmp / (z1ref/METRES_PER_KM + 0.01))


def _get_stddevs(C, ctx):
    """
    Compute total, between-event and within-event standard deviations;
    equations (18) and (19a)-(19c), p. 2099.
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


def _get_lowess_matrix(num_freqs):
    """
    Compute weights for MATLAB script's smooth2(Y, 20, 'lowess'), which fits
    local lines against sample index and includes all points tied at the
    distance to the twentieth neighbour.
    """
    indices = np.arange(num_freqs)
    span = min(20, num_freqs)
    matrix = np.zeros((num_freqs, num_freqs))
    for i in indices:
        distance = np.abs(indices - i)
        selected = distance <= np.partition(distance, span - 1)[span - 1]
        x = indices[selected] - i
        dmax = max(np.max(np.abs(x)), 1)
        # MATLAB scrppt weights both the design matrix and the observations
        weight = (1 - (np.abs(x) / dmax)**3)**1.5
        design = np.column_stack((np.ones(len(x)), x)) * weight[:, None]
        matrix[i, selected] = np.linalg.lstsq(
            design, np.diag(weight), rcond=None)[0][0]
    return matrix


def _get_nl_site_response(ctx, ln_ir_outcrop, coeff_nl, lowess_matrix):
    """
    Compute nonlinear site response on the native frequency grid;
    equations (10c)-(10d) and the discussion on pp. 2092-2093.

    :param ln_ir_outcrop:
        The natural logarithm of peak ground acceleration (PGA [g]) at rock
        outcrop
    :param coeff_nl:
        A :class:`numpy.ndarray` instance of shape [number of freqs, 3] with
        the values of the coefficients f3, f4 and f5 which are used to compute
        the non-linear term
    :param lowess_matrix:
        LOWESS smoothing weights for the native frequency grid
    :returns:
        The smoothed nonlinear term with shape
        [number of freqs, number of sites]
    """
    vsref_nl = 760.0
    num_sites = len(ctx.vs30)
    num_freqs = coeff_nl.shape[0]

    # Updating the matrix with the coefficients. This has shape (number of
    # frequencies) * (number of coeffs) * (number of sites)
    coeff_nl = np.expand_dims(coeff_nl, 2)
    coeff_nl = np.repeat(coeff_nl, num_sites, 2)

    # Updating the matrix with Vs30 values. This has shape (number of
    # frequencies) * (number of sites)
    vs30 = np.tile(ctx.vs30, (num_freqs, 1))
    ln_ir_outcrop = np.tile(ln_ir_outcrop, (num_freqs, 1))

    # Computing
    t1 = np.exp(coeff_nl[:, 2] * (np.minimum(vs30, vsref_nl)-360.))
    t2 = np.exp(coeff_nl[:, 2] * (vsref_nl-360.))
    f2 = coeff_nl[:, 1] * (t1 - t2)
    f3 = coeff_nl[:, 0]

    fnl_0 = f2 * np.log((np.exp(ln_ir_outcrop) + f3) / f3)
    idxs = np.argmin(fnl_0, axis=0)

    # Applying correction as described at page 2093 in BA18
    for i, j in enumerate(idxs):
        fnl_0[j:, i] = min(fnl_0[:, i])
    # Smooth after flattening, as in smooth2(fNL_mod0, 20, 'lowess').
    return lowess_matrix @ fnl_0


def _get_dimunition_factor(ctx, imt):
    """
    Compute kappa diminution for high-frequency extrapolation;
    equations (17a)-(17b), p. 2096.
    """
    max_freq = 23.988321
    kappa = np.exp(-0.4*np.log(ctx.vs30/760)-3.5)
    D = np.exp(-np.pi * kappa * (imt.frequency - max_freq))
    return D


def _get_mean_linear(C, ctx):
    """
    Compute log median EAS without nonlinear site response;
    equation (7), p. 2091, with the fNL part of fS omitted.
    """
    mean = (_magnitude_scaling(C, ctx) +
            _path_scaling(C, ctx) +
            _linear_site_response(C, ctx) +
            _ztor_scaling(C, ctx) +
            _normal_fault_effect(C, ctx) +
            _get_basin_term(C, ctx))
    return mean


def _get_mean(self, C, ctx, imt):
    """
    Compute log median EAS without nonlinear site response, including
    high-frequency extrapolation; equations (7) and (17), pp. 2091, 2096.
    """
    # Extrapolate from the last valid coefficient row, rounded to 24 Hz.
    if imt.frequency >= 23.988321:
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

    The nonlinear site term is flattened after its minimum and smoothed using
    the span-20 LOWESS procedure from the MATLAB script in the e-sup.
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

    def __init__(self):
        """
        Load coefficients and initialize the native grid and LOWESS weights.
        """
        # Load the coeffs
        with open(BA_COEFFS) as f:
            self.COEFFS = CoeffsTable(table=f.read())

        # Get the tabulted freqs + the non-linear coeffs per freq
        self.FREQ_NL, self.COEFF_NL = self.COEFFS.get_coeffs(
            ['f3', 'f4', 'f5'])

        # Build the LOWESS matrix
        self.LOWESS_MATRIX = _get_lowess_matrix(len(self.FREQ_NL))

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        """
        Compute log median EAS and standard deviations;
        equations (7), (18) and (19), pp. 2091, 2099.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Compute nat log of PGA on rock
        ln_ir_outcrop = _get_ln_ir_outcrop(self, ctx)

        # Get non-linear term once
        nl_response = _get_nl_site_response(
            ctx, ln_ir_outcrop, self.COEFF_NL, self.LOWESS_MATRIX)

        # Compute per IMT
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            # Compute log median EAS before nonlinear site response
            lin_component = _get_mean(self, C, ctx, imt)

            # Interpolate the smoothed nonlinear term to the requested
            # frequency
            nl_component = np.array([
                np.interp(imt.frequency, self.FREQ_NL, site)
                for site in nl_response.T])

            # Combine to get the log median EAS
            mean[m] = (lin_component + nl_component)

            # Compute sigma compnents
            sigma[m], tau[m], phi[m] = _get_stddevs(C, ctx)
