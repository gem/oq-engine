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


class AssetOutput(object):

    def __init__(self, asset):
        self.asset = asset


class ClassicalAssetOutput(AssetOutput):

    def __init__(self, asset, loss_ratio_curve,
        loss_curve, conditional_losses=None):

        super(ClassicalAssetOutput, self).__init__(asset)

        self.loss_curve = loss_curve
        self.loss_ratio_curve = loss_ratio_curve
        self.conditional_losses = conditional_losses

    def __eq__(self, other):
        return (self.asset == other.asset and
            self.loss_ratio_curve == other.loss_ratio_curve and
            self.loss_curve == other.loss_curve and
            self.conditional_losses == other.conditional_losses)

    def __ne__(self, other):
        return not self.__eq__(other)
