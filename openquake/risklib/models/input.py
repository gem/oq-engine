# coding=utf-8
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
import math
from collections import Sequence, namedtuple
from scipy.stats import lognorm
from scipy.interpolate import interp1d
import numpy


# TODO: validation on input values?
class FragilityFunctionContinuous(object):

    def __init__(self, funcseq, mean_stddev):
        self.funcs = funcseq
        self.mean, self.stddev = mean_stddev

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

    def __init__(self, funcseq, poes):
        self.funcs = funcseq
        self.poes = poes
        self._interp = None

    @property
    def interp(self):
        if self._interp is not None:
            return self._interp
        fm = self.funcs.fragility_model
        imls = [self.funcs.no_damage_limit] + fm.imls
        poes = [0.0] + self.poes
        self._interp = interp1d(imls, poes)
        return self._interp

    def poe(self, iml):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Level (IML).
        """
        highest_iml = self.funcs.fragility_model.imls[-1]
        # when the intensity measure level is above
        # the range, we use the highest one
        return self.interp(highest_iml if iml > highest_iml else iml)

    # so that the curve is pickeable
    def __getstate__(self):
        return dict(poes=self.poes, funcs=self.funcs, _interp=None)

    def __eq__(self, other):
        return (self.poes == other.poes
                and self.funcs == other.funcs)

    def __ne__(self, other):
        return not self == other


class FragilityFunctionSeq(Sequence):
    """
    An ordered sequence of fragility functions, one for each limit state
    except the "no_damage" state.
    """
    def __init__(self, fragility_model, args, no_damage_limit=None):
        self.fragility_model = fragility_model
        self.fftype = (FragilityFunctionDiscrete
                       if fragility_model.format == 'discrete'
                       else FragilityFunctionContinuous)
        self.fflist = [self.fftype(self, arg) for arg in args]
        self.no_damage_limit = no_damage_limit

    def __getitem__(self, i):
        return self.fflist[i]

    def __len__(self):
        return len(self.fflist)

    def ground_motion_value_fractions(self, gmv):
        """
        Compute the fractions of each damage state for
        the Ground Motion Value given (a Ground Motion Value
        defines the Intensity Measure Level (IML) used to
        interpolate the Fragility Function.

        :param self
          The fragility model
        :param gmv: ground motion value.
        :type gmv: float
        :param self: list of fragility functions describing
            the distribution for each limit state. The functions
            must be in order from the one with the lowest
            limit state to the one with the highest limit state.
        :type self: :py:class:`FragilityFunctionSeq` instance
        :returns: the fraction of buildings of each damage state
            computed for the given ground motion value.
        :rtype: 1d `numpy.array`. Each value represents
            the fraction of a damage state (in order from the lowest
            to the highest)
        """
        n_limit_states = len(self)
        # For N limit states in the fragility model, we always define N+1
        # damage states. The first damage state is always 'no_damage'.
        damage_state_values = numpy.zeros(n_limit_states + 1)
        # when we have a discrete fragility model and
        # the ground motion value is below the no_damage_limit or below
        # the lowest intensity measure level defined in the model
        # we simply use 100% no_damage and 0% for the
        # remaining limit states
        if self.fragility_model.format == 'discrete' and (
                gmv < self.no_damage_limit if self.no_damage_limit
                else gmv < self.fragility_model.imls[0]):
            damage_state_values[0] = 1.0
            return numpy.array(damage_state_values)

        first_poe = self[0].poe(gmv)

        # first damage state is always 1 - the probability
        # of exceedance of first limit state
        damage_state_values[0] = 1 - first_poe
        last_poe = first_poe

        # starting from one, the first damage state
        # is already computed...
        for x in xrange(1, n_limit_states):
            a_poe = self[x].poe(gmv)
            damage_state_values[x] = last_poe - a_poe
            last_poe = a_poe

        # last damage state is equal to the probability
        # of exceedance of the last limit state
        damage_state_values[n_limit_states] = self[n_limit_states - 1].poe(gmv)
        return damage_state_values


FragilityModel = namedtuple('FragilityModel', 'format imls limit_states')
