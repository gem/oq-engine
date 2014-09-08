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
from openquake.hazardlib.gsim.base import CoeffsTable


def _compute_C1_term(C, imt, dists):
    """
    Return C1 coeffs as function of Rrup as proposed by
    Rodriguez-Marek et al (2013)
    The C1 coeff are used to compute the single station sigma
    """

    c1_rrup = np.zeros_like(dists)
    idx = dists < C['Rc11']
    c1_rrup[idx] = C['phi_11']
    idx = (dists >= C['Rc11']) & (dists <= C['Rc21'])
    idx = (dists >= C['Rc11']) & (dists <= C['Rc21'])
    c1_rrup[idx] = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
        ((dists[idx] - C['Rc11']) / (C['Rc21'] - C['Rc11']))
    idx = dists > C['Rc21']
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
        _compute_small_mag_correction_term(C_ADJ, rup.mag, imt, dists)

    mean_corr = np.log(mean_corr)

    std_corr = _get_corr_stddevs(COEFFS[imt], stddev_types, len(sites.vs30),
                                 phi_ss)

    stddevs = np.log(10 ** np.array(std_corr))

    return mean_corr, stddevs

COEFFS_PHI_SS_MEAN = CoeffsTable(sa_damping=5, table="""\
    IMT              phi_ss
    pga              0.460
    0.010            0.460000000
    0.020            0.456989700
    0.030            0.455228787
    0.040            0.453979400
    0.050            0.453000000
    0.100            0.450000000
    0.150            0.468000000
    0.200            0.480
    0.250            0.480
    0.300            0.480
    0.350            0.474
    0.400            0.469
    0.450            0.464
    0.500            0.460
    0.550            0.459
    0.600            0.457
    0.650            0.456
    0.700            0.455
    0.750            0.454
    0.800            0.453
    0.850            0.452
    0.900            0.452
    0.950            0.451
    1.000            0.450
    1.050            0.448
    1.100            0.447
    1.150            0.445
    1.200            0.443
    1.250            0.442
    1.300            0.440
    1.350            0.439
    1.400            0.438
    1.450            0.436
    1.500            0.435
    1.550            0.434
    1.600            0.433
    1.650            0.432
    1.700            0.431
    1.750            0.430
    1.800            0.429
    1.850            0.428
    1.900            0.427
    1.950            0.426
    2.000            0.425
    2.050            0.424
    2.100            0.423
    2.150            0.422
    2.200            0.421
    2.250            0.420
    2.300            0.420
    2.350            0.419
    2.400            0.418
    2.450            0.417
    2.500            0.417
    2.550            0.416
    2.600            0.415
    2.650            0.415
    2.700            0.414
    2.750            0.413
    2.800            0.413
    2.850            0.412
    2.900            0.411
    2.950            0.411
    3.000            0.410
    3.050            0.410
    3.100            0.410
    3.150            0.410
    3.200            0.410
    3.250            0.410
    3.300            0.410
    3.350            0.410
    3.400            0.410
    3.450            0.410
    3.500            0.410
    3.550            0.410
    3.600            0.410
    3.650            0.410
    3.700            0.410
    3.750            0.410
    3.800            0.410
    3.850            0.410
    3.900            0.410
    3.950            0.410
    4.000            0.410
    4.050            0.410
    4.100            0.410
    4.150            0.410
    4.200            0.410
    4.250            0.410
    4.300            0.410
    4.350            0.410
    4.400            0.410
    4.450            0.410
    4.500            0.410
    4.550            0.410
    4.600            0.410
    4.650            0.410
    4.700            0.410
    4.750            0.410
    4.800            0.410
    4.850            0.410
    4.900            0.410
    4.950            0.410
    5.000            0.410
    5.050            0.410
    5.100            0.410
    5.150            0.410
    5.200            0.410
    5.250            0.410
    5.300            0.410
    5.350            0.410
    5.400            0.410
    5.450            0.410
    5.500            0.410
    5.550            0.410
    5.600            0.410
    5.650            0.410
    5.700            0.410
    5.750            0.410
    5.800            0.410
    5.850            0.410
    5.900            0.410
    5.950            0.410
    6.000            0.410
    6.050            0.410
    6.100            0.410
    6.150            0.410
    6.200            0.410
    6.250            0.410
    6.300            0.410
    6.350            0.410
    6.400            0.410
    6.450            0.410
    6.500            0.410
    6.550            0.410
    6.600            0.410
    6.650            0.410
    6.700            0.410
    6.750            0.410
    6.800            0.410
    6.850            0.410
    6.900            0.410
    6.950            0.410
    7.000            0.410
    7.050            0.410
    7.100            0.410
    7.150            0.410
    7.200            0.410
    7.250            0.410
    7.300            0.410
    7.350            0.410
    7.400            0.410
    7.450            0.410
    7.500            0.410
    7.550            0.410
    7.600            0.410
    7.650            0.410
    7.700            0.410
    7.750            0.410
    7.800            0.410
    7.850            0.410
    7.900            0.410
    7.950            0.410
    8.000            0.410
    8.050            0.410
    8.100            0.410
    8.150            0.410
    8.200            0.410
    8.250            0.410
    8.300            0.410
    8.350            0.410
    8.400            0.410
    8.450            0.410
    8.500            0.410
    8.550            0.410
    8.600            0.410
    8.650            0.410
    8.700            0.410
    8.750            0.410
    8.800            0.410
    8.850            0.410
    8.900            0.410
    8.950            0.410
    9.000            0.410
    9.050            0.410
    9.100            0.410
    9.150            0.410
    9.200            0.410
    9.250            0.410
    9.300            0.410
    9.350            0.410
    9.400            0.410
    9.450            0.410
    9.500            0.410
    9.550            0.410
    9.600            0.410
    9.650            0.410
    9.700            0.410
    9.750            0.410
    9.800            0.410
    9.850            0.410
    9.900            0.410
    9.950            0.410
    10.000           0.410
    """)
