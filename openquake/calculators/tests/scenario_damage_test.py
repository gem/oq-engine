import os
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_2, case_3, case_4, case_5, case_5a, case_6, case_7)

from openquake.calculators.tests import CalculatorTestCase


class ScenarioDamageTestCase(CalculatorTestCase):
    def assert_ok(self, pkg, job_ini, exports='xml'):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports=exports)
        got = (out['dmg_by_asset', exports] +
               out['dmg_by_taxon', exports] +
               out['dmg_total', exports])
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith(exports))
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1(self):
        self.assert_ok(case_1, 'job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1c(self):
        # this is a case with more hazard sites than exposure sites
        test_dir = os.path.dirname(case_1c.__file__)
        out = self.run_calc(
            test_dir, 'job_haz.ini,job_risk.ini', exports='xml')
        [total] = out['dmg_total', 'xml']
        self.assertEqualFiles('expected/dmg_dist_total.xml', total)

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
        # NB: the exposure file is imported twice on purpose, to make
        # sure that nothing changes; TODO: document the issue (MS)
        self.assert_ok(case_5, 'job_haz.ini,job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_5a(self):
        # this is a case with two gsims
        self.assert_ok(case_5a, 'job_haz.ini,job_risk.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_6(self):
        # this is a case with 5 assets on the same point
        self.assert_ok(case_6, 'job_h.ini,job_r.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_7(self):
        # this is a case with three loss types
        self.assert_ok(case_7, 'job_h.ini,job_r.ini', exports='csv')
