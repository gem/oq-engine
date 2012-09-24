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
import numpy
from scipy.stats import lognorm
from scipy.interpolate import interp1d


def damage_states(fragility_model):
    """
    Return the damage states from the given limit states.

    For N limit states in the fragility model, we always
    define N+1 damage states. The first damage state
    should always be 'no_damage'.
    """

    dmg_states = list(fragility_model.lss)
    dmg_states.insert(0, "no_damage")

    return dmg_states


def compute_damage(sites, frag_functions, assets_getter,
                   ground_motion_field_getter,
                   on_asset_complete_cb=lambda: None):

    fractions_per_taxonomy = {}
    dmg_states = damage_states(
        frag_functions[frag_functions.keys()[0]][0].fragility_model)

    for site in sites:
        assets = assets_getter(site)
        ground_motion_field = ground_motion_field_getter(site)

        for asset in assets:
            damage_distribution_asset, fractions = \
                damage_distribution_per_asset(
                asset, frag_functions, ground_motion_field)

            on_asset_complete_cb(damage_distribution_asset,
                collapse_map(fractions), asset, dmg_states)

            asset_fractions = fractions_per_taxonomy.get(
                asset.taxonomy, numpy.zeros((len(ground_motion_field),
                                             len(frag_functions) + 1)))

            fractions_per_taxonomy[asset.taxonomy] = asset_fractions + fractions

    return fractions_per_taxonomy


def damage_distribution_by_taxonomy(set_of_fractions):
    total_fractions = {}

    for fractions in set_of_fractions:
        for taxonomy in fractions.keys():
            current_fractions = total_fractions.get(taxonomy, None)

            if current_fractions is None:
                total_fractions[taxonomy] = numpy.array(fractions[taxonomy])
            else:
                total_fractions[taxonomy] += fractions[taxonomy]

    means = {}
    stddevs = {}

    for taxonomy in total_fractions.keys():
        means[taxonomy] = numpy.mean(total_fractions[taxonomy], axis=0)
        stddevs[taxonomy] = numpy.std(
            total_fractions[taxonomy], axis=0, ddof=1)

    return (means, stddevs)


def total_damage_distribution(set_of_fractions):
    total_fractions = None

    for fractions in set_of_fractions:
        for taxonomy in fractions.keys():

            if total_fractions is None:
                total_fractions = numpy.array(fractions[taxonomy])
            else:
                total_fractions += fractions[taxonomy]

    return numpy.mean(total_fractions, axis=0),\
           numpy.std(total_fractions, axis=0, ddof=1)


def collapse_map(fractions):
    # the collapse map needs the fractions
    # for each ground motion value of the
    # last damage state (the last column)
    last_damage_state = fractions[:, -1]
    return numpy.mean(last_damage_state), \
        numpy.std(last_damage_state, ddof=1)


def damage_distribution_per_asset(asset, fragility_functions,
                                  ground_motion_field):

    # sorting the functions by lsi (limit state index),
    # because the algorithm must process them from the one
    # with the lowest limit state to the one with
    # the highest limit state
    functions = fragility_functions[asset.taxonomy]
    functions.sort(key=lambda x: x.lsi)

    fractions = _compute_gmf_fractions(ground_motion_field,
        fragility_functions[asset.taxonomy]) * asset.number_of_units

    return (numpy.mean(fractions, axis=0),
            numpy.std(fractions, axis=0, ddof=1)), fractions


def _poe(fragility_function, iml):
    """
    Compute the Probability of Exceedance (PoE) for the given
    Intensity Measure Level (IML).
    """
    if fragility_function.is_discrete:
        return _poe_discrete(fragility_function, iml)
    else:
        return _poe_continuous(fragility_function, iml)


def _poe_discrete(fragility_function, iml):
    fm = fragility_function.fragility_model

    highest_iml = fm.imls[-1]
    no_damage_limit = fm.no_damage_limit

    # when the intensity measure level is above
    # the range, we use the highest one
    if iml > highest_iml: iml = highest_iml

    imls = [no_damage_limit] + fm.imls
    poes = [0.0] + fragility_function.poes

    return interp1d(imls, poes)(iml)


def _poe_continuous(fragility_function, iml):
    variance = fragility_function.stddev ** 2.0
    sigma = math.sqrt(math.log(
        (variance / fragility_function.mean ** 2.0) + 1.0))

    mu = fragility_function.mean ** 2.0 / math.sqrt(
        variance + fragility_function.mean ** 2.0)

    return lognorm.cdf(iml, sigma, scale=mu)


def _compute_gmf_fractions(gmf, funcs):
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
    fractions = numpy.zeros((len(gmf), len(funcs) + 1))

    for x, gmv in enumerate(gmf):
        fractions[x] = _compute_gmv_fractions(funcs, gmv)

    return fractions


def _compute_gmv_fractions(funcs, gmv):
    """
    Compute the fractions of each damage state for
    the Ground Motion Value given (a Ground Motion Value
    defines the Intensity Measure Level (IML) used to
    interpolate the Fragility Function.

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
    damage_states = numpy.zeros(len(funcs) + 1)
    fm = funcs[0].fragility_model

    # when we have a discrete fragility model and
    # the ground motion value is below the lowest
    # intensity measure level defined in the model
    # we simply use 100% no_damage and 0% for the
    # remaining limit states
    if _no_damage(fm, gmv):
        damage_states[0] = 1.0
        return numpy.array(damage_states)

    first_poe = _poe(funcs[0], gmv)

    # first damage state is always 1 - the probability
    # of exceedance of first limit state
    damage_states[0] = 1 - first_poe
    last_poe = first_poe

    # starting from one, the first damage state
    # is already computed...
    for x in xrange(1, len(funcs)):
        poe = _poe(funcs[x], gmv)
        damage_states[x] = last_poe - poe
        last_poe = poe

    # last damage state is equal to the probability
    # of exceedance of the last limit state
    damage_states[len(funcs)] = _poe(funcs[len(funcs) - 1], gmv)
    return numpy.array(damage_states)


def _no_damage(fragility_model, gmv):
    """
    There is no damage when ground motions values are less
    than the first iml or when the no damage limit value
    is greater than the ground motions value.
    """

    discrete = fragility_model.format == "discrete"
    no_damage_limit = fragility_model.no_damage_limit is not None

    return ((discrete and not no_damage_limit and
             gmv < fragility_model.imls[0]) or
            (discrete and no_damage_limit and
             gmv < fragility_model.no_damage_limit))
