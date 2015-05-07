import os
import unittest
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_3, occupants, case_6a)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_1(self):
        raise unittest.SkipTest

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_2(self):
        raise unittest.SkipTest

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini')
        agg_loss, asset_loss = out['losses_by_key', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', agg_loss)
        self.assertEqualFiles('expected/asset-loss.csv', asset_loss)

    @attr('qa', 'risk', 'scenario_damage')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini')
        agg_loss, asset_loss = out['losses_by_key', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', agg_loss)
        self.assertEqualFiles('expected/asset-loss.csv', asset_loss)

    @attr('qa', 'risk', 'scenario_damage')
    def test_case_6a(self):
        # case with two gsims
        out = self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini')
        fnames = out['losses_by_key', 'csv'][:2]
        # comparing agg-gsimltp_b1.csv and agg-gsimltp_b2.csv
        for fname in fnames:
            expected = os.path.join('expected', os.path.basename(fname))
            self.assertEqualFiles(expected, fname)
