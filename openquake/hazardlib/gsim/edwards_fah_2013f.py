# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports
:class:`EdwardsFah2013Foreland10Bars`,
:class:`EdwardsFah2013Foreland20Bars`,
:class:`EdwardsFah2013Foreland30Bars`,
:class:`EdwardsFah2013Foreland50Bars`,
:class:`EdwardsFah2013Foreland60Bars`,
:class:`EdwardsFah2013Foreland75Bars`,
:class:`EdwardsFah2013Foreland90Bars`,
:class:`EdwardsFah2013Foreland120Bars`
"""

from openquake.hazardlib.gsim.edwards_fah_2013a import (
    EdwardsFah2013Alpine10Bars)
from openquake.hazardlib.gsim.edwards_fah_2013f_coeffs import (
    COEFFS_FORELAND_10Bars, COEFFS_FORELAND_20Bars, COEFFS_FORELAND_30Bars,
    COEFFS_FORELAND_50Bars, COEFFS_FORELAND_60Bars, COEFFS_FORELAND_75Bars,
    COEFFS_FORELAND_90Bars, COEFFS_FORELAND_120Bars)


class EdwardsFah2013Foreland10Bars(EdwardsFah2013Alpine10Bars):
    """
    This function implements the GMPE developed by Ben Edwards and
    Donath Fah and published as "A Stochastic Ground-Motion Model
    for Switzerland" Bulletin of the Seismological
    Society of America, Vol. 103, No. 1, pp. 78–98, February 2013.
    The GMPE was parametrized by Carlo Cauzzi to be implemented in OpenQuake.
    This class implements the equations for 'Foreland - two
    tectonic regionalizations defined for the Switzerland -
    therefore this GMPE is region specific".
    """
    COEFFS = COEFFS_FORELAND_10Bars


class EdwardsFah2013Foreland20Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 20Bars Model :class:`EdwardsFah2013Foreland20Bars`
    """
    COEFFS = COEFFS_FORELAND_20Bars


class EdwardsFah2013Foreland30Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 30Bars Model :class:`EdwardsFah2013Foreland30Bars`
    """
    COEFFS = COEFFS_FORELAND_30Bars


class EdwardsFah2013Foreland50Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 50Bars Model :class:`EdwardsFah2013Foreland50Bars`
    """
    COEFFS = COEFFS_FORELAND_50Bars


class EdwardsFah2013Foreland60Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 60Bars Model :class:`EdwardsFah2013Foreland60Bars`
    """
    COEFFS = COEFFS_FORELAND_60Bars


class EdwardsFah2013Foreland75Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 75Bars Model :class:`EdwardsFah2013Foreland75Bars`
    """
    COEFFS = COEFFS_FORELAND_75Bars


class EdwardsFah2013Foreland90Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 90Bars Model :class:`EdwardsFah2013Foreland90Bars`
    """
    COEFFS = COEFFS_FORELAND_90Bars


class EdwardsFah2013Foreland120Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 120Bars Model :class:`EdwardsFah2013Foreland120Bars`
    """
    COEFFS = COEFFS_FORELAND_120Bars
