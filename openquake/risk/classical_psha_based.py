# -*- coding: utf-8 -*-
"""
This module defines the functions used to compute loss ratio and loss curves
using the classical psha based approach.
"""

from numpy import linspace # pylint: disable=F0401,E0611
import scipy # pylint: disable=F0401

from numpy import isnan # pylint: disable=F0401,E0611
from scipy import sqrt # pylint: disable=F0401,E0611
from scipy import stats # pylint: disable=F0401,E0611
from scipy import log # pylint: disable=F0401,E0611

from openquake import shapes

STEPS_PER_INTERVAL = 5

def compute_loss_ratio_curve(vuln_function, hazard_curve):
    """Compute a loss ratio curve for a specific hazard curve (e.g., site),
    by applying a given vulnerability function."""

    if vuln_function is None:
        vuln_function = shapes.EMPTY_CURVE

    lrem = _compute_lrem(vuln_function)
    lrem_po = _compute_lrem_po(vuln_function, lrem, hazard_curve)
    loss_ratios = _generate_loss_ratios(vuln_function)
    loss_ratio_curve = _compute_loss_ratio_curve_from_lrem_po(
                            loss_ratios, lrem_po)

    return loss_ratio_curve


def _compute_lrem_po(vuln_function, lrem, hazard_curve):
    """Compute the loss ratio * probability of occurrence matrix.""" 

    current_column = 0
    lrem_po = [None] * len(lrem)
    imls = vuln_function.abscissae

    for iml in imls:
        prob_occ = hazard_curve.ordinate_for(iml)
        for row in range(len(lrem_po)):
            if not lrem_po[row]: 
                lrem_po[row] = [None] * len(vuln_function.abscissae)
            lrem_po[row][current_column] = lrem[row][current_column] * prob_occ
        current_column += 1
    
    return lrem_po


# pylint: disable=C0103
def _compute_loss_ratio_curve_from_lrem_po(loss_ratios, lrem_po):
    """Compute the loss ratio curve."""
    
    data = []
    for row in range(len(lrem_po)-1):
        prob_occ = 0.0
        for column in range(len(lrem_po[row])):
            prob_occ += lrem_po[row][column]
        data.append((loss_ratios[row], prob_occ))

    return shapes.Curve(data)


# @state.memoize
def _generate_loss_ratios(vuln_function):
    """Loss ratios are a function of the vulnerability curve."""

# TODO (ac): We should always have covs, fix the caller
# TODO (ac): Extract domain, something like vuln_function.means
    if vuln_function.is_multi_value:
        loss_ratios = list(vuln_function.ordinates[:, 0])
    else:
        loss_ratios = list(vuln_function.ordinates)

    # we need to add 0.0 as first value
    loss_ratios.insert(0, 0.0)
    return _split_loss_ratios(loss_ratios)


# @state.memoize
def _compute_lrem(vuln_function, distribution=None):
    """Compute the loss ratio exceedance matrix."""

    if not distribution:
        distribution = stats.lognorm
        # this is so we can memoize the thing

    loss_ratios = _generate_loss_ratios(vuln_function)

    current_column = 0
    lrem = [None] * (len(loss_ratios)+1)

    def fix_value(prob):
        """Fix negative probabilities for values close to zero."""
        if isnan(prob):
            return 0.0
        if prob < 0.00001: 
            return 0.0
        else: 
            return prob

    for iml in vuln_function.abscissae:
        mean = vuln_function.ordinate_for(iml)
        cov = vuln_function.ordinate_for(iml, 1)
        stddev = cov * mean
        variance = stddev ** 2.0
        mu = log(mean ** 2.0 / sqrt(variance + mean ** 2.0) )
        sigma = sqrt(log((variance / mean ** 2.0) + 1.0))
        
        for row in range(len(loss_ratios)+1):
            if not lrem[row]: 
                lrem[row] = [None] * len(vuln_function.abscissae)
            # last loss ratio is fixed to be 1
            if row < len(loss_ratios): 
                next_ratio = loss_ratios[row]
            else: 
                next_ratio = 1.0
            
            lrem[row][current_column] = fix_value(
                    distribution.sf(next_ratio, 
                    sigma, scale=scipy.exp(mu)))

        current_column += 1

    return lrem


def _split_loss_ratios(loss_ratios, steps=STEPS_PER_INTERVAL):
    """Split the loss ratios.

    steps is the number of steps we make to go from one loss
    ratio to the other. For example, if we have [1.0, 2.0]:

        steps = 1 produces [1.0, 2.0]
        steps = 2 produces [1.0, 1.5, 2.0]
        steps = 3 produces [1.0, 1.33, 1.66, 2.0]
    """

    splitted_ratios = set()
    for idx in range(len(loss_ratios) - 1):
        splitted_ratios.update(linspace(
                loss_ratios[idx], loss_ratios[idx + 1], steps + 1))

    return list(sorted(splitted_ratios))
