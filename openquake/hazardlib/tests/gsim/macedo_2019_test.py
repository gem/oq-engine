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
Module contains the test class for the Macedo et al. (2019) Subuction Interface
and Inslab GMPEs
"""
import os
import unittest
import numpy as np
import pandas as pd
from openquake.hazardlib.imt import IA
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.macedo_2019 import MacedoEtAl2019SInter,\
    MacedoEtAl2019SSlab


DATA_PATH = os.path.join(os.path.dirname(__file__), "data/macedo_2019")


class MacedoEtAl2019ConditionedTestCase(unittest.TestCase):
    """Test cases for the Macedo et al (2019) GMM when conditioned on fixed
    ground motion values
    """
    def setUp(self):
        self.sinter_table_file = os.path.join(
            DATA_PATH,
            "macedo_2019_sinter_conditioning_gmvs.csv"
            )

        self.sslab_table_file = os.path.join(
            DATA_PATH,
            "macedo_2019_sslab_conditioning_gmvs.csv"
            )
        self.ctx_dtypes = np.dtype([
            ("mag", float),
            ("vs30", float),
            ("PGA_MEAN", float),
            ("PGA_TOTAL_STDDEV", float),
            ("SA(1.0)_MEAN", float),
            ("SA(1.0)_TOTAL_STDDEV", float)
        ])

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
            for res_type in ["MEAN", "TOTAL_STDDEV"]:
                key = f"{imt}_{res_type}"
                ctx[key] = data[key].to_numpy()
        # Get the results for each region
        for region in ["Global", "Japan", "Taiwan",
                       "South America", "New Zealand"]:
            gsim = gsim_class(region=region)
            mean = np.zeros([1, n])
            sigma = np.zeros([1, n])
            tau = np.zeros([1, n])
            phi = np.zeros([1, n])
            gsim.compute(ctx, [IA()], mean, sigma, tau, phi)
            np.testing.assert_array_almost_equal(
                np.exp(mean).flatten(),
                data[f"{region}_MEAN"].to_numpy()
                )
            np.testing.assert_array_almost_equal(
                sigma.flatten(),
                data[f"{region}_SIG"].to_numpy()
                )
            np.testing.assert_array_almost_equal(
                tau.flatten(),
                data[f"{region}_TAU"].to_numpy()
                )
            np.testing.assert_array_almost_equal(
                phi.flatten(),
                data[f"{region}_PHI"].to_numpy()
                )
        return

    def test_macedo_2019_sinter_conditioned(self):
        """Tests execution of MacedoEtAl2019SInter conditioned on ground motion
        """
        data = pd.read_csv(self.sinter_table_file, sep=",")
        gsim_sinter = MacedoEtAl2019SInter
        self._compare_gsim_by_region(data, gsim_sinter)

    def test_macedo_2019_sslab_conditioned(self):
        """Tests execution of MacedoEtAl2019SSlab conditioned on ground motion
        """
        data = pd.read_csv(self.sslab_table_file, sep=",")
        gsim_sslab = MacedoEtAl2019SSlab
        self._compare_gsim_by_region(data, gsim_sslab)


class MacedoEtAl2019SInterTestCase(BaseGSIMTestCase):
    """Test case for the Macedo et al. (2019) GMM conditioned on GMVs generated
    by the AbrahamsonEtAl2019SInter GSIM
    """
    GSIM_CLASS = MacedoEtAl2019SInter
    MEAN_FILE = "macedo_2019/macedo_2019_sinter_mean.csv"
    TOTAL_FILE = "macedo_2019/macedo_2019_sinter_total_stddev.csv"
    INTER_FILE = "macedo_2019/macedo_2019_sinter_inter_event_stddev.csv"
    INTRA_FILE = "macedo_2019/macedo_2019_sinter_intra_event_stddev.csv"
    GMM_GMPE = {"AbrahamsonEtAl2015SInter": {}}

    def test_all(self):
        self.check(self.MEAN_FILE, self.TOTAL_FILE, self.INTER_FILE,
                   self.INTRA_FILE, max_discrep_percentage=0.01,
                   gmpe=self.GMM_GMPE)


class MacedoEtAl2019SSlabTestCase(MacedoEtAl2019SInterTestCase):
    """Test case for the Macedo et al. (2019) GMM conditioned on GMVs generated
    by the AbrahamsonEtAl2019SInter GSIM
    """
    GSIM_CLASS = MacedoEtAl2019SSlab
    MEAN_FILE = "macedo_2019/macedo_2019_sslab_mean.csv"
    TOTAL_FILE = "macedo_2019/macedo_2019_sslab_total_stddev.csv"
    INTER_FILE = "macedo_2019/macedo_2019_sslab_inter_event_stddev.csv"
    INTRA_FILE = "macedo_2019/macedo_2019_sslab_intra_event_stddev.csv"
    GMM_GMPE = {"AbrahamsonEtAl2015SSlab": {}}
