# -*- coding: utf-8 -*-
# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.akkar_bommer_2010_swiss_coeffs import (
    COEFFS_PHI_SS_MEAN
    )


def _compute_C1_term(C, imt, dists):
    """
    Return C1 coeffs as function of Rrup as proposed by
    Rodriguez-Marek et al (2013)
    The C1 coeff are used to compute the single station sigma
    """

    c1_rrup = np.zeros_like(dists.rjb)
    idx = dists.rjb < C['Rc11']
    c1_rrup[idx] = C['phi_11']
    idx = (dists.rjb >= C['Rc11']) & (dists.rjb <= C['Rc21'])
    c1_rrup[idx] = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
        ((dists.rjb[idx] - C['Rc11']) / (C['Rc21'] - C['Rc11']))
    idx = dists.rjb > C['Rc21']
    c1_rrup[idx] = C['phi_21']
    return c1_rrup


def _compute_small_mag_correction_term(C, mag, imt, rhypo):
    """
    small magnitude correction applied to the median values
    """
    if mag >= 3.00 and mag < 5.5:
        min_term = np.minimum(rhypo, C['Rm'])
        max_term = np.maximum(min_term, 10)
        term_ln = np.log(max_term / 20)
        term_ratio = ((5.50 - mag) / C['a1'])
        temp = (term_ratio) ** C['a2'] * (C['b1'] + C['b2'] * term_ln)
        return 1 / np.exp(temp)
    else:
        return 1


def _compute_phi_ss(C, rup, c1_rrup, imt, mean_phi_ss):
    """
    Return phi_ss coeffs as function of magnitude as
    proposed by Rodriguez-Marek et al (2013)
    The phi_ss coeff are used to compute the single station sigma
    phi_ss natural logarithm units
    """
    if mean_phi_ss:
        C_ADJ = COEFFS_PHI_SS_MEAN[imt]
        return (C_ADJ['phi_ss']/np.log(10))

    else:
        phi_ss = 0

        if rup.mag < C['Mc1']:
            phi_ss = c1_rrup

        elif rup.mag >= C['Mc1'] and rup.mag <= C['Mc2']:
            phi_ss = c1_rrup + \
                (C['C2'] - c1_rrup) * \
                ((rup.mag - C['Mc1']) / (C['Mc2'] - C['Mc1']))
        elif rup.mag > C['Mc2']:
            phi_ss = C['C2']

        return (phi_ss) / np.log(10)


def _get_corr_stddevs(C, stddev_types, num_sites, phi_ss):
    """
    Return standard deviations adjusted for single station sigma
    as the total standard deviation - as proposed to be used in
    the Swiss Hazard Model [2014].
    """

    stddevs = []
    for stddev_type in stddev_types:
        if stddev_type == const.StdDev.TOTAL:
            stddevs.append(
                np.sqrt(
                    C['Sigma2'] * C['Sigma2'] +
                    phi_ss * phi_ss) +
                np.zeros(num_sites))
    return stddevs


def _apply_adjustments(COEFFS, C_ADJ, mean, stddevs, sites, rup, dists, imt,
                       stddev_types, mean_phi_ss):
    """
    This method applies adjustments to the mean and standard deviation.
    The small-magnitude adjustments are applied to mean, whereas the single
    station sigma is applied to the standard deviation.
    """
    c1_rrup = _compute_C1_term(C_ADJ, imt, dists)
    phi_ss = _compute_phi_ss(C_ADJ, rup, c1_rrup, imt, mean_phi_ss)

    mean_corr = np.exp(mean) * C_ADJ['k_adj'] * \
        _compute_small_mag_correction_term(C_ADJ, rup.mag, imt, dists.rjb)

    mean_corr = np.log(mean_corr)

    std_corr = _get_corr_stddevs(COEFFS[imt], stddev_types, len(sites.vs30),
                                 phi_ss)

    stddevs = np.log(10 ** np.array(std_corr))

    return mean_corr, stddevs
