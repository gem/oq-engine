import numpy
from numpy.testing import assert_almost_equal as aae
from nose.plugins.attrib import attr

from openquake.qa_tests_data.scenario import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8)

from openquake.commonlib.tests.calculators import CalculatorTestCase


class ClassicalTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini')
        self.assertEqualFiles('expected.xml', out['gmf_xml'])
