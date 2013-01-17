# coding=utf-8
# Copyright (c) 2010-2013, GEM Foundation.
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
from scipy.stats import lognorm
from scipy.interpolate import interp1d
import math


NO_DAMAGE_STATE = "no_damage"


# TODO: validation on input values?
class FragilityFunctionContinuous(object):

    def __init__(self, fragility_model, mean, stddev, lsi):
        self.lsi = lsi
        self.mean = mean
        self.stddev = stddev
        self.fragility_model = fragility_model

    def poe(self, iml):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Level (IML).
        """
        variance = self.stddev ** 2.0
        sigma = math.sqrt(math.log(
            (variance / self.mean ** 2.0) + 1.0))

        mu = self.mean ** 2.0 / math.sqrt(
            variance + self.mean ** 2.0)

        return lognorm.cdf(iml, sigma, scale=mu)


class FragilityFunctionDiscrete(object):

    def __init__(self, fragility_model, poes, lsi):
        self.lsi = lsi
        self.poes = poes
        self.fragility_model = fragility_model

    def poe(self, iml):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Level (IML).
        """
        fm = self.fragility_model

        highest_iml = fm.imls[-1]
        no_damage_limit = fm.no_damage_limit

        # when the intensity measure level is above
        # the range, we use the highest one
        if iml > highest_iml:
            iml = highest_iml

        imls = [no_damage_limit] + fm.imls
        poes = [0.0] + self.poes

        return interp1d(imls, poes)(iml)


class FragilityModel(object):
    """
    A Fragility Model object with a list attribute `lss` containing
    the limit states.
    For N limit states in the fragility model, we always define N+1
    damage states. The first damage state is always '_no_damage'.
    """

    def __init__(self, format, imls, limit_states, no_damage_limit=None):
        self.imls = imls
        self.format = format
        self.lss = list(limit_states)
        self.damage_states = [NO_DAMAGE_STATE] + self.lss
        self.no_damage_limit = no_damage_limit

    def no_damage(self, gmv):
        """
        There is no damage when ground motions values are less
        than the first iml or when the no damage limit value
        is greater than the ground motions value.
        """
        discrete = self.format == "discrete"
        no_damage_limit = self.no_damage_limit is not None

        return ((discrete and not no_damage_limit and
                 gmv < self.imls[0]) or
                (discrete and no_damage_limit and
                 gmv < self.no_damage_limit))
