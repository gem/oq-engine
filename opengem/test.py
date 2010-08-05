# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import computation
from opengem import producer


class ConcatComputation(computation.Computation):
    def __init__(self, pool, cell):
        keys = ['shake', 'roll']
        super(ConcatComputation, self).__init__(pool, cell, keys)

    def _compute(self, **kw):
        return ':'.join(str(x) for x in sorted(kw.values()))


class WordProducer(producer.FileProducer):
    def _parse_one(self):
        line = self.file.readline()
        if not line:
            return None

        x, y, value = line.strip().split()
        return ((int(x), int(y)), value) 
