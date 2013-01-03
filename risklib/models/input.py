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


# TODO: validation on input values?
class FragilityFunctionContinuous(object):

    def __init__(self, fragility_model, mean, stddev, lsi):
        self.lsi = lsi
        self.mean = mean
        self.stddev = stddev
        self.fragility_model = fragility_model

    @property
    def is_discrete(self):
        return False


class FragilityFunctionDiscrete(object):

    def __init__(self, fragility_model, poes, lsi):
        self.lsi = lsi
        self.poes = poes
        self.fragility_model = fragility_model

    @property
    def is_discrete(self):
        return True


class FragilityModel(object):

    def __init__(self, format, imls, limit_states, no_damage_limit=None):
        self.imls = imls
        self.format = format
        self.lss = limit_states
        self.no_damage_limit = no_damage_limit


class Asset(object):

    def __init__(self, asset_ref, taxonomy, value, site,
                 number_of_units=None, ins_limit=None, deductible=None,
                 retrofitting_cost=None):
        self.site = site
        self.value = value
        self.taxonomy = taxonomy
        self.asset_ref = asset_ref
        self.ins_limit = ins_limit
        self.deductible = deductible
        self.number_of_units = number_of_units
        self.retrofitting_cost = retrofitting_cost
