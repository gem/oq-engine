# The Hazard Library
# Copyright (C) 2020 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np

from openquake.hazardlib.gsim.bayless_abrahamson_2018 import \
        BaylessAbrahamson2018
from openquake.hazardlib.imt import EAS
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BaylessAbrahamson2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BaylessAbrahamson2018

    # Tables computed using the matlab script included in the supplement to
    # the BSSA paper

    fname_mean = 'BA18/BA18_mean_reduced.csv'
    fname_std_tot = 'BA18/BA18_STD_TOTAL_reduced.csv'

    def test_mean(self):
        self.check(self.fname_mean, max_discrep_percentage=0.8)

    def test_mean_lowess(self):
        # Independent Python translation of the MATLAB script including
        # smooth2(fNL_mod0, 20, 'lowess') on the native grid
        self.check('BA18/BA18_LOWESS_MEAN.csv', max_discrep_percentage=0.1)

    def test_lowess_coefficient_cache(self):
        # Cached off-grid coefficients must not change the smoothing grid
        gsim = self.GSIM_CLASS()
        # Make ctx
        ctx = np.rec.fromrecords(
            [(6., 10., 180., 1., 0., 500.),  # Soil
             (6., 10., 760., 1., 0., 500.)], # Rock
            names='mag, rrup, vs30, ztor, rake, z1pt0')
        imts = [EAS(2.238721), EAS(100.)]  # Native grid freqs
        # Store predictions before adding interpolated coefficients
        expected = np.zeros((4, len(imts), len(ctx)))
        gsim.compute(ctx, imts, *expected)
        # Request off-grid frequencies to populate the coefficient cache
        for frequency in np.geomspace(0.5, 10., 31):
            gsim.COEFFS[EAS(frequency)]
        # Recompute and check that the predictions are still unchanged
        actual = np.zeros_like(expected)
        gsim.compute(ctx, imts, *actual)
        np.testing.assert_array_equal(actual, expected)

    def test_std_total(self):
        self.check(self.fname_std_tot, max_discrep_percentage=0.1)

    def test_off_grid_interpolation(self):
        # The MATLAB script interpolates log EAS and sigma using log(f)
        gsim = self.GSIM_CLASS()
        ctx = np.rec.fromrecords(
            [(5., 10., 180., 1., 0., 500.),  # Soil
             (5., 10., 760., 1., 0., 500.)], # Bedrock
            names='mag, rrup, vs30, ztor, rake, z1pt0')

        # Frequency pairs
        pairs = [(0.1, 0.102329),       # Low-freq scaling
                 (2.187761, 2.238721),  # Non-linear site response
                 (23.988321, 24.54708), # Start of kappa extrapolation
                 (97.723724, 100.)]     # Upper end of the freq range

        # Compute mean/sig at the lower and upper frequencies
        native_imts = [EAS(f) for pair in pairs for f in pair]
        native = np.zeros((4, len(native_imts), len(ctx)))
        gsim.compute(ctx, native_imts, *native)

        # sqrt(low * high) lies halfway between the endpoints in log(f)
        imts = [EAS(np.sqrt(low * high)) for low, high in pairs]
        actual = np.zeros((4, len(imts), len(ctx)))
        gsim.compute(ctx, imts, *actual) #  Predictions at these off-grid freqs

        # At each midpoint, every output must equal its endpoint average
        expected = (native[:, ::2] + native[:, 1::2]) / 2 # The slices select
        np.testing.assert_allclose(                       # alternating lower
            actual, expected, rtol=1e-12, atol=1e-14)     # and upper endpoint 
                                                          # values
             
        
