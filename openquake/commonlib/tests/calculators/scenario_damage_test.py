from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4, case_5)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioDamageTestCase(CalculatorTestCase):
    KEYS = ['dmg_dist_per_asset', 'dmg_dist_per_taxonomy',
            'dmg_dist_total', 'collapse_map']

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini')
        for key in self.KEYS:
            self.assertEqualFiles('expected/%s.xml' % key, out[key, 'xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini')
        for key in self.KEYS:
            self.assertEqualFiles('expected/%s.xml' % key, out[key, 'xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_risk.ini')
        for key in self.KEYS:
            self.assertEqualFiles('expected/%s.xml' % key, out[key, 'xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini')
        for key in self.KEYS:
            self.assertEqualFiles('expected/%s.xml' % key, out[key, 'xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_5(self):
        # this is a test for the rupture filtering
        out = self.run_calc(case_5.__file__, 'job_haz.ini,job_risk.ini')
        for key in self.KEYS:
            self.assertEqualFiles('expected/%s.xml' % key, out[key, 'xml'])
