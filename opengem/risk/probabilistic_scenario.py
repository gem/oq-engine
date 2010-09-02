#!/usr/bin/env python
# encoding: utf-8
"""
This module defines the computations used in the
probabilistic scenario. For more information, take a look at the
scientific model at <http://to_be_defined>.
"""

class Curve(object):
    """This class defines a curve (discrete function)
    
    used in the risk domain.
    """
    
    def __init__(self, values):
        self.values = values
    
    def __eq__(self, other):
        return self.values == other.values

    @property
    def domain(self):
        """Returns the domain values of this curve."""
        
        return self.values.keys()

    def get_for(self, x_value):
        """Returns the y value (codomain) corresponding
        
        to the given x value (domain).
        """
        
        return self.values[x_value]

EMPTY_CURVE = Curve({})

def compute_loss_curve(loss_ratio_curve, asset):
    """Computes the loss curve for the given loss ratio curve."""
    
    # invalid asset
    if not asset: return EMPTY_CURVE
    
    loss_curve_values = {}
    for loss_ratio, probability_occurrence \
            in loss_ratio_curve.values.iteritems(): \
            loss_curve_values[loss_ratio * asset] = probability_occurrence
    
    return Curve(loss_curve_values)

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