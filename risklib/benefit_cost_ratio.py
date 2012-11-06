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

import numpy
import math


def bcr(eal_original, eal_retrofitted, interest_rate,
                asset_life_expectancy, retrofitting_cost):
    """
    Compute the Benefit-Cost Ratio.

    BCR = (EALo - EALr)(1-exp(-r*t))/(r*C)

    Where:

    * BCR -- Benefit cost ratio
    * EALo -- Expected annual loss for original asset
    * EALr -- Expected annual loss for retrofitted asset
    * r -- Interest rate
    * t -- Life expectancy of the asset
    * C -- Retrofitting cost
    """
    return ((eal_original - eal_retrofitted)
            * (1 - math.exp(- interest_rate * asset_life_expectancy))
            / (interest_rate * retrofitting_cost))


def mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    pes = curve.ordinates
    loss_ratios = curve.abscissae

    mean_loss_ratios = [numpy.mean([x, y])
                        for x, y in zip(loss_ratios, loss_ratios[1:])]

    mid_pes = [numpy.mean([x, y])
               for x, y in zip(pes, pes[1:])]

    mean_loss_ratios = [numpy.mean([x, y])
                        for x, y in zip(mean_loss_ratios, mean_loss_ratios[1:])]

    mid_pes = [x - y for x, y in zip(mid_pes, mid_pes[1:])]

    return numpy.dot(mean_loss_ratios, mid_pes)
