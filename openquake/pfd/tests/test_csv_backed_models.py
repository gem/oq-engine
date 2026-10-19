# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Tests that actually *use* the CSV-backed PFD coefficient tables.

Importing ``openquake.pfd.primary_surf_displ`` already reads every CSV at
import time (class attributes / module-level loaders), but before this
module no test validated the numbers. These pin a few P(D > d) values for
the three CSV-backed models.

The expected values are identical to oq-pfdha (the source-of-truth
implementation the tables were lifted from) at machine precision, so they
also serve as the in-engine regression anchor for the coefficient files.
"""
import unittest
import numpy as np
from openquake.pfd.primary_surf_displ.chiou2025 import Chiou2025PrimaryFD
from openquake.pfd.primary_surf_displ.moss2024 import Moss2024PrimaryFD
from openquake.pfd.primary_surf_displ.kuehn2024.kuehn2024 import (
    Kuehn2024PrimaryFD)

D = np.array([0.01, 0.1, 1.0])
XL = np.array([0.25])
MAG = 7.0


class CsvBackedModelsTestCase(unittest.TestCase):

    def test_chiou2025_coefficients(self):
        # data/chiou_2025_coefficients.csv (version model7)
        p = Chiou2025PrimaryFD().get_prob(
            D, X_L_ratio=XL, mag=MAG, style='strike-slip')
        np.testing.assert_allclose(
            p,
            [0.9974345471500569, 0.9637571025307536, 0.5371368054436663],
            rtol=1e-9, atol=0)

    def test_moss2024_d_ad_coefficients(self):
        # data/moss_2024_gamma_distribution_parameters_d_ad.csv
        p = Moss2024PrimaryFD().get_prob(
            D, X_L_ratio=XL, mag=MAG, version='AD')
        np.testing.assert_allclose(
            p,
            [0.999986991917209, 0.9911731959464328, 0.4577799837280986],
            rtol=1e-9, atol=0)

    def test_moss2024_d_md_coefficients(self):
        # data/moss_2024_gamma_distribution_parameters_d_md.csv
        p = Moss2024PrimaryFD().get_prob(
            D, X_L_ratio=XL, mag=MAG, version='MD')
        np.testing.assert_allclose(
            p,
            [0.9995048278453876, 0.9322719176398719, 0.24859743674732115],
            rtol=1e-9, atol=0)

    def test_kuehn2024_mean_coefficients(self):
        # kuehn2024/data/coefficients_mean_{NM,REV,SS}_powtr.csv
        p = Kuehn2024PrimaryFD().get_prob(
            D, X_L_ratio=XL, mag=MAG, style='normal',
            epistemic_uncertainty=False)
        np.testing.assert_allclose(
            p,
            [0.9998951858571609, 0.9801701472093585, 0.5317015464181556],
            rtol=1e-9, atol=0)

    def test_kuehn2024_posterior_coefficients(self):
        # kuehn2024/data/coefficients_posterior_{NM,REV,SS}_powtr.csv
        post = Kuehn2024PrimaryFD().get_prob(
            D, X_L_ratio=XL, mag=MAG, style='normal')
        self.assertEqual(post.shape, (1000, 3))
        np.testing.assert_allclose(
            post[0],
            [0.9999696094078301, 0.9863733497096807, 0.5589756738012217],
            rtol=1e-9, atol=0)
        np.testing.assert_allclose(
            post.mean(axis=0),
            [0.9995337823127354, 0.9747356896798124, 0.5257267660038744],
            rtol=1e-9, atol=0)


if __name__ == '__main__':
    unittest.main()
