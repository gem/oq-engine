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
import numpy
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
        self._interp = None

    @property
    def interp(self):
        if self._interp is not None:
            return self._interp
        fm = self.fragility_model
        imls = [fm.no_damage_limit] + fm.imls
        poes = [0.0] + self.poes
        self._interp = interp1d(imls, poes)
        return self._interp

    def poe(self, iml):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Level (IML).
        """
        highest_iml = self.fragility_model.imls[-1]
        # when the intensity measure level is above
        # the range, we use the highest one
        return self.interp(highest_iml if iml > highest_iml else iml)

    # so that the curve is pickeable
    def __getstate__(self):
        return dict(lsi=self.lsi, poes=self.poes,
                    fragility_model=self.fragility_model, _interp=None)

    def __eq__(self, other):
        return (self.lsi == other.lsi and self.poes == other.poes
                and self.fragility_model == other.fragility_model)

    def __ne__(self, other):
        return not self == other


class FragilityModel(object):
    """
    A Fragility Model object with a list attribute `damage_states`.
    For N limit states in the fragility model, we always define N+1
    damage states. The first damage state is always '_no_damage'.
    """

    def __init__(self, format, imls, limit_states, no_damage_limit=None):
        self.imls = imls
        self.format = format
        self.damage_states = [NO_DAMAGE_STATE] + list(limit_states)
        self.no_damage_limit = no_damage_limit

    def ground_motion_value_fractions(self, funcs, gmv):
        """
        Compute the fractions of each damage state for
        the Ground Motion Value given (a Ground Motion Value
        defines the Intensity Measure Level (IML) used to
        interpolate the Fragility Function.

        :param self
          The fragility model
        :param gmv: ground motion value.
        :type gmv: float
        :param funcs: list of fragility functions describing
            the distribution for each limit state. The functions
            must be in order from the one with the lowest
            limit state to the one with the highest limit state.
        :type funcs: list of
            :py:class:`FragilityFunction` instances
        :returns: the fraction of buildings of each damage state
            computed for the given ground motion value.
        :rtype: 1d `numpy.array`. Each value represents
            the fraction of a damage state (in order from the lowest
            to the highest)
        """
        damage_state_values = numpy.zeros(len(self.damage_states))
        # when we have a discrete fragility model and
        # the ground motion value is below the no_damage_limit or below
        # the lowest intensity measure level defined in the model
        # we simply use 100% no_damage and 0% for the
        # remaining limit states
        if self.format == 'discrete' and (
                gmv < self.no_damage_limit if self.no_damage_limit
                else gmv < self.imls[0]):
            damage_state_values[0] = 1.0
            return numpy.array(damage_state_values)

        first_poe = funcs[0].poe(gmv)

        # first damage state is always 1 - the probability
        # of exceedance of first limit state
        damage_state_values[0] = 1 - first_poe
        last_poe = first_poe

        # starting from one, the first damage state
        # is already computed...
        for x in xrange(1, len(funcs)):
            a_poe = funcs[x].poe(gmv)
            damage_state_values[x] = last_poe - a_poe
            last_poe = a_poe

        # last damage state is equal to the probability
        # of exceedance of the last limit state
        damage_state_values[len(funcs)] = funcs[len(funcs) - 1].poe(gmv)
        return damage_state_values

    def __eq__(self, other):
        return (self.imls == other.imls and self.format == other.format
                and self.damage_states == other.damage_states and
                self.no_damage_limit == other.no_damage_limit)

    def __ne__(self, other):
        return not self == other
