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
Module contains the test class for the Liu and Macedo (2022) Subuction Interface
and Inslab GMPEs
"""
import os
import unittest
import numpy as np
import pandas as pd
from openquake.hazardlib.imt import CAV
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.liu_macedo_2022 import LiuMacedo2022SInter


DATA_PATH = os.path.join(os.path.dirname(__file__), "data/liu_macedo_2022")


class LiuMacedo2022ConditionedTestCase(unittest.TestCase):
    """Test cases for the Liu and Macedo(2022) GMM when conditioned on fixed
    ground motion values
    """

    def setUp(self):
        self.sinter_table_file = os.path.join(
            DATA_PATH, "liu_macedo_2022_sinter_conditioning_gmvs.csv"
        )

        # self.sslab_table_file = os.path.join(
        #     DATA_PATH,
        #     "liu_macedo_2022_sslab_conditioning_gmvs.csv"
        #     )
        self.ctx_dtypes = np.dtype(
            [
                ("mag", float),
                ("vs30", float),
                ("PGA_MEAN", float),
                ("PGA_TOTAL_STDDEV", float),
                ("SA(1.0)_MEAN", float),
                ("SA(1.0)_TOTAL_STDDEV", float),
                ("Global_MEAN", float),
                ("Global_SIG", float),
                ("Global_TAU", float),
                ("Global_PHI", float),
                ("SA(1.0)_INTER_EVENT_STDDEV", float),
                ("SA(1.0)_INTRA_EVENT_STDDEV", float),
                ("PGA_INTER_EVENT_STDDEV", float),
                ("PGA_INTRA_EVENT_STDDEV", float),
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
        for imt in ["PGA", "SA(1.0)"]:
            for res_type in [
                "MEAN",
                "TOTAL_STDDEV",
                "INTER_EVENT_STDDEV",
                "INTRA_EVENT_STDDEV",
            ]:
                key = f"{imt}_{res_type}"
                ctx[key] = data[key].to_numpy()
        # Get the results for each region
        for region in ["Global"]:
            gsim = gsim_class(region=region)
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

    def test_liu_macedo_2022_sinter_conditioned(self):
        """Tests execution of LiuMacedo2022SInter conditioned on ground motion"""
        data = pd.read_csv(self.sinter_table_file, sep=",")
        gsim_sinter = LiuMacedo2022SInter
        self._compare_gsim_by_region(data, gsim_sinter)


#     def test_liu_macedo_2022_sslab_conditioned(self):
#         """Tests execution of LiuMacedo2022SSlab conditioned on ground motion
#         """
#         data = pd.read_csv(self.sslab_table_file, sep=",")
#         gsim_sslab = LiuMacedo2022SSlab
#         self._compare_gsim_by_region(data, gsim_sslab)


class LiuMacedo2022SInterTestCase(BaseGSIMTestCase):
    """Test case for the Liu and Macedo (2022) GMM conditioned on GMVs generated
    by the ParkerEtAl2020SInter GSIM
    """

    GSIM_CLASS = LiuMacedo2022SInter
    MEAN_FILE = "liu_macedo_2022/liu_macedo_2022_sinter_mean.csv"
    TOTAL_FILE = "liu_macedo_2022/liu_macedo_2022_sinter_total_stddev.csv"
    INTER_FILE = "liu_macedo_2022/liu_macedo_2022_sinter_inter_event_stddev.csv"
    INTRA_FILE = "liu_macedo_2022/liu_macedo_2022_sinter_intra_event_stddev.csv"
    GMM_GMPE = {"ParkerEtAl2020SInter": {}}

    def test_all(self):
        self.check(
            self.MEAN_FILE,
            self.TOTAL_FILE,
            self.INTER_FILE,
            self.INTRA_FILE,
            max_discrep_percentage=0.01,
            gmpe=self.GMM_GMPE,
        )


# class LiuMacedo2022SSlabTestCase(LiuMacedo2022SInterTestCase):
#     """Test case for the Liu and Macedo (2022) GMM conditioned on GMVs generated
#     by the ParkerEtAl2020SInter GSIM
#     """
#     GSIM_CLASS = LiuMacedo2022SSlab
#     MEAN_FILE = "liu_macedo_2022/liu_macedo_2022_sslab_mean.csv"
#     TOTAL_FILE = "liu_macedo_2022/liu_macedo_2022_sslab_total_stddev.csv"
#     INTER_FILE = "liu_macedo_2022/liu_macedo_2022_sslab_inter_event_stddev.csv"
#     INTRA_FILE = "liu_macedo_2022/liu_macedo_2022_sslab_intra_event_stddev.csv"
#     GMM_GMPE = {"ParkerEtAl2020SSlab": {}}
