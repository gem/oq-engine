# Copyright (c) 2010-2013, GEM Foundation.
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
import pickle
import numpy
from openquake.risklib import scientific


class ScenarioDamageFunctionsTestCase(unittest.TestCase):

    def test_dda_iml_above_range(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is higher than the highest
        # intensity measure level defined in the model (in this
        # particular case 0.7). Given this condition, to compute
        # the fractions of buildings we use the highest intensity
        # measure level defined in the model (0.7 in this case)

        ffns = [scientific.FragilityFunctionDiscrete(
            [0.1, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00])] * 2

        self._close_to(scientific.damage_state_fractions(ffns, 0.7),
                       scientific.damage_state_fractions(ffns, 0.8))

    def test_dda_iml_below_range_damage_limit_defined(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) and lower than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 100% no_damage and 0% for the
        # remaining limit states defined in the model.

        ffns = [scientific.FragilityFunctionDiscrete(
            [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00], 0.5)] * 2
        self._close_to([1.0, 0.0, 0.0],
                       scientific.damage_state_fractions(ffns, 0.02))

    def test_gmv_between_no_damage_limit_and_first_iml(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) but bigger than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 97.5% no_damage and 2.5% for the
        # remaining limit states defined in the model.

        ffs = [
            scientific.FragilityFunctionDiscrete(
                [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00], 0.05),
            scientific.FragilityFunctionDiscrete(
                [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.00, 0.05, 0.20, 0.50], 0.05)]

        self._close_to([0.975, 0.025, 0.],
                       scientific.damage_state_fractions(ffs, 0.075))

    def _close_to(self, expected, actual):
        numpy.testing.assert_allclose(actual, expected, atol=0.0, rtol=0.05)

    def test_can_pickle(self):
        ffd = scientific.FragilityFunctionDiscrete(
            [0, .1, .2, .3], [0.05, 0.20, 0.50, 1.00])
        self.assertEqual(pickle.loads(pickle.dumps(ffd)), ffd)
