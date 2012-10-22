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

import collections


ClassicalAssetOutput = collections.namedtuple("ClassicalAssetOutput",
    ["asset", "loss_ratio_curve", "loss_curve", "conditional_losses"])


ScenarioDamageAssetOutput = collections.namedtuple("ScenarioDamageAssetOutput",
    ["asset", "damage_distribution_asset", "collapse_map"])


BCRAssetOutput = collections.namedtuple("BCRAssetOutput", ["asset", "bcr",
    "eal_original", "eal_retrofitted"])


ProbabilisticEventBasedAssetOutput = collections.namedtuple(
    "ProbabilisticEventBasedAssetOutput", ["asset", "losses",
    "loss_ratio_curve", "loss_curve", "insured_loss_ratio_curve",
    "insured_loss_curve", "insured_losses", "conditional_losses"])


ScenarioRiskAssetOutput = collections.namedtuple("ScenarioRiskAssetOutput",
    ["asset", "mean", "standard_deviation"])
