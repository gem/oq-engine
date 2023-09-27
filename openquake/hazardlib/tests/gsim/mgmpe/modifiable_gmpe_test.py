# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
import numpy as np
import unittest
from openquake.hazardlib import const, valid
from openquake.hazardlib.contexts import get_mean_stds
from openquake.hazardlib.imt import PGA, SA, MMI
from openquake.hazardlib.gsim.base import registry, CoeffsTable
from openquake.hazardlib.contexts import RuptureContext, test_cmaker
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import (
    ModifiableGMPE, _dict_to_coeffs_table)
from openquake.hazardlib.imt import from_string

aae = np.testing.assert_array_almost_equal


class ModifiableGMPEAlAtik2015SigmaTest(unittest.TestCase):

    def test1(self):
        params1 = {"tau_model": "global", "ergodic": False}
        params2 = {"tau_model": "cena", "ergodic": True}
        params3 = {}
        gsims = [ModifiableGMPE(gmpe={'YenierAtkinson2015BSSA': {}},
                                sigma_model_alatik2015=params)
                 for params in [params1, params2, params3]]
        cmaker = test_cmaker(gsims, ['PGA'])
        ctx = cmaker.new_ctx(4)
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        ctx.vs30 = 760.
        ctx.rrup = np.array([1., 10., 30., 70.])
        mea, sig, tau, phi = cmaker.get_mean_stds([ctx])  # (G,M,N)

        # Expected results hand computed
        aae(phi[0], 0.41623333)
        aae(phi[1], 0.67626858)
        aae(phi[2], 0.67626858)
        aae(tau[0], 0.36855)
        aae(tau[1], 0.32195)
        aae(tau[2], 0.36855)

        # now test with_betw_ratio
        cmaker.gsims[0] = ModifiableGMPE(
            gmpe={'Campbell2003': {}},
            add_between_within_stds={'with_betw_ratio': 0.6})
        mea, sig, tau, phi = cmaker.get_mean_stds([ctx])  # (G,M,N)
        aae(tau[0], 0.44075136)
        aae(phi[0], 0.26445082)

        # check error is raised for GMPEs with only total std
        with self.assertRaises(ValueError):
            ModifiableGMPE(gmpe={'Campbell2003': {}},
                           set_between_epsilon={'epsilon_tau': 0.5})

    def test2(self):
        # check mean and stds
        gsims = [ModifiableGMPE(gmpe={'AkkarEtAlRjb2014': {}},
                                set_between_epsilon={'epsilon_tau': 0.5}),
                 valid.gsim('AkkarEtAlRjb2014')]
        cmaker = test_cmaker(gsims, ['PGA'])
        ctx = cmaker.new_ctx(4)
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        ctx.vs30 = 760.
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        mea, sig, tau, phi = cmaker.get_mean_stds([ctx])  # (G,M,N)

        # check the computed mean + between event variability
        exp_mean = mea[1] + tau[1] * 0.5
        aae(exp_mean, mea[0])

        # check the total std corresponds to the within event stddev
        aae(sig[0], phi[1])

    def test_coefficients_as_dictionary(self):
        """Check the parsing of the coefficients to a dictionary"""
        input_coeffs = {"PGA": 1.0, "SA(0.2)": 2.0, "SA(3.0)": 3.0}
        output_coeffs = _dict_to_coeffs_table(input_coeffs, "XYZ")
        self.assertListEqual(list(output_coeffs), ["XYZ"])
        self.assertIsInstance(output_coeffs["XYZ"], CoeffsTable)
        self.assertAlmostEqual(output_coeffs["XYZ"][PGA()]["XYZ"], 1.0)
        self.assertAlmostEqual(output_coeffs["XYZ"][SA(0.2)]["XYZ"], 2.0)
        self.assertAlmostEqual(output_coeffs["XYZ"][SA(3.0)]["XYZ"], 3.0)


