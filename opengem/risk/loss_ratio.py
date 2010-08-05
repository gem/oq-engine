# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import computation

class LossRatioComputation(computation.Computation):
    """Example Loss Ratio Computation

    The _compute function in this class should be replaced with something real.

    """
    def __init__(self, pool, cell):
        keys = ['shakemap', 'exposure', 'vulnerability']
        super(LossRatioComputation, self).__init__(pool, cell, keys=keys)

    def _compute(self, shakemap, exposure, vulnerability):
        output = ':'.join(str(x) for x in (shakemap, exposure, vulnerability))
        return 'loss_ratio:' + output
