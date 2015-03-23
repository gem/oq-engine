from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_3, occupants)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles('expected/agg_loss.csv',
                              out['agg']['agg_loss', 'csv'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles('expected/agg_loss.csv',
                              out['agg']['agg_loss', 'csv'])

