import unittest

import numpy as np

from openquake.sep.liquefaction.vertical_settlement import (
    hazus_vertical_settlement)

class TestHazusVerticalSettlement(unittest.TestCase):
    def setUp(self):
        self.all_liq_types = ['vh', 'h', 'm', 'l', 'vl', 'n']

    def test_hazus_vertical_settlement_single_m(self):
        v_settle = hazus_vertical_settlement('vh', return_unit='m')
        np.testing.assert_almost_equal(v_settle, 0.3047999902464003)

    def test_hazus_vertical_settlement_single_in(self):
        assert hazus_vertical_settlement('vh', return_unit='in') == 12.

    def test_hazus_vertical_settlement_list_m(self):
        v_settle = hazus_vertical_settlement(self.all_liq_types)
        np.testing.assert_array_almost_equal(
            v_settle,
            np.array([0.3047999902464003, 0.15239999512320015,
                      0.05079999837440005, 0.025399999187200026, 0.0, 0.0])
        )
