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
This module defines functions that can be applied to loss ratio
or loss curves.
"""

from numpy import mean

from openquake import shapes
from openquake.utils.general import unique_curve


def compute_conditional_loss(curve, probability):
    """Return the loss (or loss ratio) corresponding to the given
    PoE (Probability of Exceendance).

    Return the max loss (or loss ratio) if the given PoE is smaller
    than the lowest PoE defined.

    Return zero if the given PoE is greater than the
    highest PoE defined.
    """
    # dups in the curve have to be skipped
    loss_curve_without_dups = shapes.Curve(unique_curve(curve))

    if loss_curve_without_dups.ordinate_out_of_bounds(probability):
        if probability < loss_curve_without_dups.y_values[-1]:
            return loss_curve_without_dups.x_values[-1]
        else:
            return 0.0

    return loss_curve_without_dups.abscissa_for(probability)


def compute_loss_curve(loss_ratio_curve, asset):
    """Compute the loss curve for the given asset value.

    A loss curve is obtained from a loss ratio curve by
    multiplying each X value (loss ratio) for the given asset.
    """

    if not asset:
        return shapes.EMPTY_CURVE

    return loss_ratio_curve.rescale_abscissae(asset)


def _compute_mid_mean_pe(loss_ratio_curve):
    """Compute a new loss ratio curve taking the mean values."""

    loss_ratios = loss_ratio_curve.abscissae
    pes = loss_ratio_curve.ordinates

    ratios = collect(loop(loss_ratios, lambda x, y: mean([x, y])))
    mid_pes = collect(loop(pes, lambda x, y: mean([x, y])))

    return shapes.Curve(zip(ratios, mid_pes))


def _compute_mid_po(loss_ratio_pe_mid_curve):
    """Compute a loss ratio curve that has PoOs
    (Probabilities of Occurrence) as Y values."""

    loss_ratios = loss_ratio_pe_mid_curve.abscissae
    pes = loss_ratio_pe_mid_curve.ordinates

    ratios = collect(loop(loss_ratios, lambda x, y: mean([x, y])))
    pos = collect(loop(pes, lambda x, y: x - y))

    return shapes.Curve(zip(ratios, pos))


def compute_mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    mid_curve = _compute_mid_po(_compute_mid_mean_pe(curve))
    return sum(i * j for i, j in zip(
            mid_curve.abscissae, mid_curve.ordinates))


def loop(elements, func, *args):
    """Loop over the given elements, yielding func(current, next, *args)."""
    for idx in xrange(elements.size - 1):
        yield func(elements[idx], elements[idx + 1], *args)


def collect(iterator):
    """Simply collect the data taken from the given iterator."""
    data = []

    for element in iterator:
        data.append(element)

    return data
