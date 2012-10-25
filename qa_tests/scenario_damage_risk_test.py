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

import unittest
from risklib import api
from risklib.models import input

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
    
    def test_discrete(self):
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
 
        out = calculator(
            input.Asset("a1", "RM", 3000, None, number_of_units=3000), 
            self.hazard['a1'])
        mean = [875.81078203, 1448.29628694, 675.89293103]
        stdev = [757.54019289, 256.15319254, 556.76593931]
        cmap = (675.89293102729573, 556.76593931180378)
        almost_equal(out.damage_distribution_asset, (mean, stdev))
        almost_equal(out.collapse_map, cmap)

        out = calculator(
            input.Asset("a3", "RM", 1000, None, number_of_units=1000), 
            self.hazard['a3'])
        mean = [224.4178072, 465.64396155, 309.93823125]
        stdev = [220.65161409, 136.92817619, 246.84424913]
        cmap = (309.93823125141324, 246.84424912551529)
        almost_equal(out.damage_distribution_asset, (mean, stdev))
        almost_equal(out.collapse_map, cmap)

        out = calculator(
            input.Asset("a2", "RC", 2000, None, number_of_units=2000), 
            self.hazard['a2'])
        mean = [344.90849228, 747.62412976, 907.46737796]
        stdev = [300.61123079, 144.64852962, 417.30737837]
        cmap = (907.46737796377931, 417.30737836563844)
        almost_equal(out.damage_distribution_asset, (mean, stdev))
        almost_equal(out.collapse_map, cmap)

        # TODO: check the aggregations








#################### the following must be put somewhere else ###############

def almost_equal(a, b, precision=1E-7):
    assert equal(a, b, precision), '%s != %s' % (str(a), str(b))

def equal(f1, f2, precision, strip=None):
    """
    An utility to check if two numbers (or nested sequences of numbers)
    are equal within a given precision. Here are few examples of usage:

  >>> equal(1, 1, .001) # these numbers are exactly equal, so no problem
  True

  >>> equal(1, 1.1, .001) # these numbers are equal within 0.1% of precision
  False

  >>> equal(1, 1.0011, .001) # these numbers are NOT at 0.1% of precision
  False

  >>> equal(range(3), range(3), .1) # these sequences are exactly equals
  True

  >>> equal([0, 1, 2], [0, 1, 1.9], .01) # these sequences are not equals
  False

  Notice that 'equal' has a .last_args attributes that stores the last
  arguments passed to it; in this case

  >>> equal.last_args #doctest: +ELLIPSIS
  (2, 1.899999999..., 0.01)

  >>> equal([1, [2,3]], [1, [2, 3]], .01)
  True

  If the sequences are not homogenous, you get a ValueError:

  >>> equal([1, [2,3]], [1, [2]], .01)
  Traceback (most recent call last):
    ...
  ValueError: Sequences of different length
    """
    equal.last_args = f1, f2, precision
    if hasattr(f1, '__iter__'):
        if len(f1) != len(f2):
            raise ValueError('Sequences of different length')
        return all(equal(e1, e2, precision, strip) for (e1, e2) in zip(f1, f2))
    elif not isinstance(f1, float):
        if strip and isinstance(f1, basestring) and isinstance(f2, basestring):
            return f1.strip(strip) == f2.strip(strip)
        return f1 == f2
    elif f1 == f2 or abs(f1 - f2)/abs(f1 + f2) * 2 < precision \
            or abs(f1 - f2) < 1e-12:
        return True
    else:
        return False

