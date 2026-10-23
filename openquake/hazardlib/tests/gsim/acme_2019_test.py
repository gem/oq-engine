# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
import os
import numpy as np
import unittest

from openquake.hazardlib import contexts
from openquake.hazardlib.imt import SA
from openquake.hazardlib.gsim.acme_2019 import AlAtikSigmaModel
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014ACME2019
from openquake.hazardlib.gsim.yenier_atkinson_2015 import get_sof_adjustment


DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ACME19')


class ACMEAlAtikSigmaModelWrapperTest(unittest.TestCase):

    def setUp(self):
        self.ctx = ctx = contexts.RuptureContext()
        ctx.rup_id = 0
        ctx.mag = 6.0
        ctx.vs30 = np.array([760.] * 4)
        ctx.rjb = ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.hypo_depth = np.array([10., 10., 30., 70.])
        ctx.rake = np.array([30.] * 4)
        ctx.dip = np.full(4, 45.)
        ctx.ztor = np.zeros(4)
        ctx.rx = np.zeros(4)
        ctx.z1pt0 = np.full(4, -999.)
        ctx.vs30measured = np.ones(4, dtype=bool)
        ctx.sids = np.arange(4)

    def test01(self):
        # Test expected results when adjusting Bindi 2014 GMM
        # with Al Atik sigma model and kappa adjustment file
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        ctx = self.ctx
        # Expected log means are Bindi's SA(0.1 s) log means plus ln(kappa).
        # The kappa factor at 0.1 s is 1.215197171648, interpolated from
        # the fixture's 'high' column using log period.
        expected_with_kappa_adj = [
            [-0.369481005046, -1.142677878809,
             -2.359719061696, -3.526413297299],
            [0.553060006037] * 4,
            [0.368550000000] * 4,
            [0.412366666667] * 4]
        # At M6 the corner period is 3.031354 s. SA(2.5) therefore uses
        # extrapolation from Bindi's selected 1.0-2.0 s periods.
        # No kappa adjustment because test data does not cover T = 2.5 s.
        expected_with_extrapolation = [
            [-3.435802721714, -4.142526649199,
             -5.006783386772, -5.723403517172],
            [0.536626597365] * 4,
            [0.368550000000] * 4,
            [0.390050000000] * 4]
        cases = [
            (0.1, {'kappa_file': filename, 'kappa_val': 'high'},
             expected_with_kappa_adj),
            (2.5, {}, expected_with_extrapolation)]
        for period, kwargs, expected in cases:
            with self.subTest(period=period):
                gmm = AlAtikSigmaModel(
                    gmpe_name='BindiEtAl2014Rjb', **kwargs)
                result = contexts.get_mean_stds(gmm, ctx, [SA(period)])
                np.testing.assert_allclose(result[:, 0, :], expected,
                                           rtol=0, atol=1e-7)

    def test02(self):
        # Checks if YA15 ACME subclass is always being evaluated at vs30=760
        # see HID 2.6.2
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='YenierAtkinson2015ACME2019',
                               kappa_file=filename,
                               kappa_val='high')
        ctx = self.ctx
        imt = SA(0.1)
        mean_760 = contexts.get_mean_stds(gmm, ctx, [imt])[0]

        ctx.vs30 = np.array([1500.] * 4)
        mean_1500 = contexts.get_mean_stds(gmm, ctx, [imt])[0]
        # So results will be identifical
        np.testing.assert_allclose(mean_760, mean_1500)

    def test03(self):
        # CY14 ACME mean with hanging wall and centered Ztor/Dpp excluded.
        # Expected means use scalar reference-motion and site equations.
        gmm = ChiouYoungs2014ACME2019()
        ctx = self.ctx
        result = contexts.get_mean_stds(
            gmm, ctx, [SA(0.1), SA(1.0)], truncation_level=0)[0]
        # Rows are log means at SA(0.1) and SA(1.0).
        expected = np.array([
            [0.169588368191, -0.848556808315,
             -2.120231937083, -3.342581946335],
            [-1.120368533583, -2.261628158863,
             -3.515484106424, -4.493888647502]])
        np.testing.assert_allclose(result, expected, rtol=0, atol=1e-7)


class GetSoFTestCase(unittest.TestCase):
    MSG = 'Wrong style-of-faulting coefficient'

    def test_short_period(self):
        # Normal
        rake = -90
        period = 0.01
        expected = 0.8401
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 1.0612
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 0.8843
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)

    def test_long_period(self):
        # Normal
        rake = -90
        period = 2.0
        expected = 0.9775
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 0.9882
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 1.0289
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
