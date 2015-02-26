import unittest
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4, case_5)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioDamageTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1(self):
        raise unittest.SkipTest(case_1)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_2(self):
        raise unittest.SkipTest(case_2)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        raise unittest.SkipTest(case_3)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected/dmg_dist_per_asset.xml',
            out['dmg_dist_per_asset', 'xml'])
        self.assertEqualFiles(
            'expected/dmg_dist_per_taxonomy.xml',
            out['dmg_dist_per_taxonomy', 'xml'])
        self.assertEqualFiles(
            'expected/dmg_dist_total.xml', out['dmg_dist_total', 'xml'])
        self.assertEqualFiles(
            'expected/collapse_map.xml', out['collapse_map', 'xml'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_5(self):
        # this is a test for the rupture filtering
        out = self.run_calc(case_5.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected/dmg_dist_total.xml', out['dmg_dist_total', 'xml'])

