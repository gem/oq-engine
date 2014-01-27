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
import collections


class NoneOr(object):
    """
    Accept the empty string (casted to None) or something else validated
    by the cast callable.
    """
    def __init__(self, cast):
        self.cast = cast

    def __call__(self, value):
        if value == '':
            return None
        return self.cast(value)


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
        return value

category = Choice('population', 'buildings')


class Regex(object):
    """
    Compare the value with the given regex
    """
    def __init__(self, regex):
        self.rx = re.compile(regex)

    def __call__(self, value):
        if self.rx.match(value) is None:
            raise ValueError('%r does not match the regex %r' %
                             (value, self.rx.pattern))
        return value

name = Regex(r'^[a-zA-Z_]\w*$')


class FloatRange(object):
    def __init__(self, minrange, maxrange):
        self.minrange = minrange
        self.maxrange = maxrange

    def __call__(self, value):
        f = float(value)
        if f > self.maxrange:
            raise ValueError('%r is bigger than the max, %r' %
                             (f, self.maxrange))
        if f < self.minrange:
            raise ValueError('%r is smaller than the min, %r' %
                             (f, self.minrange))
        return f


def not_empty(text):
    """Check that the string is not empty"""
    if not text:
        raise ValueError('Got an empty string')
    return text


def namelist(text):
    """String -> list of identifiers"""
    names = text.split()
    if not names:
        raise ValueError('Got an empty name list')
    return map(name, names)


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


def positivefloat(text):
    """String -> positive float"""
    f = float(text)
    if f < 0:
        raise ValueError('float %d < 0' % f)
    return f


_BOOL_DICT = {
    '0': False,
    '1': True,
    'false': False,
    'true': True,
}


def boolean(text):
    """String -> boolean"""
    if text.lower() in _BOOL_DICT and text.lower() != text:
        raise ValueError('%r is not a lowercase string' % text)
    try:
        return _BOOL_DICT[text]
    except KeyError:
        raise ValueError('Not a boolean: %s' % text)


probability = FloatRange(0, 1)

IMT = collections.namedtuple('IMT', 'imt saPeriod saDamping')


def IMTstr(text):
    """String -> namedtuple with fields imt, saPeriod, saDamping"""
    mo = re.match(r'PGA|PGV|PGD|IA|RSD|MMI|SA\((\d+\.?\d*)\)', text)
    if mo is None:
        raise ValueError('%r is not a valid IMT' % text)
    period = mo.group(1)
    if period:
        return IMT('SA', float(period), 5.0)
    return IMT(text, None, None)
