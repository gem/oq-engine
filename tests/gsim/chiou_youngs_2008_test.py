from nhe.gsim.chiou_youngs_2008 import ChiouYoungs2008

from tests.gsim.utils import BaseGSIMTestCase


class ChiouYoungs2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip

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

    def test_inter_event_stddev(self):
        # data generated from opensha
        self.check('CY08/CY08_INTER_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.002)

    def test_intra_event_stddev(self):
        # data generated from opensha
        self.check('CY08/CY08_INTRA_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.001)
