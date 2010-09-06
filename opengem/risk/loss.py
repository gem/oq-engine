# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Deterministic Risk Computations based on Hazard, Exposure and Vulnerability

Expects to receive:
    loss-ratio curves that are store in XML
    grid of columns and rows from region of coordinates

It can receive region, grid, and site from shapes.py

Expects to compute:
    compute the loss ratio at each site that corresponds to a certain 
    probability of exceedance.

"""
import sys
sys.path.append("/Users/benwyss/Projects/opengem")

from opengem import computation
from opengem.parser import shaml_output



class LossComputation(computation.Computation):
    """Example Loss Computation

    The _compute function in this class should be replaced with something real.

    """
    def __init__(self, pool, cell):
        keys = ['shakemap', 'exposure', 'vulnerability']
        super(LossComputation, self).__init__(pool, cell, keys=keys)

    def _compute(self, shakemap, exposure, vulnerability):
        output = ':'.join(str(x) for x in (shakemap, exposure, vulnerability))
        return 'loss:' + output
