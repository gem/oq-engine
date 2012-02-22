from nhe.attrel.chiou_youngs_2008 import ChiouYoungs2008

from tests.attrel.base import BaseAttRelTestCase


class ChiouYoungs2008TestCase(BaseAttRelTestCase):
    ATTREL_CLASS = ChiouYoungs2008

    def test_total_stddev_hanging_wall_strike_slip_measured(self):
        self.check('CY08/CY08_SIGMEAS_MS_HW_SS.csv',
                    max_discrep_percentage=0.015)

    def test_total_stddev_hanging_wall_strike_slip_inferred(self):
        self.check('CY08/CY08_SIGINFER_MS_HW_SS.csv',
                   max_discrep_percentage=0.015)

    def test_mean_hanging_wall_normal_slip(self):
        self.check('CY08/CY08_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('CY08/CY08_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('CY08/CY08_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)
