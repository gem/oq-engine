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


"""
This module defines the functions useful for a scenario-damage
calculator
"""

import numpy
from risklib.fragility_model import damage_states, _no_damage
from risklib.fragility_function import _poe


def damage_distribution_by_taxonomy(set_of_fractions):
    """
    Given an iterator over fractions, it aggregates them by taxonomy
    and returns the means and standard deviations for each taxonomy.

    :param set_of_fractions
      set_of_fractions is an iterator over dictionaries, where each
      dictionary maps a taxonomy to a damage distribution matrix
    """
    total_fractions = {}

    for fractions in set_of_fractions:
        for taxonomy in fractions:
            if not taxonomy in total_fractions:
                total_fractions[taxonomy] = numpy.array(fractions[taxonomy])
            else:
                total_fractions[taxonomy] += fractions[taxonomy]

    means = {}
    stddevs = {}

    for taxonomy in total_fractions:
        means[taxonomy], stddevs[taxonomy] = (
            _damage_distribution_stats(total_fractions[taxonomy]))

    return (means, stddevs)


def total_damage_distribution(set_of_fractions):

    if not set_of_fractions or not set_of_fractions[0]:
        return None

    # get the shape of the damage distribution matrix
    shape = set_of_fractions[0].values()[0].shape

    total_fractions = numpy.zeros(shape)

    for fractions in set_of_fractions:
        for taxonomy in fractions:
            total_fractions += fractions[taxonomy]

    return _damage_distribution_stats(total_fractions)


def _collapse_map(fractions):
    # the collapse map needs the fractions
    # for each ground motion value of the
    # last damage state (the last column)
    return _damage_distribution_stats(fractions[:, -1])


def _damage_distribution_per_asset(
        asset, (fragility_model, fragility_functions), ground_motion_field):
    """
    Computes the damage distribution related with a single asset.

    :return a tuple of the form ((x, y), z) where z is a matrix NxM
      (damage states per ground motion values), x and y are vectors with
      the means and the standard deviation computed for each damage
      state, respectively.

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

    fractions = _ground_motion_field_fractions(
        (fragility_model, fragility_functions_sorted), ground_motion_field)
    fractions *= asset.number_of_units

    return _damage_distribution_stats(fractions), fractions


def _ground_motion_field_fractions((fragility_model, funcs), gmf):
    """
    Compute the fractions of each damage state for
    each ground motion value given. `gmf` means Ground Motion Field,
    a set of Ground Motion Values that are logically related (they
    are generally associated with a single asset).

    :param gmf: ground motion values.
    :type gmf: list of floats
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`risklib.scenario_damage.models.FragilityFunction` instances
    :returns: the fractions for each damage state.
    :rtype: 2d `numpy.array`. Each column represents
        a damage state (in order from the lowest
        to the highest). Each row represents the
        values for that damage state for a particular
        ground motion value.
    """

    # we always have a number of damage states
    # which is len(limit states) + 1
    fractions = _make_damage_distribution_matrix(fragility_model, gmf)

    for x, gmv in enumerate(gmf):
        fractions[x] = _ground_motion_value_fractions(
            (fragility_model, funcs), gmv)

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

    # we always have a number of damage states
    # which is len(limit states) + 1
    damage_state_values = _make_damage_distribution_matrix(fragility_model)

    # when we have a discrete fragility model and
    # the ground motion value is below the lowest
    # intensity measure level defined in the model
    # we simply use 100% _no_damage and 0% for the
    # remaining limit states
    if _no_damage(fragility_model, gmv):
        damage_state_values[0] = 1.0
        return numpy.array(damage_state_values)

    first_poe = _poe(funcs[0], gmv)

    # first damage state is always 1 - the probability
    # of exceedance of first limit state
    damage_state_values[0] = 1 - first_poe
    last_poe = first_poe

    # starting from one, the first damage state
    # is already computed...
    for x in xrange(1, len(funcs)):
        a_poe = _poe(funcs[x], gmv)
        damage_state_values[x] = last_poe - a_poe
        last_poe = a_poe

    # last damage state is equal to the probability
    # of exceedance of the last limit state
    damage_state_values[len(funcs)] = _poe(funcs[len(funcs) - 1], gmv)
    return numpy.array(damage_state_values)


def _make_damage_distribution_matrix(
        fragility_model, ground_motion_field=None):
    if ground_motion_field:
        shape = (len(ground_motion_field),
                 len(damage_states(fragility_model)))
    else:
        shape = len(damage_states(fragility_model))
    return numpy.zeros(shape)


def _damage_distribution_stats(fractions):
    return (numpy.mean(fractions, axis=0),
            numpy.std(fractions, axis=0, ddof=1))
