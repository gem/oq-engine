#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Validation library
"""

import re

NAME = re.compile(r'[a-zA-Z_]\w*')


class Choice(object):
    """
    Check if the choice is valid.
    """
    def __init__(self, *choices):
        self.choices = choices

    def __call__(self, value):
        if not value in self.choices:
            raise ValueError('%r is not a valid choice in %s' % (
                             value, self.choices))

category = Choice('population', 'buildings')


def namelist(text):
    """String -> list of identifiers"""
    names = text.split()
    if not names:
        raise ValueError('Got an empty name list')
    for name in names:
        if NAME.match(name) is None:
            raise ValueError('%r is not a valid name' % name)
    return names


def longitude(text):
    """String -> longitude float"""
    lon = float(text)
    if lon > 180.:
        raise ValueError('longitude %s > 180' % lon)
    elif lon < -180.:
        raise ValueError('longitude %s < -180' % lon)
    return lon


def latitude(text):
    """String -> latitude float"""
    lat = float(text)
    if lat > 90.:
        raise ValueError('latitude %s > 90' % lat)
    elif lat < -90.:
        raise ValueError('latitude %s < -90' % lat)
    return lat


def positiveint(text):
    """String -> positive integer"""
    i = int(text)
    if i < 0:
        raise ValueError('integer %d < 0' % i)
    return i
