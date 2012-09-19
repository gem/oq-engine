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

import numpy

# TODO Update doc
def compute_gmf_fractions(gmf, funcs):
    """
    Compute the fractions of each damage state for
    each ground motion value given.

    :param gmf: ground motion values computed in the grid
        point where the asset is located.
    :type gmf: list of floats
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
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
        fractions[x] += compute_gmv_fractions(funcs, gmv)

    return fractions


def compute_gmv_fractions(funcs, gmv):
    """
    Compute the fractions of each damage state for
    the ground motion value given.

    :param gmv: ground motion value that defines the Intensity
        Measure Level used to interpolate the fragility functions.
    :type gmv: float
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
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
    if fm.no_damage(gmv):
        damage_states[0] = 1.0
        return numpy.array(damage_states)

    first_poe = funcs[0].poe(gmv)

    # first damage state is always 1 - the probability
    # of exceedance of first limit state
    damage_states[0] = 1 - first_poe

    last_poe = first_poe

    # starting from one, the first damage state
    # is already computed...
    for x in xrange(1, len(funcs)):
        poe = funcs[x].poe(gmv)
        damage_states[x] = last_poe - poe
        last_poe = poe

    # last damage state is equal to the probabily
    # of exceedance of the last limit state
    damage_states[len(funcs)] = funcs[len(funcs) - 1].poe(gmv)

    return numpy.array(damage_states)
