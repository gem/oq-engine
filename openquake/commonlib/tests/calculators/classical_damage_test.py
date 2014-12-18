import unittest
from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_damage import (
    case_1)
from openquake.commonlib.tests.calculators import CalculatorTestCase


class ClassicalDamageTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_1.__file__, 'job_discrete.ini')
        self.assertEqualFiles(
            'expected/damage_discrete.csv', out['classical_damage_csv'])

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_1.__file__, 'job_continuous.ini')
        self.assertEqualFiles(
            'expected/damage_continuous.csv', out['classical_damage_csv'])