class ModifiableGMPETest(unittest.TestCase):

    def setUp(self):
        self.ctx = ctx = RuptureContext()
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        sites = Dummy.get_site_collection(4, vs30=760.)
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        self.imt = PGA()

    def test_scale_median_scalar(self):
        """Check the scaling of the median ground motion - scalar"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                             set_scale_median_scalar={'scaling_factor': 1.2})
        mean_unscaled = gmm_unscaled.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[0]
        mean = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[0]
        np.testing.assert_almost_equal(np.exp(mean) / np.exp(mean_unscaled),
                                       1.2 * np.ones(mean.shape))

    def test_scale_median_vector(self):
        """Check the scaling of the median ground motion - IMT-dependent"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_median_vector={'scaling_factor': {"PGA": 0.9,
                                                        "SA(0.2)": 1.1}})
        for imt, sfact in zip([PGA(), SA(0.2)], [0.9, 1.1]):
            mean_unscaled = gmm_unscaled.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[0]
            mean = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                            imt, stddevs)[0]
            np.testing.assert_almost_equal(
                np.exp(mean) / np.exp(mean_unscaled),
                sfact * np.ones(mean.shape))

    def test_scale_total_sigma_scalar(self):
        """Check the scaling of the total stddev - scalar"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_total_sigma_scalar={"scaling_factor": 1.2})
        [stddev_unscaled] = gmm_unscaled.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, self.imt, stddevs)[1]
        [stddev] = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                            self.imt, stddevs)[1]
        np.testing.assert_array_almost_equal(stddev / stddev_unscaled,
                                             1.2 * np.ones(stddev.shape))

    def test_scale_total_sigma_vector(self):
        """Check the scaling of the total stddev - vector"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm_unscaled = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_scale_total_sigma_vector={"scaling_factor": {"PGA": 0.9,
                                                             "SA(0.2)": 1.1}})

        for imt, sfact in zip([PGA(), SA(0.2)], [0.9, 1.1]):
            [stddev_unscaled] = gmm_unscaled.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            [stddev] = gmm.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            np.testing.assert_almost_equal(
                stddev / stddev_unscaled,
                sfact * np.ones(stddev.shape))

    def test_fixed_total_sigma(self):
        """Check the assignment of total sigma to a fixed value"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]
        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_fixed_total_sigma={"total_sigma": {"PGA": 0.6,
                                                   "SA(0.2)": 0.75}})

        for imt, sfact in zip([PGA(), SA(0.2)], [0.6, 0.75]):
            [stddev] = gmm.get_mean_and_stddevs(
                self.ctx, self.ctx, self.ctx, imt, stddevs)[1]
            np.testing.assert_almost_equal(stddev,
                                           sfact * np.ones(stddev.shape))

    def test_add_delta(self):
        """Check adding/removing a delta std to the total std"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]

        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            add_delta_std_to_total_std={"delta": -0.20})
        imt = PGA()
        [stddev] = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, imt, stddevs)[1]

        # Original total std for PGA is 0.7121
        np.testing.assert_almost_equal(stddev[0], 0.68344277, decimal=6)

    def test_set_total_std_as_tau_plus_phi(self):
        """Check set total std as between plus phi SS"""
        gmpe_name = 'AkkarEtAlRjb2014'
        stddevs = [const.StdDev.TOTAL]

        gmm = ModifiableGMPE(
            gmpe={gmpe_name: {}},
            set_total_std_as_tau_plus_delta={"delta": 0.45})
        imt = PGA()
        [stddev] = gmm.get_mean_and_stddevs(
            self.ctx, self.ctx, self.ctx, imt, stddevs)[1]

        # Original tau for PGA is 0.6201
        np.testing.assert_almost_equal(stddev[0], 0.5701491121, decimal=6)


class ModifiableGMPETestSwissAmpl(unittest.TestCase):
    """
    Tests the implementation of a correction factor for intensity
    """
    def get_ctx(self, cmaker):
        ctx = cmaker.new_ctx(4)
        ctx.mag = 6.0
        ctx.hypo_depth = 10.
        ctx.amplfactor = [-1.0, 1.5, 0.00, -1.99]
        ctx.ch_ampl03 = [-0.2, 0.4, 0.6, 0]
        ctx.ch_phis2s03 = [0.3, 0.4, 0.5, 0.2]
        ctx.ch_phiss03 = [0.2, 0.1, 0.3, 0.4]
        ctx.rhypo = ctx.rrup = ctx.repi = np.array([1., 10., 30., 70.])
        return ctx

    def test(self):
        for gmpe_name in ['ECOS2009', 'BindiEtAl2011RepiFixedH',
                          'BaumontEtAl2018High2210IAVGDC30n7',
                          'FaccioliCauzzi2006']:

            gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                                 apply_swiss_amplification={})
            gmpe = valid.gsim(gmpe_name)
            cmaker = test_cmaker([gmm, gmpe], ['MMI'])
            ctx = self.get_ctx(cmaker)
            mea, sig, tau, phi = cmaker.get_mean_stds([ctx])
            exp_mean = mea[1] + np.array([-1.00, 1.50, 0, -1.99])

            # Check the computed mean + amplification
            np.testing.assert_almost_equal(mea[0], exp_mean)

        for gmpe_name in ['EdwardsFah2013Alpine10Bars',
                          'EdwardsFah2013Foreland60Bars',
                          'ChiouYoungs2008SWISS01']:

            gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                                 apply_swiss_amplification_sa={})
            gmpe = valid.gsim(gmpe_name)
            cmaker = test_cmaker([gmm, gmpe], ['SA(0.3)'])
            ctx = self.get_ctx(cmaker)
            mea, sig, tau, phi = cmaker.get_mean_stds([ctx])
            exp_mean = mea[1] + np.array([-0.2, 0.4, 0.6, 0])
            exp_stdev = np.sqrt(np.array([0.3, 0.4, 0.5, 0.2])**2 +
                                np.array([0.2, 0.1, 0.3, 0.4])**2)

            # Check the computed mean + amplification
            aae(mea[0], exp_mean)

            # Check the computed intra-event stdev
            aae(phi[0], [exp_stdev])
