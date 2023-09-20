import unittest

import numpy as np

from openquake.sep.liquefaction.vertical_settlement import (
    hazus_vertical_settlement)

class TestHazusVerticalSettlement(unittest.TestCase):
    def setUp(self):
        self.all_liq_types = ['vh', 'h', 'm', 'l', 'vl', 'n']
        self.mag = 7.5
        self.pga = np.array([0.15, 0.20, 0.25, 0.30, 0.35, 0.40])

    def test_hazus_vertical_settlement_list_m(self):
        v_settle = hazus_vertical_settlement(self.all_liq_types, mag=self.mag,pga=self.pga, return_unit='m')
        np.testing.assert_array_almost_equal(
            v_settle,
            np.array([0.039243, 0.017734, 0.003213, 0.000591, 0., 0.])
        )

    def test_hazus_vertical_settlement_list_in(self):
        v_settle = hazus_vertical_settlement(self.all_liq_types, mag=self.mag,pga=self.pga, return_unit='in')
        np.testing.assert_array_almost_equal(
            v_settle,
            np.array([1.545019, 0.698172, 0.126501, 0.023263, 0. , 0.])
        )
