import unittest
import numpy as np
from openquake.sep.landslide.static_safety_factor import infinite_slope_fs

slope = np.linspace(0.0, 1.0, 12)


class InfiniteSlopeTestCase(unittest.TestCase):
    def test_infinite_slope_wet(self):
        sfs = infinite_slope_fs(
            slope, cohesion=20e3, friction_angle=30.0, saturation_coeff= 0.1, slab_thickness = 2.5, soil_dry_density= 1500.0
        )
        sfs_ = np.array(
            [
                1.082523e+05, 
                1.193242e+01, 
                6.002900e+00, 
                4.042058e+00,
                3.072719e+00, 
                2.499313e+00, 
                2.123257e+00, 
                1.859423e+00,
                1.665260e+00, 
                1.517152e+00, 
                1.400959e+00, 
                1.307716e+00
            ]
        )
        np.testing.assert_allclose(sfs, sfs_, rtol=1e-4)

    def test_infinite_slope_dry(self):
        sfs = infinite_slope_fs(
            slope,
            cohesion=20e3,
            friction_angle=30.0,
            saturation_coeff=0.0,
            slab_thickness = 2.5,
            soil_dry_density= 1500.0
        )
        sfs_ = np.array(
            [
                1.121013e+05, 
                1.235581e+01, 
                6.214595e+00, 
                4.183188e+00,
                3.178566e+00, 
                2.583991e+00, 
                2.193822e+00, 
                1.919907e+00,
                1.718184e+00, 
                1.564195e+00, 
                1.443298e+00, 
                1.346206e+00
            ]
        )
        np.testing.assert_allclose(sfs, sfs_, rtol=1e-4)



