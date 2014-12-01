from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase


# skeleton of the test: to be filled with something useful
class ClassicalTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        pass
