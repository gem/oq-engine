# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import mock
import unittest

from risklib import api
from risklib.models import input, output
from risklib import vulnerability_function


class ComputeOnSitesTestCase(unittest.TestCase):

    def test_multiple_sites(self):
        asset = input.Asset("a1", None, None, None)
        sites = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)
        assets_getter = mock.Mock(return_value=[asset])

        list(api.compute_on_sites(sites,
            assets_getter, hazard_getter, calculator))

        calls = [mock.call(asset, 1.0)] * 3
        calculator.assert_has_calls(calls)

        calls = [mock.call((1.0, 1.0)), mock.call((2.0, 2.0)),
            mock.call((3.0, 3.0))]

        assets_getter.assert_has_calls(calls)
        hazard_getter.assert_has_calls(calls)

    def test_multiple_assets_per_site(self):
        sites = [(1.0, 1.0)]

        assets = [
            input.Asset("a1", None, None, None),
            input.Asset("a2", None, None, None),
            input.Asset("a3", None, None, None),
        ]

        calculator = mock.Mock()
        assets_getter = mock.Mock(return_value=assets)
        hazard_getter = mock.Mock(return_value=1.0)

        list(api.compute_on_sites(sites,
            assets_getter, hazard_getter, calculator))

        calls = [mock.call(assets[0], 1.0), mock.call(assets[1], 1.0),
            mock.call(assets[2], 1.0)]

        calculator.assert_has_calls(calls)


class ComputeOnAssetsTestCase(unittest.TestCase):

    def test_compute_on_assets(self):
        assets = [
            input.Asset("a1", None, None, (1.0, 1.0)),
            input.Asset("a2", None, None, (2.0, 2.0)),
            input.Asset("a3", None, None, (3.0, 3.0)),
        ]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)

        list(api.compute_on_assets(assets, hazard_getter, calculator))

        calls = [mock.call((1.0, 1.0)), mock.call((2.0, 2.0)),
            mock.call((3.0, 3.0))]

        hazard_getter.assert_has_calls(calls)

        calls = [mock.call(assets[0], 1.0), mock.call(assets[1], 1.0),
                 mock.call(assets[2], 1.0)]

        calculator.assert_has_calls(calls)


class ConditionalLossesTestCase(unittest.TestCase):

    def test_conditional_losses(self):
        asset = input.Asset("a1", None, None, None)
        asset_output = output.ClassicalAssetOutput(
            asset, [(2.0, 2.0)], [(1.0, 1.0)])

        loss_curve_calculator = mock.Mock(return_value=asset_output)

        with mock.patch("risklib.classical._conditional_losses") as stub:
            stub.return_value = {0.1: 0.5, 0.2: 0.5}

            asset_output = api.conditional_losses(
                [0.1, 0.2], loss_curve_calculator)(asset, 1.0)

            loss_curve_calculator.assert_called_with(asset, 1.0)

            expected_output = output.ClassicalAssetOutput(
                asset, [(2.0, 2.0)], [(1.0, 1.0)], {0.1: 0.5, 0.2: 0.5})

            # as output we have the output from the given loss curve
            # calculator, plus the conditional losses
            self.assertEquals(expected_output, asset_output)


class ClassicalCalculatorTestCase(unittest.TestCase):

    def test_classical_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]
        asset = input.Asset("a1", "RC", 1.0, None)

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}
        asset_output = api.classical(vulnerability_model)(asset, hazard_curve)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.loss_curve)
        self.assertIsNotNone(asset_output.loss_ratio_curve)
