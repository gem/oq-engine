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

import math
from scipy.stats import lognorm
from scipy.interpolate import interp1d

# TODO: add validation on input values
# TODO: add immutability
class FragilityFunctionContinuous(object):

    def __init__(self, fragility_model, mean, stddev):
        self.mean = mean
        self.stddev = stddev
        self.fragility_model = fragility_model

    def poe(self, iml):
        """
        Compute the Probability of Exceedance for the given
        Intensity Measure Level using continuous functions.
        """

        variance = self.stddev ** 2.0
        sigma = math.sqrt(math.log((variance / self.mean ** 2.0) + 1.0))
        mu = math.exp(math.log(self.mean ** 2.0 / math.sqrt(
            variance + self.mean ** 2.0)))

        return lognorm.cdf(iml, sigma, scale=mu)


class FragilityFunctionDiscrete(object):

    def __init__(self, fragility_model, poes):
        self.poes = poes
        self.fragility_model = fragility_model

    def poe(self, iml):
        """
        Compute the Probability of Exceedance for the given
        Intensity Measure Level using discrete functions.
        """

        highest_iml = self.fragility_model.imls[-1]
        no_damage_limit = self.fragility_model.no_damage_limit

        # when the intensity measure level is above
        # the range, we use the highest one
        if iml > highest_iml:
            iml = highest_iml

        imls = [no_damage_limit] + self.fragility_model.imls
        poes = [0.0] + self.poes

        return interp1d(imls, poes)(iml)


class FragilityModel(object):

    def __init__(self, format, imls, no_damage_limit=None):
        self.imls = imls
        self.format = format
        self.no_damage_limit = no_damage_limit

    def no_damage(self, gmv):
        """
        There is no damage when ground motions values are less
        than the first iml or when the no damage limit value
        is greater than the ground motions value.
        """
        discrete = self.format == "discrete"
        no_damage_limit = self.no_damage_limit is not None

        return ((discrete and not no_damage_limit and gmv < self.imls[0]) or
                (discrete and no_damage_limit and gmv < self.no_damage_limit))
