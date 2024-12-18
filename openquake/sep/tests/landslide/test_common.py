import unittest

import numpy as np

from openquake.sep.landslide.common import (
    static_factor_of_safety,
    rock_slope_static_factor_of_safety,
)

slope_array = np.linspace(0.0, 60.0)


class test_factors_of_safety(unittest.TestCase):
    def test_static_factor_of_safety_wet(self):
        sfs = static_factor_of_safety(
            slope_array, cohesion=20e3, friction_angle=30.0
        )

        sfs_ = np.array(
            [
                6.20240095e06,
                5.06510388e01,
                2.53226659e01,
                1.68786065e01,
                1.26556254e01,
                1.01210752e01,
                8.43074034e00,
                7.22281393e00,
                6.31639255e00,
                5.61097425e00,
                5.04625782e00,
                4.58386974e00,
                4.19822763e00,
                3.87162059e00,
                3.59139796e00,
                3.34828255e00,
                3.13531646e00,
                2.94717892e00,
                2.77973153e00,
                2.62970712e00,
                2.49449194e00,
                2.37197006e00,
                2.26041028e00,
                2.15838244e00,
                2.06469473e00,
                1.97834603e00,
                1.89848920e00,
                1.82440261e00,
                1.75546769e00,
                1.69115120e00,
                1.63099097e00,
                1.57458445e00,
                1.52157942e00,
                1.47166631e00,
                1.42457198e00,
                1.38005450e00,
                1.33789879e00,
                1.29791303e00,
                1.25992557e00,
                1.22378236e00,
                1.18934475e00,
                1.15648761e00,
                1.12509770e00,
                1.09507231e00,
                1.06631808e00,
                1.03874991e00,
                1.01229011e00,
                9.86867591e-01,
                9.62417171e-01,
                9.38878988e-01,
            ]
        )

        np.testing.assert_allclose(sfs, sfs_, rtol=1e-4)

    def test_static_factor_of_safety_dry(self):
        sfs = static_factor_of_safety(
            slope_array,
            cohesion=20e3,
            friction_angle=30.0,
            saturation_coeff=0.0,
        )

        sfs_ = np.array(
            [
                6.42293250e06,
                5.24517723e01,
                2.62226213e01,
                1.74781196e01,
                1.31047800e01,
                1.04799047e01,
                8.72926131e00,
                7.47817851e00,
                6.53932067e00,
                5.80861236e00,
                5.22360825e00,
                4.74457040e00,
                4.34500675e00,
                4.00657663e00,
                3.71617953e00,
                3.46420835e00,
                3.24345774e00,
                3.04841769e00,
                2.87480262e00,
                2.71922912e00,
                2.57899045e00,
                2.45189541e00,
                2.33615117e00,
                2.23027666e00,
                2.13303766e00,
                2.04339736e00,
                1.96047846e00,
                1.88353361e00,
                1.81192218e00,
                1.74509189e00,
                1.68256409e00,
                1.62392184e00,
                1.56880031e00,
                1.51687887e00,
                1.46787460e00,
                1.42153687e00,
                1.37764289e00,
                1.33599393e00,
                1.29641217e00,
                1.25873798e00,
                1.22282769e00,
                1.18855164e00,
                1.15579246e00,
                1.12444371e00,
                1.09440859e00,
                1.06559888e00,
                1.03793402e00,
                1.01134028e00,
                9.85750046e-01,
                9.61101210e-01,
            ]
        )

        np.testing.assert_allclose(sfs, sfs_, rtol=1e-4)

    @unittest.skip
    def test_rock_slope_static_factor_of_safety(self):
        rock_slope_static_factor_of_safety(
            slope_array,
            cohesion=20e3,
            friction_angle=30.0,
        )
