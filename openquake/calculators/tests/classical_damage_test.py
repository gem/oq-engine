from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_damage import (
    case_1, case_2, case_1a, case_1b, case_1c, case_2a, case_2b, case_3a,
    case_4a, case_4b, case_4c, case_5a, case_6a, case_6b, case_7a, case_7b,
    case_7c, case_8a)
from openquake.calculators.tests import CalculatorTestCase

import numpy

aae = numpy.testing.assert_almost_equal


class ClassicalDamageCase1TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_1.__file__, 'job_continuous.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_1.__file__, 'job_discrete.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_1.__file__, 'job_interpolation.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


# tests with no damage limit
class ClassicalDamageCase2TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_2.__file__, 'job_continuous.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_2.__file__, 'job_discrete.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_2.__file__, 'job_interpolation.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


class ClassicalDamageTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1a(self):
        self.run_calc(case_1a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.971702, 0.00488098, 0.0067176, 0.005205, 0.0114946], 6)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1b(self):
        self.run_calc(case_1b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.98269, 0.001039, 0.0028866, 0.0032857, 0.01009], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1c(self):
        self.run_calc(case_1c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.971829, 0.005068, 0.00682, 0.005172, 0.011111], 6)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2a(self):
        self.run_calc(case_2a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, (0.97072, 0.004527, 0.008484, 0.0052885, 0.010976), 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2b(self):
        self.run_calc(case_2b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.970740, 0.004517, 0.00847858, 0.0052878, 0.0109759], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_3a(self):
        self.run_calc(case_3a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.972491, 0.008021, 0.010599, 0.0057342, 0.0031543], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4a(self):
        self.run_calc(case_4a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.970851, 0.0044304, 0.00841, 0.00529, 0.01102], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4b(self):
        self.run_calc(case_4b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.108756, 0.044266, 0.138326, 0.14414, 0.564511], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4c(self):
        self.run_calc(case_4c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.108756, 0.044266, 0.138326, 0.14414, 0.564511], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_5a(self):
        self.run_calc(case_5a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [4.85426, 0.02215, 0.042048, 0.02643, 0.055113], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_6a(self):
        self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini')
        damages = list(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.9568527, 0.0149491, 0.0150699, 0.0075941, 0.005534], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_6b(self):
        self.run_calc(case_6b.__file__, 'job_haz.ini,job_risk.ini')
        damages = list(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.933186, 0.030293, 0.0272806, 0.0059548, 0.0032858], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7a(self):
        self.run_calc(case_7a.__file__, 'job_haz.ini,job_risk.ini')
        damages = list(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.971802, 0.016595, 0.0092597, 0.001942, 0.000400], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7b(self):
        self.run_calc(case_7b.__file__, 'job_haz.ini,job_risk.ini')
        damages = list(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.8329889, 0.0927366, 0.0574756, 0.013433, 0.003366], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7c(self):
        self.run_calc(case_7c.__file__, 'job_haz.ini,job_risk.ini')
        damages = list(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.927043, 0.0399827, 0.0248378, 0.0062636, 0.0018722], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_8a(self):
        self.run_calc(case_8a.__file__, 'job_haz.ini,job_risk.ini')
        damages = self.calc.datastore['damages-rlzs'][0]
        expected = [(0.971829, 0.005068, 0.0068199, 0.005172, 0.011110),
                    (0.973699, 0.005596, 0.0070726, 0.004946, 0.008684)]
        aae(map(tuple, damages), expected, 5)
