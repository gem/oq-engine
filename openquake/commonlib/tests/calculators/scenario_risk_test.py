import os
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_3, occupants, case_6a)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini')
        for fname in out['agg', 'csv']:
            self.assertEqualFiles('expected/agg_loss.csv', fname)
        for fname in out['asset-loss', 'csv']:
            self.assertEqualFiles('expected/asset-loss.csv', fname)

    @attr('qa', 'risk', 'scenario_damage')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini')
        for fname in out['agg', 'csv']:
            self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_6a(self):
        out = self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini')
        for fname in out['agg', 'csv']:
            expected = os.path.join('expected', os.path.basename(fname))
            self.assertEqualFiles(expected, fname)
