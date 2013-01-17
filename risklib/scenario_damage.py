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


"""
This module defines the functions useful for a scenario-damage
calculator
"""

import numpy


def _damage_distribution_per_asset(
        asset, (fragility_model, fragility_functions), ground_motion_field):
    """
    Computes the damage distribution related with a single asset.

    :return a matrix NxM of damage states per ground motion values

    :param asset
      the asset considered. It must provide the property
      number_of_units

    :param fragility_functions
      an iterator over the fragility functions related with the
      `asset`. Each Fragility function must provide the property lsi
      (limit state index)

    :param ground_motion_field
      the ground motion field object associated with the `asset`
    """
    # sorting the functions by lsi (limit state index),
    # because the algorithm must process them from the one
    # with the lowest limit state to the one with
    # the highest limit state
    fragility_functions_sorted = sorted(
        fragility_functions, key=lambda x: x.lsi)
    fractions = numpy.array([
        _ground_motion_value_fractions(
            (fragility_model, fragility_functions_sorted), gmv)
        * asset.number_of_units
        for gmv in ground_motion_field])
    return fractions


def _ground_motion_value_fractions((fragility_model, funcs), gmv):
    """
    Compute the fractions of each damage state for
    the Ground Motion Value given (a Ground Motion Value
    defines the Intensity Measure Level (IML) used to
    interpolate the Fragility Function.

    :param fragility_model
      The fragility model

    :param gmv: ground motion value.
    :type gmv: float
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`risklib.scenario_damage.models.FragilityFunction` instances
    :returns: the fraction of buildings of each damage state
        computed for the given ground motion value.
    :rtype: 1d `numpy.array`. Each value represents
        the fraction of a damage state (in order from the lowest
        to the highest)
    """

    # we always have a number of damage states which is len(limit states) + 1
    damage_state_values = numpy.zeros(len(fragility_model.damage_states))

    # when we have a discrete fragility model and
    # the ground motion value is below the lowest
    # intensity measure level defined in the model
    # we simply use 100% no_damage and 0% for the
    # remaining limit states
    if fragility_model.no_damage(gmv):
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
    return numpy.array(damage_state_values)
