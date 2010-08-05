# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import computation


class ConcatComputation(computation.Computation):
    def __init__(self, pool, cell):
        keys = ['shake', 'roll']
        super(ConcatComputation, self).__init__(pool, cell, keys)

    def _compute(self, **kw):
        return ':'.join(str(x) for x in sorted(kw.values()))
