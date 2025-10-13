# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import numpy as np


def _compute_C1_term(C, dists):
    """
    Return C1 coeffs as function of Rrup as proposed by
    Rodriguez-Marek et al (2013)
    The C1 coeff are used to compute the single station sigma
    """
    c1_dists = np.zeros_like(dists)
    idx = dists < C['Rc11']
    c1_dists[idx] = C['phi_11']
    idx = (dists >= C['Rc11']) & (dists <= C['Rc21'])
    c1_dists[idx] = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
        ((dists[idx] - C['Rc11']) / (C['Rc21'] - C['Rc11']))
    idx = dists > C['Rc21']
    c1_dists[idx] = C['phi_21']
    return c1_dists


def _compute_small_mag_correction_term(C, mag, rhypo):
    """
    small magnitude correction applied to the median values
    """
    if not isinstance(mag, np.ndarray):
        mag = np.full_like(rhypo, mag)
    term = np.ones_like(mag)
    within = (mag >= 3.00) & (mag < 5.5)
    min_term = np.minimum(rhypo[within], C['Rm'])
    max_term = np.maximum(min_term, 10)
    term_ln = np.log(max_term / 20)
    term_ratio = ((5.50 - mag[within]) / C['a1'])
    temp = (term_ratio) ** C['a2'] * (C['b1'] + C['b2'] * term_ln)
    term[within] = 1 / np.exp(temp)
    return term


def _compute_phi_ss(C, mag, c1_dists, log_phi_ss, mean_phi_ss):
    """
    Returns the embeded logic tree for single station sigma
    as defined to be used in the Swiss Hazard Model 2014:
    the single station sigma branching levels combines with equal
    weights: the phi_ss reported as function of magnitude
    as proposed by Rodriguez-Marek et al (2013) with the mean
    (mean_phi_ss) single station value;
    the resulted phi_ss is in natural logarithm units
    """
    phi_ss = np.zeros_like(c1_dists)
    if not isinstance(mag, np.ndarray):
        mag = np.full_like(c1_dists, mag)
    phi_ss[mag < C['Mc1']] = c1_dists[mag < C['Mc1']]
    within = (mag >= C['Mc1']) & (mag <= C['Mc2'])
    phi_ss[within] = c1_dists[within] + (C['C2'] - c1_dists[within]) * (
        (mag[within] - C['Mc1']) / (C['Mc2'] - C['Mc1']))
    phi_ss[mag > C['Mc2']] = C['C2']
    return (phi_ss * 0.50 + mean_phi_ss * 0.50) / log_phi_ss


def _corr_sig(sig, C, tau_ss, phi_ss, NL=None, tau_value=None):
    """
    Adjust standard deviations for single station sigma
    as the total standard deviation - as proposed to be used in
    the Swiss Hazard Model [2014].
    """
    s = phi_ss ** 2
    if tau_value is not None and NL is not None:
        s += tau_value * tau_value * ((1 + NL) ** 2)
        t = tau_value * tau_value * ((1 + NL) ** 2)
    else:
        s += C[tau_ss] * C[tau_ss]
        t = C[tau_ss] * C[tau_ss]
    return np.sqrt(s), np.sqrt(t), phi_ss


def _apply_adjustments(COEFFS, C_ADJ, tau_ss, mean, sig, tau, phi, ctx,
                       dist, imt, log_phi_ss, NL=None, tau_value=None):
    """
    This method applies adjustments to the mean and standard deviation.
    The small-magnitude adjustments are applied to mean, whereas the
    embedded single station sigma logic tree is applied to the
    total standard deviation.
    """
    c1_dists = _compute_C1_term(C_ADJ, dist)
    phi_ss = _compute_phi_ss(
        C_ADJ, ctx.mag, c1_dists, log_phi_ss, C_ADJ['mean_phi_ss'])

    mean_corr = np.exp(mean) * C_ADJ['k_adj'] * \
        _compute_small_mag_correction_term(C_ADJ, ctx.mag, dist)

    mean[:] = np.log(mean_corr)
    sig[:], tau[:], phi[:] = _corr_sig(sig, COEFFS[imt], tau_ss,
                                       phi_ss, NL, tau_value)
