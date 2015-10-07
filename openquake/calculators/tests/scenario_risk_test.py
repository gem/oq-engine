import os
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_1, case_2, case_1g, case_3, occupants, case_6a)

from openquake.calculators.tests import CalculatorTestCase


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [assetcol] = out['assetcol', 'csv']
        self.assertEqualFiles('expected/assetcol.csv', assetcol)

        [fname] = out['avglosses', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [fname] = out['avglosses', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_6a(self):
        # case with two gsims
        out = self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        fnames = out['agglosses', 'csv']
        # comparing agg-gsimltp_b1.csv and agg-gsimltp_b2.csv
        for fname in fnames:
            expected = os.path.join('expected', os.path.basename(fname))
            self.assertEqualFiles(expected, fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1g(self):
        out = self.run_calc(case_1g.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [fname] = out['agglosses', 'csv']
        self.assertEqualFiles('expected/agg-gsimltp_@.csv', fname)
