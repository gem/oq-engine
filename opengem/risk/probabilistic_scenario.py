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
    
    @property
    def domain(self):
        return self.values.keys()
    
    def get_for(self, x_value):
        """Returns the y value (codomain) for the given x value (domain)."""
        
        return self.values[x_value]
    
    def __eq__(self, other):
        return self.values == other.values

EMPTY_CURVE = Curve({})

def compute_loss_curve(loss_ratio_curve, asset):
    """Computes the loss curve for the given loss ratio curve."""
    
    # invalid asset
    if not asset: return EMPTY_CURVE
    
    loss_curve_values = {}
    
    for loss_ratio in loss_ratio_curve.domain:
        loss_curve_values[loss_ratio * asset] = \
                loss_ratio_curve.get_for(loss_ratio)
    
    return Curve(loss_curve_values)