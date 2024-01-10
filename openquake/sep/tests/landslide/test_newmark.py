import unittest

import numpy as np

from openquake.sep.landslide.common import static_factor_of_safety

from openquake.sep.landslide.newmark import (
    newmark_critical_accel,
    newmark_displ_from_pga_M,
    prob_failure_given_displacement,
)


class jibson_landslide_test(unittest.TestCase):
    """
    Tests the Newmark landslide functions given by Jibson with calibrations
    from his work on the Northridge earthquake.
    """

    def setUp(self):
        self.slopes = np.array([0.0, 3.0, 10.0, 25.0, 50.0, 70.0])
        self.fs = static_factor_of_safety(
            self.slopes,
            cohesion=20e3,
            friction_angle=32.0,
            saturation_coeff=0.0,
            slab_thickness=2.5,
            soil_dry_density=1500.0,
        )

    def test_newmark_critical_accel(self):
        ca = newmark_critical_accel(self.fs, self.slopes)
        ca_ = np.array(
            [11.46329996, 10.94148504, 9.66668506, 6.74308623, 1.75870504, 0.0]
        )
        np.testing.assert_allclose(ca, ca_)

    def test_newmark_displ_from_pga_M_M65(self):
        pgas = np.linspace(0.0, 2.0, num=10)
        Dns = newmark_displ_from_pga_M(pgas, critical_accel=1.0, M=6.5)

        Dn_ = np.array(
            [
                0.000000e00,
                0.000000e00,
                0.000000e00,
                0.000000e00,
                0.000000e00,
                6.006612e-05,
                6.681122e-04,
                1.929713e-03,
                3.775745e-03,
                6.137864e-03,
            ]
        )
        np.testing.assert_allclose(Dns, Dn_, atol=1e-9)

    def test_prob_failure_given_displacement(self):
        Dn_ = np.array(
            [
                0.000000e00,
                0.000000e00,
                0.000000e00,
                0.000000e00,
                0.000000e00,
                6.006612e-05,
                6.681122e-04,
                1.929713e-03,
                3.775745e-03,
                6.137864e-03,
            ]
        )

        pf = prob_failure_given_displacement(Dn_)

        pf_ = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                5.368313e-06,
                2.328222e-04,
                1.222611e-03,
                3.483592e-03,
                7.407753e-03,
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)
