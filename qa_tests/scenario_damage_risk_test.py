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

import unittest, numpy
from risklib import api
from risklib.models import input

def assert_close(expected, actual):
    return numpy.testing.assert_allclose(
        expected, actual, atol=0.0, rtol=1E-7)

class ScenarioDamageRiskTestCase(unittest.TestCase):

    hazard = dict(
        a1 = [0.17111044666642075, 0.3091294488722627, 0.15769192850594427,
              0.33418745728229904, 0.1744414801203893, 0.29182607890936946,
              0.16115560432050713, 0.2822499831821711, 0.22753947129871863,
              0.2900247583738464],
        a3 = [0.3051275714154333, 0.2670311789324559, 0.15943380711124205,
              0.2361640051201896, 0.2885030735639452, 0.244808088235014,
              0.16157066112741528, 0.2395727775322746, 0.4791639979180004,
              0.38630241325610637],
        a2 = [0.6040315550126056, 0.33487798185272694, 0.39260185463612385, 
              0.367634839907372, 0.34461255379999045, 0.28035744548676755,
              0.44360919761302703, 0.2418451146800914, 0.5069824581167889, 
              0.45975761535464116],
        )
    
    def assert_ok(self, asset_output, expected_means, expected_stdevs):
        # a scenario_damage calculator returns:
        # 1. the damage_distribution, i.e. (means, stdevs) for all damage states
        # 2. the collapse_map, i.e. (mean, stdev) of the highest damage state
        assert_close(asset_output.damage_distribution_asset,
                     (expected_means, expected_stdevs))
        assert_close(asset_output.collapse_map,
                     (expected_means[-1], expected_stdevs[-1]))

    def test_continuous_ff(self):
        fragility_model = input.FragilityModel(
            "continuous", None, ["LS1", "LS2"])

        fragility_functions = dict(
            RC = [
                input.FragilityFunctionContinuous(
                    fragility_model, 0.2, 0.05, 'LS1'),
                input.FragilityFunctionContinuous(
                    fragility_model, 0.35, 0.10, 'LS2')
                ],
            RM = [
                input.FragilityFunctionContinuous(
                    fragility_model, 0.25, 0.08, 'LS1'),
                input.FragilityFunctionContinuous(
                    fragility_model, 0.40, 0.12, 'LS2'),
                ])

        calculator = api.scenario_damage(fragility_model, fragility_functions)
 
        asset_output = calculator(
            input.Asset("a1", "RM", 3000, None, number_of_units=3000), 
            self.hazard['a1'])
        expected_means = [1562.6067550208, 1108.0189275488, 329.3743174305]
        expected_stdevs = [968.93502576, 652.7358505746, 347.3929450270]
        self.assert_ok(asset_output, expected_means, expected_stdevs)

        asset_output = calculator(
            input.Asset("a3", "RM", 1000, None, number_of_units=1000), 
            self.hazard['a3'])
        expected_means = [417.3296948271, 387.2084383654, 195.4618668074]
        expected_stdevs = [304.4769498434, 181.1415598664, 253.91309010185]
        self.assert_ok(asset_output, expected_means, expected_stdevs)
       
        asset_output = calculator(
            input.Asset("a2", "RC", 2000, None, number_of_units=2000), 
            self.hazard['a2'])
        expected_means = [56.7201291212, 673.1047565606, 1270.1751143182]
        expected_stdevs = [117.7802813522, 485.2023172324, 575.8724057319]
        self.assert_ok(asset_output, expected_means, expected_stdevs)

        # TODO: check the aggregations

    def test_discrete_ff(self):
        fragility_model = input.FragilityModel(
            "discrete", [0.1, 0.2, 0.3, 0.5], ["LS1", "LS2"])

        fragility_functions = dict(
            RC = [
                input.FragilityFunctionDiscrete(
                    fragility_model, [0.0073, 0.35, 0.74, 0.99], 'LS1'),
                input.FragilityFunctionDiscrete(
                    fragility_model, [0.001, 0.02, 0.25, 0.72], 'LS2')
                ],
            RM = [
                input.FragilityFunctionDiscrete(
                    fragility_model, [0.01, 0.64, 0.95, 1.0], 'LS1'),
                input.FragilityFunctionDiscrete(
                    fragility_model, [0.0003, 0.05, 0.40, 0.86], 'LS2'),
                ])

        calculator = api.scenario_damage(fragility_model, fragility_functions)
 
        asset_output = calculator(
            input.Asset("a1", "RM", 3000, None, number_of_units=3000), 
            self.hazard['a1'])
        expected_means = [875.81078203, 1448.29628694, 675.89293103]
        expected_stdevs = [757.54019289, 256.15319254, 556.76593931]
        self.assert_ok(asset_output, expected_means, expected_stdevs)

        asset_output = calculator(
            input.Asset("a3", "RM", 1000, None, number_of_units=1000), 
            self.hazard['a3'])
        expected_means = [224.4178072, 465.64396155, 309.93823125]
        expected_stdevs = [220.65161409, 136.92817619, 246.84424913]
        self.assert_ok(asset_output, expected_means, expected_stdevs)

        asset_output = calculator(
            input.Asset("a2", "RC", 2000, None, number_of_units=2000), 
            self.hazard['a2'])
        expected_means = [344.90849228, 747.62412976, 907.46737796]
        expected_stdevs = [300.61123079, 144.64852962, 417.30737837]
        self.assert_ok(asset_output, expected_means, expected_stdevs)

        # TODO: check the aggregations
