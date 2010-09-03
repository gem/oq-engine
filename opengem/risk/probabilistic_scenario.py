#!/usr/bin/env python
# encoding: utf-8
"""
This module defines the computations used in the
probabilistic scenario. For more information, take a look at the
scientific model at <http://to_be_defined>.
"""

# TODO (ac): Document how these functions must be called to build a loss curve,
# and which values can be cached during the computation process

from scipy import stats

from opengem import shapes

def compute_loss_curve(loss_ratio_curve, asset):
    """Computes the loss curve."""
    
    # invalid asset
    if not asset: return shapes.EMPTY_CURVE
    
    loss_curve_values = {}
    for loss_ratio, probability_occurrence \
            in loss_ratio_curve.values.iteritems(): \
            loss_curve_values[loss_ratio * asset] = probability_occurrence
    
    return shapes.Curve(loss_curve_values)

def compute_lrem_po(vuln_function, lrem, hazard_curve):
    """Computes a loss matrix."""
    
    current_column = 0
    lrem_po = [None] * len(lrem)
    
    # we need to process intensity measure levels in ascending order
    imls = list(vuln_function.domain)
    imls.sort()
    
    for iml in imls:
        prob_occ = hazard_curve.get_for(iml)
        
        for row in range(len(lrem_po)):
            if not lrem_po[row]: 
                lrem_po[row] = [None] * len(vuln_function.domain)
            
            lrem_po[row][current_column] = lrem[row][current_column] * prob_occ
        
        current_column += 1

    return lrem_po

def compute_loss_ratio_curve(loss_ratios, lrem_po):
    """Computes the loss ratio curve."""
    
    loss_ratio_curve_values = {}
    
    for row in range(len(lrem_po)):
        prob_occ = 0.0
        
        for column in range(len(lrem_po[row])):
            prob_occ += lrem_po[row][column]
    
        loss_ratio_curve_values[loss_ratios[row]] = prob_occ

    return shapes.Curve(loss_ratio_curve_values)

# TODO (ac): Document how vulnerability functions are represented
def compute_lrem(loss_ratios, vuln_function, distribution=stats.lognorm):
    """Computes the loss ratio exceedance matrix."""    

    current_column = 0
    lrem = [None] * len(loss_ratios)
    
    # we need to process intensity measure levels in ascending order
    imls = list(vuln_function.domain)
    imls.sort()

# TODO (ac): Find out why we have negative probabilities
# for values close to zero. Same behaviour in Java, so it probably
# depends on how floating point values are handled internally
    def fix_value(prob):
        if prob < 0.00001: return 0.0
        else: return prob
    
    for iml in imls:
        
        for row in range(len(loss_ratios)):
            if not lrem[row]: 
                lrem[row] = [None] * len(vuln_function.domain)
            
            # last loss ratio is fixed to be 1
            if row < len(loss_ratios) - 1: next_ratio = loss_ratios[row + 1]
            else: next_ratio = 1 

            # we need to use std deviation, but we have cov
            cov = vuln_function.get_for(iml)[1]
            mean = vuln_function.get_for(iml)[0]
            
            lrem[row][current_column] = fix_value(1 - 
                    fix_value(distribution.cdf(next_ratio, mean, mean * cov)))
        
        current_column += 1

    return lrem