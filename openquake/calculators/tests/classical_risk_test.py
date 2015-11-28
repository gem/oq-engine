from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3, case_4)
from openquake.calculators.tests import CalculatorTestCase


class ClassicalRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='xml')
        [fname] = out['loss_curves-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_curves.xml', fname)

        clp = self.calc.oqparam.conditional_loss_poes
        fnames = out['loss_maps-rlzs', 'xml']
        self.assertEqual(len(fnames), 3)  # for 3 conditional loss poes
        for poe, fname in zip(clp, fnames):
            self.assertEqualFiles('expected/loss_map-poe-%s.xml' % poe, fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini', exports='xml')
        [fname] = out['loss_curves-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_curves.xml', fname)

        clp = self.calc.oqparam.conditional_loss_poes
        fnames = out['loss_maps-rlzs', 'xml']
        self.assertEqual(len(fnames), 1)  # for 1 conditional loss poe
        for poe, fname in zip(clp, fnames):
            self.assertEqualFiles('expected/loss_map-poe-%s.xml' % poe, fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [fname] = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        fnames = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fnames[0])
        self.assertEqualFiles('expected/loss_curves-001.csv', fnames[1])

    # TODO: tests with more than a loss type
    # tests with more than one pair IMT, taxo
