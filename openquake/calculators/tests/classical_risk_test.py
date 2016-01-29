from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3, case_4, case_5, case_master)
from openquake.calculators.tests import CalculatorTestCase
from openquake.commonlib.writers import scientificformat
from openquake.commonlib.datastore import view


class ClassicalRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='xml')

        # check loss ratios
        lrs = self.calc.datastore['composite_risk_model/VF-structural']
        got = scientificformat(lrs.mean_loss_ratios, '%.2f')
        self.assertEqual(got, '0.05 0.10 0.20 0.40 0.80')

        # check loss curves
        [fname] = out['loss_curves-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_curves.xml', fname)

        # check loss maps
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
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        [fname] = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        fnames = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fnames[0])
        self.assertEqualFiles('expected/loss_curves-001.csv', fnames[1])

    @attr('qa', 'risk', 'classical_risk')
    def test_case_5(self):
        # test with different curve resolution for different taxonomies
        out = self.run_calc(case_5.__file__, 'job_h.ini,job_r.ini',
                            exports='xml', individual_curves='false')

        # check mean loss curves
        [fname] = out['loss_curves-stats', 'xml']
        self.assertEqualFiles('expected/loss_curves-mean.xml', fname)

        # check individual avg losses
        text = view('loss_curves_avg', self.calc.datastore)
        self.assertEqual(text, '''========= ============= ============ ===================================================
asset_ref lon           lat          structural                                         
========= ============= ============ ===================================================
a6        -7.816800E+01 1.559329E+01 2.837295E-03 2.886262E-03 2.872555E-03 2.889799E-03
a7        -7.816812E+01 1.559329E+01 1.073631E-06 1.110482E-06 1.096380E-06 1.115112E-06
========= ============= ============ ===================================================''')

    @attr('qa', 'risk', 'classical_risk')
    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini')
        # TODO: check the expected mean/quantiles curves
