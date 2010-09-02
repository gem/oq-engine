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