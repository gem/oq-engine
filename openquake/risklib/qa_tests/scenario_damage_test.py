# coding=utf-8
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import unittest
import numpy
from openquake.risklib import scientific, workflows


# FIXME(lp) remove this. it is just using the default args
def assert_close(expected, actual):
    return numpy.testing.assert_allclose(
        expected, actual, atol=0.0, rtol=1E-7)


class ScenarioDamageRiskTestCase(unittest.TestCase):

    hazard = dict(
        a1=[0.17111044666642075, 0.3091294488722627, 0.15769192850594427,
            0.33418745728229904, 0.1744414801203893, 0.29182607890936946,
            0.16115560432050713, 0.2822499831821711, 0.22753947129871863,
            0.2900247583738464],
        a3=[0.3051275714154333, 0.2670311789324559, 0.15943380711124205,
            0.2361640051201896, 0.2885030735639452, 0.244808088235014,
            0.16157066112741528, 0.2395727775322746, 0.4791639979180004,
            0.38630241325610637],
        a2=[0.6040315550126056, 0.33487798185272694, 0.39260185463612385,
            0.367634839907372, 0.34461255379999045, 0.28035744548676755,
            0.44360919761302703, 0.2418451146800914, 0.5069824581167889,
            0.45975761535464116],
    )

    def assert_ok(self, fractions, expected_means, expected_stdevs):
        # a scenario_damage calculator returns:
        # 1.the damage_distribution, i.e. (means, stdevs) for all damage states
        # 2.the collapse_map, i.e. (mean, stdev) of the highest damage state
        assert_close(scientific.mean_std(fractions),
                     (expected_means, expected_stdevs))

    def test_continuous_ff(self):
        fragility_model = {
            'RC': [scientific.FragilityFunctionContinuous('LS1', 0.2, 0.05),
                   scientific.FragilityFunctionContinuous('LS2', 0.35, 0.10)],
            'RM': [scientific.FragilityFunctionContinuous('LS1', 0.25, 0.08),
                   scientific.FragilityFunctionContinuous('LS2', 0.40, 0.12)]}

        calculator_rm = workflows.Damage(
            'PGA', 'RM', dict(damage=fragility_model['RM']))

        calculator_rc = workflows.Damage(
            'PGA', 'RC', dict(damage=fragility_model['RC']))

        [a1], [asset_output_a1] = calculator_rm(
            'damage', ['a1'], [self.hazard['a1']])

        expected_means = [1562.6067550208, 1108.0189275488, 329.3743174305]
        expected_stdevs = [968.93502576, 652.7358505746, 347.3929450270]
        self.assert_ok(asset_output_a1 * 3000, expected_means, expected_stdevs)

        [a3], [asset_output_a3] = calculator_rm(
            'damage', ['a3'], [self.hazard['a3']])
        expected_means = [417.3296948271, 387.2084383654, 195.4618668074]
        expected_stdevs = [304.4769498434, 181.1415598664, 253.91309010185]
        self.assert_ok(asset_output_a3 * 1000, expected_means, expected_stdevs)

        rm = asset_output_a1 * 3000 + asset_output_a3 * 1000

        [a2], [asset_output_a2] = calculator_rc(
            'damage', ['a2'], [self.hazard['a2']])

        expected_means = [56.7201291212, 673.1047565606, 1270.1751143182]
        expected_stdevs = [117.7802813522, 485.2023172324, 575.8724057319]
        self.assert_ok(asset_output_a2 * 2000, expected_means, expected_stdevs)

        rc = asset_output_a2 * 2000

        assert_close(
            rm.mean(0), [1979.9364498479, 1495.2273659142, 524.8361842379])
        assert_close(
            rm.std(0, ddof=1),
            [1103.6005152909, 745.3252495731, 401.9195159565])
        assert_close(
            rc.mean(0), [56.7201291212, 673.1047565606, 1270.1751143182])
        assert_close(
            rc.std(0, ddof=1),
            [117.7802813522, 485.2023172324, 575.8724057319])

    def test_discrete_ff(self):
        fragility_model = {
            'RC': [
                scientific.FragilityFunctionDiscrete(
                    'LS1', [0.1, 0.2, 0.3, 0.5], [0.0073, 0.35, 0.74, 0.99]),
                scientific.FragilityFunctionDiscrete(
                    'LS2', [0.1, 0.2, 0.3, 0.5], [0.001, 0.02, 0.25, 0.72])],
            'RM': [
                scientific.FragilityFunctionDiscrete(
                    'LS1', [0.1, 0.2, 0.3, 0.5], [0.01, 0.64, 0.95, 1.0]),
                scientific.FragilityFunctionDiscrete(
                    'LS2', [0.1, 0.2, 0.3, 0.5], [0.0003, 0.05, 0.40, 0.86])]}

        calculator_rm = workflows.Damage(
            'PGA', 'RM', dict(damage=fragility_model['RM']))

        [a1], [asset_output_a1] = calculator_rm(
            'damage', ['a1'], [self.hazard['a1']])

        expected_means = [875.81078203, 1448.29628694, 675.89293103]
        expected_stdevs = [757.54019289, 256.15319254, 556.76593931]
        self.assert_ok(asset_output_a1 * 3000, expected_means, expected_stdevs)

        [a3], [asset_output_a3] = calculator_rm(
            'damage', ['a3'], [self.hazard['a3']])

        expected_means = [224.4178072, 465.64396155, 309.93823125]
        expected_stdevs = [220.65161409, 136.92817619, 246.84424913]
        self.assert_ok(asset_output_a3 * 1000, expected_means, expected_stdevs)

        rm = asset_output_a1 * 3000 + asset_output_a3 * 1000

        calculator_rc = workflows.Damage(
            'PGA', 'RC', dict(damage=fragility_model['RC']))
        [a2], [asset_output_a2] = calculator_rc(
            'damage', ['a2'], [self.hazard['a2']])

        expected_means = [344.90849228, 747.62412976, 907.46737796]
        expected_stdevs = [300.61123079, 144.64852962, 417.30737837]
        self.assert_ok(asset_output_a2 * 2000, expected_means, expected_stdevs)

        rc = asset_output_a2 * 2000

        assert_close(
            rm.mean(0), [1100.2285892246, 1913.9402484967, 985.8311622787])
        assert_close(
            rm.std(0, ddof=1),
            [880.2774984768, 296.2197411105, 616.5632580754])
        assert_close(
            rc.mean(0), [344.9084922789, 747.6241297573, 907.4673779638])
        assert_close(
            rc.std(0, ddof=1),
            [300.6112307894, 144.6485296163, 417.307378365])
