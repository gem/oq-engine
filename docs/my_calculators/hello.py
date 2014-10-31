import os
from openquake.commonlib.calculators import calculators, base


@calculators.add('hello')
class HelloCalculator(base.BaseCalculator):
    def pre_execute(self):
        pass

    def execute(self):
        return 'hello world'

    def post_execute(self, result):
        fname = os.path.join(self.oqparam.export_dir, 'hello.txt')
        open(fname, 'w').write(result)
        return dict(hello=fname)

if __name__ == '__main__':
    import sys
    from openquake.commonlib import readinput
    with open(sys.argv[1]) as job_ini:
        oqparam = readinput.get_oqparam(job_ini)
        calc = HelloCalculator(oqparam)
        print calc.run()
