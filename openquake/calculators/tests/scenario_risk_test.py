from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario_risk import (
    case_1, case_2, case_1g, case_3, occupants, case_6a)

from openquake.calculators.tests import CalculatorTestCase
from openquake.commonlib.datastore import view


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')

        [fname] = out['loss_map-rlzs', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv,xml')

        [fname] = out['loss_map-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_map.xml', fname)

        [fname] = out['loss_map-rlzs', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

        # check wrong time_event
        self.calc.datastore.attrs['time_event'] = "'Day'"
        with self.assertRaises(ValueError) as ctx:
            self.calc.pre_execute()
        msg = str(ctx.exception)
        self.assertIn("time_event is 'Day' in", msg)
        self.assertIn("but the exposure contains day, night, transit", msg)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_6a(self):
        # case with two gsims
        out = self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        f1, f2 = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg-gsimltp_b1_structural.csv', f1)
        self.assertEqualFiles('expected/agg-gsimltp_b2_structural.csv', f2)

        # testing the totlosses view
        dstore = self.calc.datastore
        text = view('totlosses', dstore)
        self.assertEqual(text, '''\
=============== ===================
structural-mean structural-mean_ins
=============== ===================
2.6872496E+03   NAN                
3.2341374E+03   NAN                
=============== ===================''')

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1g(self):
        out = self.run_calc(case_1g.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg-gsimltp_@.csv', fname)
