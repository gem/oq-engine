#!/usr/bin/env python
# encoding: utf-8
"""
This module defines the computations used in the
probabilistic scenario. For more information, take a look at the
scientific model at <http://to_be_defined>.
"""

from opengem import shapes


def compute_loss_curve(loss_ratio_curve, asset):
    """Computes the loss curve for the given loss ratio curve."""
    
    # invalid asset
    if not asset: return shapes.EMPTY_CURVE
    
    loss_curve_values = {}
    for loss_ratio, probability_occurrence \
            in loss_ratio_curve.values.iteritems(): \
            loss_curve_values[loss_ratio * asset] = probability_occurrence
    
    return shapes.Curve(loss_curve_values)