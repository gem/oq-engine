from nose.plugins.attrib import attr

from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based_risk import case_2


class EventLossTestCase(CalculatorTestCase):
    @attr('qa', 'risk', 'event_loss')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_haz.ini,job_risk.ini',
                            calculation_mode='event_loss', exports='csv')

        self.assertEqualFiles(
            'expected/rlz-000-structural-event-loss-asset.csv',
            out['rlz-000-structural-event-loss-asset'])

        self.assertEqualFiles(
            'expected/rlz-000-structural-event-loss.csv',
            out['rlz-000-structural-event-loss'])
