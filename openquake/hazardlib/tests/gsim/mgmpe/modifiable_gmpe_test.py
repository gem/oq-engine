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
import unittest
import numpy as np
from openquake.hazardlib import valid
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import (
    ModifiableGMPE, _dict_to_coeffs_table)

aae = np.testing.assert_array_almost_equal
ORIG, MODI = 0, 1  # original vs modified GMPE


class ModifiableGMPETest(unittest.TestCase):

    def test_AlAtik2015Sigma(self):
        params1 = {"tau_model": "global", "ergodic": False}
        params2 = {"tau_model": "cena", "ergodic": True}
        params3 = {}
        gsims = [ModifiableGMPE(gmpe={'YenierAtkinson2015BSSA': {}},
                                sigma_model_alatik2015=params)
                 for params in [params1, params2, params3]]
        cmaker = simple_cmaker(gsims, ['PGA'])
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

    def test_AkkarEtAlRjb2014(self):
        # check mean and stds
        gsims = [ModifiableGMPE(gmpe={'AkkarEtAlRjb2014': {}},
                                set_between_epsilon={'epsilon_tau': 0.5}),
                 valid.gsim('AkkarEtAlRjb2014')]
        cmaker = simple_cmaker(gsims, ['PGA'])
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

    def get_mean_stds(self, **kw):
        gmpe_name = 'AkkarEtAlRjb2014'
        gmm1 = ModifiableGMPE(gmpe={gmpe_name: {}})
        gmm2 = ModifiableGMPE(gmpe={gmpe_name: {}}, **kw)
        cmaker = simple_cmaker([gmm1, gmm2], ['PGA', 'SA(0.2)'])
        ctx = cmaker.new_ctx(4)
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx. vs30 = 760.
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        return cmaker.get_mean_stds([ctx])  

    def test(self):

        # check the scaling of the median ground motion - IMT-independent
        mea, sig, tau, phi = self.get_mean_stds(
            set_scale_median_scalar={'scaling_factor': 1.2})
        aae(np.exp(mea[MODI]) / np.exp(mea[ORIG]), 1.2)

        # Check the scaling of the median ground motion - IMT-dependent
        mea, sig, tau, phi = self.get_mean_stds(
            set_scale_median_vector={
                'scaling_factor': {"PGA": 0.9, "SA(0.2)": 1.1}})
        for m, s in enumerate([0.9, 1.1]):
            aae(np.exp(mea[MODI, m]) / np.exp(mea[ORIG, m]), s)
        
        # Check the scaling of the total stddev - scalar
        mea, sig, tau, phi = self.get_mean_stds(
            set_scale_total_sigma_scalar={'scaling_factor': 1.2})
        aae(sig[MODI] / sig[ORIG], 1.2)
        
        # Check the scaling of the total stddev - vector
        mea, sig, tau, phi = self.get_mean_stds(
            set_scale_total_sigma_vector={
                'scaling_factor': {"PGA": 0.9, "SA(0.2)": 1.1}})
        for m, s in enumerate([0.9, 1.1]):
            aae(sig[MODI, m] / sig[ORIG, m], s)
        
        # Check the assignment of total sigma to a fixed value
        mea, sig, tau, phi = self.get_mean_stds(
            set_fixed_total_sigma={"total_sigma": {"PGA": 0.6,
                                                   "SA(0.2)": 0.75}})
        for m, s in enumerate([0.6, 0.75]):
            aae(sig[MODI, m], s)

        # Check adding/removing a delta std to the total std
        mea, sig, tau, phi = self.get_mean_stds(
            add_delta_std_to_total_std={"delta": -0.20})

        aae(sig[ORIG, 0], 0.712105)
        aae(sig[MODI, 0], 0.68344277)

        # Check set total std as between plus phi SS
        mea, sig, tau, phi = self.get_mean_stds(
            set_total_std_as_tau_plus_delta={"delta": 0.45})
        
        aae(phi[ORIG, 0], 0.6201)
        aae(sig[MODI, 0], 0.5701491121)


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
            cmaker = simple_cmaker([gmm, gmpe], ['MMI'])
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
            cmaker = simple_cmaker([gmm, gmpe], ['SA(0.3)'])
            ctx = self.get_ctx(cmaker)
            mea, sig, tau, phi = cmaker.get_mean_stds([ctx])
            exp_mean = mea[1] + np.array([-0.2, 0.4, 0.6, 0])
            exp_stdev = np.sqrt(np.array([0.3, 0.4, 0.5, 0.2])**2 +
                                np.array([0.2, 0.1, 0.3, 0.4])**2)

            # Check the computed mean + amplification
            aae(mea[0], exp_mean)

            # Check the computed intra-event stdev
            aae(phi[0], [exp_stdev])
