# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
This module will read the loss/loss ratio curves currently stored in the xml 
format, and compute the loss/loss ratio at each site that corresponds to a 
certain probability of exceedance
"""
from opengem import computation

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
