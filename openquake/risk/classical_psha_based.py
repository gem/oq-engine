# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



"""
This module defines functions to compute loss ratio curves
using the classical psha based approach.
"""

from scipy import sqrt, stats, log, exp  # pylint: disable=F0401,E0611
from numpy import empty, linspace  # pylint: disable=F0401,E0611
from numpy import array, concatenate  # pylint: disable=F0401,E0611
from numpy import subtract, mean  # pylint: disable=F0401,E0611

from openquake import shapes
from openquake.risk.common import loop, collect

STEPS_PER_INTERVAL = 5


def compute_loss_ratio_curve(vuln_function, hazard_curve):
    """Compute a loss ratio curve for a specific hazard curve (e.g., site),
    by applying a given vulnerability function.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.
    """

    lrem = _compute_lrem(vuln_function)
    lrem_po = _compute_lrem_po(vuln_function, lrem, hazard_curve)
    loss_ratios = _generate_loss_ratios(vuln_function)

    return shapes.Curve(zip(loss_ratios, lrem_po.sum(axis=1)))


def _compute_lrem_po(vuln_function, lrem, hazard_curve):
    """Compute the LREM * PoOs matrix."""

    lrem = array(lrem)
    lrem_po = empty(lrem.shape)

    imls = _compute_imls(vuln_function)

    if hazard_curve:
        pos = _convert_pes_to_pos(hazard_curve, imls)
        for idx, po in enumerate(pos):
            lrem_po[:, idx] = lrem[:, idx] * po

    return lrem_po


def _generate_loss_ratios(vuln_function):
    """Generate the set of loss ratios used to compute the LREM
    (Loss Ratio Exceedance Matrix)."""

    # we manually add 0.0 as first loss ratio and the last (1.0) loss ratio
    loss_ratios = concatenate((array([0.0]),
            vuln_function.means, array([1.0])))

    return _split_loss_ratios(loss_ratios)


def _compute_lrem(vuln_function, distribution=None):
    """Compute the LREM (Loss Ratio Exceedance Matrix)."""

    if distribution is None:
        # this is so we can memoize the thing
        distribution = stats.lognorm

    loss_ratios = _generate_loss_ratios(vuln_function)
    # LREM has number of rows equal to the number of loss ratios
    # and number of columns equal to the number if imls
    lrem = empty((loss_ratios.size, vuln_function.imls.size), float)

    for idx, value in enumerate(vuln_function):
        mean_val, cov = value[1:]

        stddev = cov * mean_val
        variance = stddev ** 2.0
        mu = log(mean_val ** 2.0 / sqrt(variance + mean_val ** 2.0))
        sigma = sqrt(log((variance / mean_val ** 2.0) + 1.0))

        for row, value in enumerate(lrem):
            lrem[row][idx] = distribution.sf(loss_ratios[row],
                    sigma, scale=exp(mu))

    return lrem


def _split_loss_ratios(loss_ratios, steps=None):
    """Split the loss ratios, producing a new set of loss ratios.

    Keyword arguments:
    steps -- the number of steps we make to go from one loss
    ratio to the next. For example, if we have [1.0, 2.0]:

        steps = 1 produces [1.0, 2.0]
        steps = 2 produces [1.0, 1.5, 2.0]
        steps = 3 produces [1.0, 1.33, 1.66, 2.0]
    """

    if steps is None:
        steps = STEPS_PER_INTERVAL

    splitted_ratios = set()

    for interval in loop(array(loss_ratios), linspace, steps + 1):
        splitted_ratios.update(interval)

    return array(sorted(splitted_ratios))


def _compute_imls(vuln_function):
    """
        Compute the mean IMLs (Intensity Measure Level)
        for the given vulnerability function.
    """

    imls = vuln_function.imls

    # "special" cases for lowest part and highest part of the curve
    lowest_curve_value = imls[0] - ((imls[1] - imls[0]) / 2)

    # if the calculated lowest_curve_value goes < 0 we have to force the 0
    # IMLs have to be >= 0
    if lowest_curve_value < 0:
        lowest_curve_value = 0

    highest_curve_value = imls[-1] + ((imls[-1] - imls[-2]) / 2)

    between_curve_values = collect(loop(imls, lambda x, y: mean([x, y])))

    return [lowest_curve_value] + between_curve_values + [highest_curve_value]


def _compute_pes_from_imls(haz_curve, imls):
    """
        Return the PoEs (Probability of Exceendance) defined in the
        hazard curve for each IML (Intensity Measure Level) given.
    """
    pes = [haz_curve.ordinate_for(iml) for iml in imls]

    return array(pes)


def _convert_pes_to_pos(hazard_curve, imls):
    """
        For each IML (Intensity Measure Level) given compute the
        PoOs (Probability of Occurence) from the PoEs
        (Probability of Exceendance) defined in the given hazard curve.
    """
    return collect(loop(_compute_pes_from_imls(hazard_curve, imls),
        lambda x, y: subtract(array(x), array(y))))
