# -*- coding: utf-8 -*-

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


def compute_insured_losses(asset, losses):
    """
    Compute insured losses for the given asset using the related set of ground
    motion values and vulnerability function.

    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance.
    :param losses: an array of loss values multiplied by the asset value.
    :type losses: a 1-dimensional :py:class:`numpy.ndarray` instance.
    """

    for i, value in enumerate(losses):
        if value < asset.deductible:
            losses[i] = 0
        else:
            if value > asset.ins_limit:
                losses[i] = asset.ins_limit

    return losses
