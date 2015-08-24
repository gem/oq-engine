import os
from openquake.calculators import base


@base.calculators.add('hello')
class HelloCalculator(base.BaseCalculator):
    def pre_execute(self):
        pass

    def execute(self):
        return 'hello world'

    def post_execute(self, result):
        fname = os.path.join(self.oqparam.export_dir, 'hello.txt')
        open(fname, 'w').write(result)
        return dict(hello=fname)
