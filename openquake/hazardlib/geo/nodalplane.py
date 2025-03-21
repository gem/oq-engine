# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import collections

NP = collections.namedtuple('NP', 'strike dip rake')


# NB: instantiating NodalPlane returns instances of NP, so it is a hack,
# but it is the simplest solution that maintains backward compatibility
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

    def __new__(cls, strike, dip, rake):
        cls.check_dip(dip)
        cls.check_rake(rake)
        cls.check_strike(strike)
        return NP(strike, dip, rake)

    @classmethod
    def check_dip(cls, dip):
        """
        Check if ``dip`` is in range ``(0, 90]``
        and raise ``ValueError`` otherwise.
        """
        if not 0 < dip < 90.000001:  # some tolerance for numeric errors
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
        if not (rake == 'undefined' or -180 < rake < 180.000001):
            # some tolerance for numeric errors
            raise ValueError('rake %g is out of range (-180, 180]' % rake)
