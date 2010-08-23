# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import computation
import logging

class LossComputation(computation.Computation):
    """Example Loss Computation

    The _compute function in this class should be replaced with something real.

    """
    def __init__(self, pool, cell):
        keys = ['shakemap', 'exposure', 'vulnerability']
        super(LossComputation, self).__init__(pool, cell, keys=keys)

    def _compute(self, shakemap, exposure, vulnerability):
        # output = ':'.join(str(x) for x in (shakemap, exposure, vulnerability))
        # return 'loss:' + output
        return float(shakemap * exposure * vulnerability * 254/9) 
