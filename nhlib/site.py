# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`nhlib.site` defines :class:`Site`.
"""
class Site(object):
    """
    Site object represents a geographical location defined by its position
    as well as its soil characteristics.

    :param location:
        Instance of :class:`~nhlib.geo.point.Point` representing where the site
        is located.
    :param vs30:
        Average shear wave velocity in the top 30 m, in m/s.
    :param vs30measured:
        Boolean value, ``True`` if ``vs30`` was measured on that location
        and ``False`` if it was inferred.
    :param z1pt0:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 1.0 km/sec, in km.
    :param z2pt5:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 2.5 km/sec, in km.

    :raises ValueError:
        If any of ``vs30``, ``z1pt0`` or ``z2pt5`` is zero or negative.
    """
    __slots__ = 'location vs30 vs30measured z1pt0 z2pt5'.split()

    def __init__(self, location, vs30, vs30measured, z1pt0, z2pt5):
        if not vs30 > 0:
            raise ValueError('vs30 must be positive')
        if not z1pt0 > 0:
            raise ValueError('z1pt0 must be positive')
        if not z2pt5 > 0:
            raise ValueError('z2pt5 must be positive')
        self.location = location
        self.vs30 = vs30
        self.vs30measured = vs30measured
        self.z1pt0 = z1pt0
        self.z2pt5 = z2pt5
