import unittest

import numpy as np

from openquake.sep.liquefaction.vertical_settlement import (
    hazus_vertical_settlement)

class TestHazusVerticalSettlement(unittest.TestCase):
    def setUp(self):
        self.all_liq_types = ['vh', 'h', 'm', 'l', 'vl', 'n']
        # self.mag = 7.5
        # self.pga = np.array([0.15, 0.20, 0.25, 0.30, 0.35, 0.40])

    def test_hazus_vertical_settlement_list_m(self):
        v_settle = hazus_vertical_settlement(self.all_liq_types, return_unit='m')
        np.testing.assert_array_almost_equal(
            v_settle,
            np.array([0.3048, 0.1524, 0.0508, 0.0254, 0., 0.])
        )

    def test_hazus_vertical_settlement_list_in(self):
        v_settle = hazus_vertical_settlement(self.all_liq_types, return_unit='in')
        np.testing.assert_array_almost_equal(
            v_settle,
            np.array([12., 6., 2., 1., 0., 0.])
        )
