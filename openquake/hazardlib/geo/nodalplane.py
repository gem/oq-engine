# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.nodalplane` implements
:class:`NodalPlane`.
"""
from openquake.baselib.slots import with_slots


@with_slots
class NodalPlane(object):
    """
    Nodal plane represents earthquake rupture orientation and propagation
    direction.

    :param strike:
        Angle between line created by the intersection of rupture plane
        and the North direction (defined between 0 and 360 degrees).
    :param dip:
        Angle between earth surface and fault plane (defined between 0 and 90
        degrees).
    :param rake:
        Angle describing rupture propagation direction (defined between -180
        and +180 degrees).
    :raises ValueError:
        If any of parameters exceeds the definition range.
    """
    _slots_ = ['strike', 'dip', 'rake']

    def __init__(self, strike, dip, rake):
        self.check_dip(dip)
        self.check_rake(rake)
        self.check_strike(strike)
        self.strike = strike
        self.dip = dip
        self.rake = rake

    @classmethod
    def check_dip(cls, dip):
        """
        Check if ``dip`` is in range ``(0, 90]``
        and raise ``ValueError`` otherwise.
        """
        if not 0 < dip <= 90:
            raise ValueError('dip %g is out of range (0, 90]' % dip)

    @classmethod
    def check_strike(cls, strike):
        """
        Check if ``strike`` is in range ``[0, 360)``
        and raise ``ValueError`` otherwise.
        """
        if not 0 <= strike < 360:
            raise ValueError('strike %g is out of range [0, 360)' % strike)

    @classmethod
    def check_rake(cls, rake):
        """
        Check if ``rake`` is in range ``(-180, 180]``
        and raise ``ValueError`` otherwise.
        """
        if not -180 < rake <= 180:
            raise ValueError('rake %g is out of range (-180, 180]' % rake)
