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
Module contains the test class for the Macedo et al. (2021)
"""


import os
import numpy as np
import pandas as pd

import unittest
from openquake.hazardlib.imt import CAV
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.macedo_2021 import MacedoEtAl2021

DATA_PATH = os.path.join(os.path.dirname(__file__), "data/macedo_2021")


class MacedoEtAl2021ConditionedTestCase(unittest.TestCase):
    """
    Test cases for the Macedo et al (2021) GMM when conditioned on
    fixed ground motion values
    """

    def setUp(self):
        self.asc_table_file = os.path.join(
            DATA_PATH, "macedo_2021_conditioning_gmvs.csv"
        )

        self.ctx_dtypes = np.dtype(
            [
                ("mag", float),
                ("vs30", float),
                ("rrup", float),
                ("rjb", float),
                ("rx", float),
                ("dip", float),
                ("PGA_MEAN", float),
                ("PGA_TOTAL_STDDEV", float),
                ("PGA_INTER_EVENT_STDDEV", float),
                ("PGA_INTRA_EVENT_STDDEV", float),
                ("Global_MEAN", float),
                ("Global_SIG", float),
                ("Global_TAU", float),
                ("Global_PHI", float),
            ]
        )

    def _compare_gsim_by_region(self, data: pd.DataFrame, gsim_class):
        """Sorts the values from the data file in context and target, and then
        runs the GSIM for each region
        """
        n = data.shape[0]
        # Build the context from the data
        ctx = np.recarray(n, dtype=self.ctx_dtypes)
        ctx["mag"] = data["mag"].to_numpy()
        ctx["vs30"] = data["vs30"].to_numpy()
        ctx["rrup"] = data["rrup"].to_numpy()
        ctx["rjb"] = data["rjb"].to_numpy()
        ctx["rx"] = data["rx"].to_numpy()
        ctx["dip"] = data["dip"].to_numpy()
        for imt in ["PGA"]:
            for res_type in [
                "MEAN",
                "TOTAL_STDDEV",
                "INTER_EVENT_STDDEV",
                "INTRA_EVENT_STDDEV",
            ]:
                key = f"{imt}_{res_type}"
                ctx[key] = data[key].to_numpy()

        region = "Global"
        gsim = gsim_class()
        mean = np.zeros([1, n])
        sigma = np.zeros([1, n])
        tau = np.zeros([1, n])
        phi = np.zeros([1, n])

        gsim.compute(ctx, [CAV()], mean, sigma, tau, phi)
        np.testing.assert_array_almost_equal(
            np.exp(mean).flatten(), data[f"{region}_MEAN"].to_numpy()
        )
        np.testing.assert_array_almost_equal(
            sigma.flatten(), data[f"{region}_SIG"].to_numpy()
        )
        np.testing.assert_array_almost_equal(
            tau.flatten(), data[f"{region}_TAU"].to_numpy()
        )
        np.testing.assert_array_almost_equal(
            phi.flatten(), data[f"{region}_PHI"].to_numpy()
        )
        return

    def test_macedo_2021_asc_conditioned(self):
        """
        Tests execution of MacedoEtAl2021 conditioned on ground motion
        """
        data = pd.read_csv(self.asc_table_file, sep=",")
        gsim_asc = MacedoEtAl2021
        self._compare_gsim_by_region(data, gsim_asc)


class MacedoEtAl2021TestCase(BaseGSIMTestCase):
    """
    Test case for the Macedo et al. (2021) GMM conditioned on GMVs generated
    by the AbrahamsonEtAl2014 GSIM
    """

    GSIM_CLASS = MacedoEtAl2021
    MEAN_FILE = "macedo_2021/macedo_2021_mean.csv"
    TOTAL_FILE = "macedo_2021/macedo_2021_total_stddev.csv"
    INTER_FILE = "macedo_2021/macedo_2021_inter_event_stddev.csv"
    INTRA_FILE = "macedo_2021/macedo_2021_intra_event_stddev.csv"
    GMM_GMPE = {"AbrahamsonEtAl2014": {}}

    def test_all(self):
        self.check(
            self.MEAN_FILE,
            self.TOTAL_FILE,
            self.INTER_FILE,
            self.INTRA_FILE,
            max_discrep_percentage=0.01,
            gmpe=self.GMM_GMPE,
        )
