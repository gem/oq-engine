# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module defines functions that can be applied to loss ratio
or loss curves.
"""

from numpy import mean, array, subtract # pylint: disable=E1101, E0611

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
    return sum(i*j for i, j in zip(mid_curve.abscissae, mid_curve.ordinates))

def compute_imls(vuln_function):
    """
        Computes Intensity Measure Levels considering
        the highest/lowest values a special case
    """

    imls = vuln_function.imls

    lowest_curve_value = imls[0] - ((imls[1] - imls[0]) / 2)
    highest_curve_value = imls[-1] + ((imls[-1] - imls[-2]) / 2)
    between_curve_values = collect(loop(vuln_function.imls,
            lambda x, y: mean([x, y])))
    return [lowest_curve_value] + between_curve_values + [highest_curve_value]

def compute_pes_from_imls(haz_curve, imls):
    """
        Computes the probabilities of exceedances from imls
    """

    curve_tuple = [(el['x'], el['y']) for el in haz_curve['curve']]
    curve = shapes.Curve(curve_tuple)
    pes = [curve.ordinate_for(iml) for iml in imls]

    return array(pes)

def compute_pos_from_pes(hazard_curve, imls):
    """
        Computes the probability occurences from the probability exceedances
    """
    return collect(loop(compute_pes_from_imls(hazard_curve, imls), 
        lambda x, y: subtract(array(x), array(y))))

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
