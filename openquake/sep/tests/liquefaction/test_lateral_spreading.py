import unittest

import numpy as np
from openquake.sep.liquefaction.lateral_spreading import (
    hazus_lateral_spreading_displacement,
    hazus_lateral_spreading_displacement_fn,
    _hazus_displacement_correction_factor,
)


class test_lateral_spreading(unittest.TestCase):
    def test_hazus_displacement_correction_factor(self):
        """
        Replicates Figure 4.10 in the HAZUS manual: Displacement
        Correction Factor, KΔ for Lateral Spreading Displacement
        Relationships (after Seed & Idriss, 1982).
        """
        mags = np.linspace(4.0, 8.5, num=20)
        corrs = np.array(
            [
                -0.0163,
                0.02033406,
                0.05897747,
                0.10031577,
                0.14503448,
                0.19381913,
                0.24735526,
                0.30632838,
                0.37142404,
                0.44332776,
                0.52272508,
                0.61030151,
                0.7067426,
                0.81273387,
                0.92896085,
                1.05610908,
                1.19486408,
                1.34591138,
                1.50993651,
                1.687625,
            ]
        )

        disp_corr = _hazus_displacement_correction_factor(mags)
        np.testing.assert_array_almost_equal(disp_corr, corrs)

    def test_hazus_lateral_spreading_displacements_fn(self):
        """
        Replicates Figure 4.9 in the HAZUS manual
        """
        pga = np.linspace(0.0, 4.0, num=20)
        pga_threshold = 1.0

        disps = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.64855263,
                3.24276316,
                5.83697368,
                8.43118421,
                11.02539474,
                14.26815789,
                18.15947368,
                22.05078947,
                25.94210526,
                29.83342105,
                42.15592105,
                57.28881579,
                72.42171053,
                87.55460526,
                102.6875,
            ]
        )

        d_in = hazus_lateral_spreading_displacement_fn(7.5, pga, pga_threshold)

        np.testing.assert_array_almost_equal(disps, d_in)

    def test_hazus_lateral_spreading_displacements_1(self):
        d = hazus_lateral_spreading_displacement(7.5, 0.7, "h")
        np.testing.assert_almost_equal(d, 5.955532517756293)

    def test_hazus_lateral_spreading_displacements_2(self):
        mag = 7.5
        pga = 0.7
        ds = hazus_lateral_spreading_displacement(
            mag, pga, ["n", "l", "m", "h", "vh"]
        )

        ds_answer = np.array([0.0, 1.391073, 3.825452, 5.955533, 9.505667])

        np.testing.assert_array_almost_equal(ds, ds_answer)

    def test_hazus_lateral_spreading_displacements_3(self):
        mag = 7.5
        pga = np.array([1.5, 1.0, 0.8, 0.6, 0.2])
        ds = hazus_lateral_spreading_displacement(
            mag, pga, ["n", "l", "m", "h", "vh"]
        )

        ds_answer = np.array(
            [0.0, 3.99933571, 5.04264067, 4.43404611, 0.41732199]
        )

        np.testing.assert_array_almost_equal(ds, ds_answer)
