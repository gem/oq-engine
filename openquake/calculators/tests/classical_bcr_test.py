from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_bcr import case_1
from openquake.calculators.tests import CalculatorTestCase


class ClassicalBCRTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_bcr')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='xml')
        [fname] = out['bcr-rlzs', 'xml']
        self.assertEqualFiles('expected/bcr-structural.xml', fname)
