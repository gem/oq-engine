# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Module contains the test class for the conditional GMPE
"""
from typing import List
import unittest
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib.gsim.conditional_gmpe import ConditionalGMPE


imt_dtypes_basic = np.dtype([
    ("PGA_MEAN", float),
    ("PGA_TOTAL_STDDEV", float),
    ("SA(1.0)_MEAN", float),
    ("SA(1.0)_TOTAL_STDDEV", float)
])


imt_dtypes_inter_only = np.dtype([
    ("PGA_MEAN", float),
    ("PGA_TOTAL_STDDEV", float),
    ("PGA_INTER_EVENT_STDDEV", float),
    ("SA(1.0)_MEAN", float),
    ("SA(1.0)_TOTAL_STDDEV", float),
    ("SA(1.0)_INTER_EVENT_STDDEV", float),
])


imt_dtypes_full = np.dtype([
    ("PGA_MEAN", float),
    ("PGA_TOTAL_STDDEV", float),
    ("PGA_INTER_EVENT_STDDEV", float),
    ("PGA_INTRA_EVENT_STDDEV", float),
    ("SA(1.0)_MEAN", float),
    ("SA(1.0)_TOTAL_STDDEV", float),
    ("SA(1.0)_INTER_EVENT_STDDEV", float),
    ("SA(1.0)_INTRA_EVENT_STDDEV", float),
])


class ConditionalGMPETestCase(unittest.TestCase):
    """Tests the main ConditionalGMPE for both cases when ground motion values
    are supplied and ground motion models are called
    """
    def setUp(self):
        class DummyGMPE(GMPE):
            """
            """
            DEFINED_FOR_TECTONIC_REGION_TYPE = ''
            DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
            DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
            DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
                const.StdDev.TOTAL,
            }

            REQUIRES_SITES_PARAMETERS = {}
            REQUIRES_RUPTURE_PARAMETERS = {"mag", }
            REQUIRES_DISTANCES = {"rrup", }

            def compute(self, ctx: np.recarray, imts: List, mean: np.ndarray,
                        sig: np.ndarray, tau: np.ndarray, phi: np.ndarray):
                for m, imt in enumerate(imts):
                    if str(imt) == "PGA":
                        mean[m] += np.log(1.0)
                        sig[m] += 0.8
                    else:
                        mean[m] += np.log(0.1)
                        sig[m] += 0.6
                return
        self.dummy_gmpe = DummyGMPE

    def test_instantiation_unknown_gmpe(self):
        # Should raise a basic KeyError
        with self.assertRaises(KeyError) as ke:
            _ = ConditionalGMPE(gmpe={"XYZ": {}})
        self.assertEqual(str(ke.exception), "'XYZ'")

    def test_usage_no_gmpe_minimum(self):
        # Should return the GMVs in the ctx for mean and sigma only
        ctx = np.recarray(3, dtype=imt_dtypes_basic)
        ctx["PGA_MEAN"] = np.array([0.1, 0.2, 0.3])
        ctx["PGA_TOTAL_STDDEV"] = np.array([0.1, 0.1, 0.1])
        ctx["SA(1.0)_MEAN"] = np.array([0.05, 0.1, 0.15])
        ctx["SA(1.0)_TOTAL_STDDEV"] = np.array([0.08, 0.1, 0.12])
        cgmm = ConditionalGMPE()
        cgmm.REQUIRES_IMTS = {"PGA", "SA(1.0)"}
        mean_gms, sigma_gms, tau_gms, phi_gms =\
            cgmm.get_conditioning_ground_motions(ctx)
        for imt_string in ["PGA", "SA(1.0)"]:
            np.testing.assert_array_almost_equal(mean_gms[imt_string],
                                                 ctx[f"{imt_string}_MEAN"])
            np.testing.assert_array_almost_equal(
                sigma_gms[imt_string],
                ctx[f"{imt_string}_TOTAL_STDDEV"]
                )
            np.testing.assert_array_almost_equal(tau_gms[imt_string],
                                                 np.zeros(3))
            np.testing.assert_array_almost_equal(phi_gms[imt_string],
                                                 np.zeros(3))

    def test_usage_no_gmpe_inter_only(self):
        # Should return the GMVs in the ctx for mean, sigma and tau,
        # but not for phi
        ctx = np.recarray(3, dtype=imt_dtypes_inter_only)
        ctx["PGA_MEAN"] = np.array([0.1, 0.2, 0.3])
        ctx["PGA_TOTAL_STDDEV"] = np.array([0.1, 0.1, 0.1])
        ctx["PGA_INTER_EVENT_STDDEV"] = np.array([0.05, 0.05, 0.05])
        ctx["SA(1.0)_MEAN"] = np.array([0.05, 0.1, 0.15])
        ctx["SA(1.0)_TOTAL_STDDEV"] = np.array([0.08, 0.1, 0.12])
        ctx["SA(1.0)_INTER_EVENT_STDDEV"] = np.array([0.04, 0.05, 0.06])
        cgmm = ConditionalGMPE()
        cgmm.REQUIRES_IMTS = {"PGA", "SA(1.0)"}
        mean_gms, sigma_gms, tau_gms, phi_gms =\
            cgmm.get_conditioning_ground_motions(ctx)
        print(tau_gms["PGA"], tau_gms["SA(1.0)"])
        for imt_string in ["PGA", "SA(1.0)"]:
            np.testing.assert_array_almost_equal(mean_gms[imt_string],
                                                 ctx[f"{imt_string}_MEAN"])
            np.testing.assert_array_almost_equal(
                sigma_gms[imt_string],
                ctx[f"{imt_string}_TOTAL_STDDEV"]
                )
            np.testing.assert_array_almost_equal(
                tau_gms[imt_string],
                ctx[f"{imt_string}_INTER_EVENT_STDDEV"]
                )
            np.testing.assert_array_almost_equal(phi_gms[imt_string],
                                                 np.zeros(3))

    def test_usage_no_gmpe_full(self):
        # Should return the GMVs in the ctx for mean, sigma, tau and phi
        ctx = np.recarray(3, dtype=imt_dtypes_full)
        ctx["PGA_MEAN"] = np.array([0.1, 0.2, 0.3])
        ctx["PGA_TOTAL_STDDEV"] = np.array([0.1, 0.1, 0.1])
        ctx["PGA_INTER_EVENT_STDDEV"] = np.array([0.07, 0.07, 0.07])
        ctx["PGA_INTRA_EVENT_STDDEV"] = np.array([0.03, 0.03, 0.03])
        ctx["SA(1.0)_MEAN"] = np.array([0.05, 0.1, 0.15])
        ctx["SA(1.0)_TOTAL_STDDEV"] = np.array([0.08, 0.1, 0.12])
        ctx["SA(1.0)_INTER_EVENT_STDDEV"] = np.array([0.06, 0.07, 0.08])
        ctx["SA(1.0)_INTRA_EVENT_STDDEV"] = np.array([0.02, 0.03, 0.04])
        cgmm = ConditionalGMPE()
        cgmm.REQUIRES_IMTS = {"PGA", "SA(1.0)"}
        mean_gms, sigma_gms, tau_gms, phi_gms =\
            cgmm.get_conditioning_ground_motions(ctx)
        for imt_string in ["PGA", "SA(1.0)"]:
            np.testing.assert_array_almost_equal(mean_gms[imt_string],
                                                 ctx[f"{imt_string}_MEAN"])
            np.testing.assert_array_almost_equal(
                sigma_gms[imt_string],
                ctx[f"{imt_string}_TOTAL_STDDEV"]
                )
            np.testing.assert_array_almost_equal(
                tau_gms[imt_string],
                ctx[f"{imt_string}_INTER_EVENT_STDDEV"]
                )
            np.testing.assert_array_almost_equal(
                phi_gms[imt_string],
                ctx[f"{imt_string}_INTRA_EVENT_STDDEV"]
                )

    def test_usage_gmpe_empty_ctx(self):
        # Should raise an error saying it needs a GMPE if not GMVs are defined
        # Provide data but no GMVs and no GMPE
        ctx_empty = np.recarray(3, dtype=np.dtype([("mag", float),
                                                   ("rrup", float)]))
        ctx_empty["mag"] = np.array([5., 6., 7.])
        ctx_empty["rrup"] = np.array([10., 20., 50.0])
        with self.assertRaises(ValueError) as ve:
            cgmm = ConditionalGMPE()
            cgmm.REQUIRES_IMTS = {"PGA", "SA(1.0)"}
            _ = cgmm.get_conditioning_ground_motions(ctx_empty)
        self.assertEqual(
            str(ve.exception),
            "Conditioning ground motions must be specified in ctx "
            "or a GMPE must be provided"
        )

    def test_usage_with_gmpe(self):
        # Tests to retrieve values from a GMPE
        ctx_empty = np.recarray(3, dtype=np.dtype([("mag", float),
                                                   ("rrup", float)]))
        ctx_empty["mag"] = np.array([5., 6., 7.])
        ctx_empty["rrup"] = np.array([10., 20., 50.0])
        cgmm = ConditionalGMPE(gmpe={"DummyGMPE": {}})
        cgmm.REQUIRES_IMTS = {"PGA", "SA(1.0)"}
        mean_gms, sigma_gms, tau_gms, phi_gms = \
            cgmm.get_conditioning_ground_motions(ctx_empty)
        null_array = np.zeros(3, dtype=float)
        # Mean and sigma take constant values from Dummy GMPE
        np.testing.assert_array_almost_equal(mean_gms["PGA"],
                                             null_array + 1.0)
        np.testing.assert_array_almost_equal(mean_gms["SA(1.0)"],
                                             null_array + 0.1)

        np.testing.assert_array_almost_equal(sigma_gms["PGA"],
                                             null_array + 0.8)
        np.testing.assert_array_almost_equal(sigma_gms["SA(1.0)"],
                                             null_array + 0.6)
        for imt_str in ["PGA", "SA(1.0)"]:
            np.testing.assert_array_almost_equal(tau_gms[imt_str], null_array)
            np.testing.assert_array_almost_equal(phi_gms[imt_str], null_array)
