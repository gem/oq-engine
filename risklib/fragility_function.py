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


from scipy.stats import lognorm
from scipy.interpolate import interp1d
import math


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
    if iml > highest_iml:
        iml = highest_iml

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
