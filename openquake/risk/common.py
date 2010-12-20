# -*- coding: utf-8 -*-
"""
This module defines the functions that can be applied to loss ratio
or loss curves.
"""

from numpy import mean # pylint: disable=E1101, E0611

from openquake import shapes


def compute_conditional_loss(curve, probability):
    """Return the loss (or loss ratio) corresponding to the given
    PoE (Probability of Exceendance).
    
    Return zero if the probability if out of bounds.
    """

    if curve.ordinate_out_of_bounds(probability):
        return 0.0

    return curve.abscissa_for(probability)


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

    data = []
    loss_ratios = loss_ratio_curve.abscissae
    pes = loss_ratio_curve.ordinates

    for idx in xrange(len(loss_ratios) - 1):
        data.append((mean([loss_ratios[idx],
                loss_ratios[idx + 1]]),
                mean([pes[idx], pes[idx + 1]])))

    return shapes.Curve(data)


def _compute_mid_po(loss_ratio_pe_mid_curve):
    """Compute a loss ratio curve that has PoOs
    (Probabilities of Occurrence) as Y values."""

    data = []
    loss_ratios = loss_ratio_pe_mid_curve.abscissae
    pes = loss_ratio_pe_mid_curve.ordinates

    for idx in xrange(len(loss_ratios) - 1):
        data.append((mean([loss_ratios[idx],
                loss_ratios[idx + 1]]), pes[idx] - pes[idx + 1]))

    return shapes.Curve(data)


def compute_mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    mid_pos_curve = _compute_mid_po(_compute_mid_mean_pe(curve))

    return sum(i*j for i, j in zip(
            mid_pos_curve.abscissae, mid_pos_curve.ordinates))
