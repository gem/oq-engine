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


NO_DAMAGE_STATE = "no_damage"


def damage_states(fragility_model):
    """
    Return the damage states from the given limit states.

    For N limit states in the fragility model, we always
    define N+1 damage states. The first damage state
    should always be '_no_damage'.

    :param fragility_model A Fragility Model object which support a
      property `lss` containing an iterator over limit states
    """

    dmg_states = list(fragility_model.lss)
    dmg_states.insert(0, NO_DAMAGE_STATE)

    return dmg_states


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
