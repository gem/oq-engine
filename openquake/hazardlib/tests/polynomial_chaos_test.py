# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import copy
import unittest
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.polynomial_chaos import get_coeff, get_hermite
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008


class GetHermiteTest(unittest.TestCase):

    def test01(self):
        sg = 0.53
        computed = np.squeeze(get_hermite(np.array([sg])))
        # expected values computed by hand
        expected = [1, 0.53, -0.7191, -1.441123, 1.39350481, 6.50304955,
                    -3.52090779]
        np.testing.assert_almost_equal(computed, expected)

class GetCoeffTest(unittest.TestCase):

    def test01(self):
        m_mu = np.array([0.78])
        sigma = np.array([0.5])
        sigma_mu = np.array([0.2])
        imls = np.array([0.90])
        cff = np.squeeze(get_coeff(m_mu, sigma, sigma_mu, imls))

        computed = cff[0:6]
        expected = np.array([+3.835280479424e-02,
                             -1.170898587226e-02,
                             +1.501469721901e-03,
                             +3.997519121971e-05,
                             -3.594660885475e-05,
                             -2.045750986545e-04])
        np.testing.assert_almost_equal(computed, expected)


class ScenarioTest(unittest.TestCase):
    """
    """
    # Compute the probability of exceedance using as a standard deviation the
    # combination of aleatory and epistemic stds.
    # To perform the test we should compute the conditional probability for
    # various values of sigma and compare the mean and fractiles obtained with
    # the two methods

    def setUp(self):
        # Set ground-motion model and imls
        self.gsim = BooreAtkinson2008()
        self.imls = np.logspace(-2, 0, num=40)
        self.epistemic_std = 0.2  # same value used by L&A2019
        # Set rupture parameters and distances
        dists = DistancesContext()
        dists.rjb = np.array([10.])
        sites = Dummy.get_site_collection(len(dists.rjb), vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        imt = PGA()
        # Compute ground-motion
        self.mean_std_orig = self.gsim.get_mean_std(sites, rup, dists, [imt])
        # Compute the probability of exceedance
        self.poes_orig = self.gsim.get_poes(self.mean_std_orig, self.imls,
                                            truncation_level=None)
        # Compute the 'combined' std. `mean_std` has shape 2, number of sites,
        # number of intensity measure types
        mean_std = np.empty_like(self.mean_std_orig)
        mean_std[0, :] = self.mean_std_orig[0, :]
        mean_std[1, :] = (self.mean_std_orig[1, :]**2 +
                          (np.ones_like(mean_std[1, :]) *
                           self.epistemic_std)**2)**0.5
        self.mean_std = mean_std
        # Compute the probability of exceedance using the 'combined' standard
        # deviation - This is PC coeff 0
        self.poes_comb = self.gsim.get_poes(mean_std, self.imls,
                                            truncation_level=None)
        # Sample the epistemic epistemic uncertainty distribution
        num_realisations = 400
        np.random.seed(1)
        samples = np.random.normal(loc=0.0, scale=self.epistemic_std,
                                   size=num_realisations)
        # Prepare the array where to store the results and compute the
        # probability of exceedance for all the realisations
        realisations = np.empty((num_realisations, len(self.imls)))
        for i in range(num_realisations):
            tmp = copy.copy(self.mean_std_orig)
            tmp[0, :] += samples[i]
            realisations[i, :] = self.gsim.get_poes(tmp, self.imls,
                                                    truncation_level=None)
        self.realisations = realisations

    def test_mean(self):
        """
        Check that the mean of the conditional probability of exceedance i.e.
        C0 is equal to the mean hazard we obtain using the classical approach
        used to process epistemic uncertainty.
        """
        mean_epi = np.mean(self.realisations, axis=0)
        np.testing.assert_almost_equal(mean_epi, np.squeeze(self.poes_comb),
                                       decimal=2)
        # ---- REMOVE this
        if 0:
            import matplotlib.pyplot as plt
            _ = plt.figure()
            plt.plot(self.imls, mean_epi)
            plt.plot(self.imls, np.squeeze(self.poes_comb))
            plt.xscale('log')
            plt.xlabel('IMLs')
            plt.ylabel('PoEs')
            plt.show()

    def test_fractile(self):
        """
        Check that the calculation of fractiles using the PC expansion
        provides results consistent with the ones computed using the
        traditional approach.
        """
        # These are the results obtained using the classical approach
        mean_epi = np.mean(self.realisations, axis=0)
        std_epi = np.std(self.realisations, axis=0)
        # Empirical standard deviation
        sigma_mu = np.ones((self.mean_std.shape[1])) * self.epistemic_std
        # Compute the PC coefficients
        m_mu = self.mean_std[0, :, 0]
        pc_coef = get_coeff(m_mu, self.mean_std[1, :, 0], sigma_mu, self.imls)

        import matplotlib.pyplot as plt
        _ = plt.figure()
        for deg in range(0, 6):
            plt.plot(np.log(self.imls), pc_coef[deg-1, :])
        plt.show()

        # Compute samples of the Hermite polynomial
        num_samples = 50
        csi = np.random.normal(loc=0.0, scale=self.epistemic_std,
                               size=num_samples)
        xx = get_hermite(csi)

        _ = plt.figure()
        curves = np.zeros((num_samples, len(self.imls)))
        for rlz in range(0, num_samples):
            curves[rlz, :] = self.poes_comb
            for deg in range(1, 5):
                curves[rlz, :] += pc_coef[deg-1, :] * xx[deg, rlz]
            plt.plot(self.imls, curves[rlz, :], '--')
        plt.plot(self.imls, mean_epi)
        plt.plot(self.imls, np.squeeze(self.poes_comb), lw=3)
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('IMLs')
        plt.ylabel('PoEs')
        plt.show()
