import unittest
from openquake.qa_tests_data.classical import case_1, case_4
from openquake.qa_tests_data.event_based_risk import case_miriam
from openquake.commonlib import readinput, calc


def gen_ruptures(src):
    for i, rup in enumerate(src.iter_ruptures()):
        rup.serial = src.serial[i]
        yield rup


class StochasticEventSetCollectionTestCase(unittest.TestCase):

    def check(self, pkg, expected):
        oq = readinput.get_oqparam('job.ini', pkg)
        csm = readinput.get_composite_source_model(oq)
        csm.init_serials()
        [src] = csm.get_sources()
        sesc = calc.StochasticEventSetCollection(list(gen_ruptures(src))[:3])
        self.assertEqual(str(sesc), expected)

    def test_point_source(self):
        self.check(case_1, '''\
rupserial\tmagnitude\tlon\tlat\tdepth\ttectonic_region_type\tstrike\tdip\trake\tboundary
0\t4.000000E+00\t0.00000\t0.00000\t4.000000E+00\tactive shallow crust\t0.000000E+00\t9.000000E+01\t0.000000E+00\tMULTIPOLYGON(((0.0 -0.00449660802959,0.0 0.00449660802959,0.0 -0.00449660802959,0.0 0.00449660802959,0.0 -0.00449660802959)))
''')

    def _test_simple_fault_source(self):
        self.check(case_4, '')

    def test_complex_fault_source(self):
        self.check(case_miriam, '''\
rupserial\tmagnitude\tlon\tlat\tdepth\ttectonic_region_type\tstrike\tdip\trake\tboundary\n0\t5.100000E+00\t-78.78848\t14.80459\t9.583333E+00\tActive Shallow Crust\t3.536375E+02\t8.113641E+01\t1.800000E+02\tMULTIPOLYGON(((-78.79 14.76,-78.8003402907 14.8490839989,-78.7868941663 14.8492561721,-78.7766666668 14.760001911,-78.79 14.76)))\n1\t5.100000E+00\t-78.79876\t14.89375\t9.583333E+00\tActive Shallow Crust\t3.536349E+02\t8.105386E+01\t1.800000E+02\tMULTIPOLYGON(((-78.8003402907 14.8490839989,-78.8106891099 14.9381675351,-78.7971301181 14.938509981,-78.7868941663 14.8492561721,-78.8003402907 14.8490839989)))\n2\t5.100000E+00\t-78.80906\t14.98292\t9.583333E+00\tActive Shallow Crust\t3.536322E+02\t8.097137E+01\t1.800000E+02\tMULTIPOLYGON(((-78.8106891099 14.9381675351,-78.8210465183 15.0272506054,-78.8073745825 15.0277633343,-78.7971301181 14.938509981,-78.8106891099 14.9381675351)))
''')

    def _test_characteristic_source(self):
        pass

    def _test_nonparametric_source(self):
        pass
