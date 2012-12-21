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


def mean(values):
    "Averages between a value and the next value in a sequence"
    return map(numpy.mean, zip(values, values[1:]))


def diff(values):
    "Differences between a value and the next value in a sequence"
    return [x - y for x, y in zip(values, values[1:])]


def mean_loss(curve):
    """
    Compute the mean loss (or loss ratio) for the given curve.
    For instance, for a curve with four values [(x1, y1), (x2, y2), (x3, y3),
    (x4, y4)], returns

      x1 + 2x2 + x3  y1 - y3    x2 + 2x3 + x4  y2 - y4
    [(-------------, -------), (-------------, -------)]
           4             2            4           4
    """
    mean_ratios = mean(mean(curve.abscissae))  # not clear why it is done twice
    mean_pes = diff(mean(curve.ordinates))
    return numpy.dot(mean_ratios, mean_pes)
