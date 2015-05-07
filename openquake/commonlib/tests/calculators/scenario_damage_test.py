import os
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4, case_5, case_5a)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioDamageTestCase(CalculatorTestCase):
    def assert_ok(self, pkg, job_ini):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports='xml')
        got = out['damages_by_key', 'xml']
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith('.xml'))
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1(self):
        self.assert_ok(case_1, 'job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_2(self):
        self.assert_ok(case_2, 'job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        self.assert_ok(case_3, 'job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_4(self):
        self.assert_ok(case_4, 'job_haz.ini,job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_5(self):
        # this is a test for the rupture filtering
        self.assert_ok(case_5, 'job_haz.ini,job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_5a(self):
        # this is a case with two gsims
        self.assert_ok(case_5a, 'job_haz.ini,job_risk.ini')
