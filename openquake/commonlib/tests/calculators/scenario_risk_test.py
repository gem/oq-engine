import os
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_3, occupants)

from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.commonlib.calculators.scenario import ScenarioCalculator
from openquake.commonlib import readinput


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles('expected/agg_loss.csv', out['agg', 'csv'])
        self.assertEqualFiles('expected/asset-loss.csv',
                              out['asset-loss', 'csv'])

    @attr('qa', 'risk', 'scenario_damage')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles('expected/agg_loss.csv', out['agg', 'csv'])


class _ScenarioRiskQATestCase(CalculatorTestCase):
    cases = ['case_3a', 'case_7a']

    @attr('qa', 'risk', 'scenario_damage')
    def test_all(self):
        datadir = os.path.join(
            os.path.dirname(os.path.dirname(case_3.__file__)), 'data')
        oq = readinput.get_oqparam(os.path.join(datadir, 'case_7a.ini'))
        ScenarioCalculator(oq).run()  # save cache

        for case in self.cases:
            out = self.run_calc(datadir, '%s.ini' % case, usecache='0')
            print out.keys()
