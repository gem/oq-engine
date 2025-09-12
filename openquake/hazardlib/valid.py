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
Validation library for the engine, the desktop tools, and anything else
"""

import os
import re
import ast
import json
import toml
import socket
import logging
import inspect
from functools import partial
import numpy

from openquake.baselib.general import distinct, pprod
from openquake.baselib import config, hdf5
from openquake.hazardlib import imt, scalerel, gsim, pmf, site, tom
from openquake.hazardlib.gsim.base import registry, gsim_aliases
from openquake.hazardlib.calc.filters import (  # noqa
    IntegrationDistance, floatdict
)
from openquake.sep import classes

RENAMED_SEPS = {
    'NewmarkDisplacement': "Jibson2007BLandslides",
    'GrantEtAl2016RockSlopeFailure': "Jibson2007ALandslides"}

PRECISION = pmf.PRECISION

SCALEREL = scalerel._get_available_class(scalerel.BaseMSR)

GSIM = gsim.get_available_gsims()

MAG, DIS, LON, LAT, EPS = 0, 1, 2, 3, 4

mag_pmf = partial(pprod, axis=(DIS, LON, LAT, EPS))
dist_pmf = partial(pprod, axis=(MAG, LON, LAT, EPS))
mag_dist_pmf = partial(pprod, axis=(LON, LAT, EPS))
mag_dist_eps_pmf = partial(pprod, axis=(LON, LAT))
lon_lat_pmf = partial(pprod, axis=(DIS, MAG, EPS))
mag_lon_lat_pmf = partial(pprod, axis=(DIS, EPS))
# applied on matrix MAG DIS LON LAT EPS


def trt_pmf(matrices):
    """
    From T matrices of shape (Ma, D, Lo, La, E, ...) into one matrix of
    shape (T, ...)
    """
    return numpy.array([pprod(mat, axis=(MAG, DIS, LON, LAT, EPS))
                        for mat in matrices])


# this dictionary is useful to extract a fixed set of
# submatrices from the full disaggregation matrix
# NB: the TRT keys have extractor None, since the extractor
# without TRT can be used; we still need to populate the pmf_map
# since it is used to validate the keys accepted by the job.ini file
pmf_map = dict([
    ('Mag', mag_pmf),
    ('Dist', dist_pmf),
    ('Mag_Dist', mag_dist_pmf),
    ('Mag_Dist_Eps', mag_dist_eps_pmf),
    ('Lon_Lat', lon_lat_pmf),
    ('Mag_Lon_Lat', mag_lon_lat_pmf),
    ('TRT', trt_pmf),
    ('TRT_Mag', None),
    ('TRT_Lon_Lat', None),
    ('TRT_Mag_Dist', None),
    ('TRT_Mag_Dist_Eps', None),
])


def disagg_outputs(value):
    """
    Validate disaggregation outputs. For instance

    >>> disagg_outputs('TRT Mag_Dist')
    ['TRT', 'Mag_Dist']
    >>> disagg_outputs('TRT, Mag_Dist')
    ['TRT', 'Mag_Dist']
    """
    values = value.replace(',', ' ').split()
    for val in values:
        if val not in pmf_map:
            raise ValueError('Invalid disagg output: %s' % val)
    return values


class FromFile(object):
    """
    Fake GSIM to be used when the GMFs are imported from an
    external file and not computed with a GSIM.
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    DEFINED_FOR_REFERENCE_VELOCITY = None
    _toml = '[FromFile]'
    kwargs = {}

    def compute(self, ctx, imts, mean, sig, tau, phi):
        pass

    def requires(self):
        return ()

    def __repr__(self):
        return '[FromFile]'


def to_toml(uncertainty):
    """
    Converts an uncertainty node into a TOML string
    """
    if hasattr(uncertainty, 'attrib'):  # is a node
        text = uncertainty.text.strip()
        kvs = uncertainty.attrib.items()
    else:  # is a string
        text = uncertainty.strip()
        kvs = []
    text = gsim_aliases.get(text, text)  # use the gsim alias if any
    if not text.startswith('['):  # a bare GSIM name was passed
        text = '[%s]' % text
    for k, v in kvs:
        try:
            v = ast.literal_eval(v)
        except (SyntaxError, ValueError):
            v = repr(v)
        text += '\n%s = %s' % (k, v)
    return text


def _fix_toml(v):
    # horrible hack to remove a pickle error with
    # TomlDecoder.get_empty_inline_table.<locals>.DynamicInlineTableDict
    # using toml.loads(s, _dict=dict) would be the right way, but it does
    # not work :-(
    if isinstance(v, numpy.ndarray):
        return list(v)
    elif hasattr(v, 'items'):
        return {k1: _fix_toml(v1) for k1, v1 in v.items()}
    elif isinstance(v, list):
        return [_fix_toml(x) for x in v]
    elif isinstance(v, numpy.float64):
        return float(v)
    return v


# more tests are in tests/valid_test.py
def gsim(value, basedir=''):
    """
    Convert a string into a GSIM instance

    >>> gsim('BooreAtkinson2011')
    [BooreAtkinson2011]
    """
    value = to_toml(value)  # convert to TOML
    [(gsim_name, kwargs)] = toml.loads(value).items()
    kwargs = _fix_toml(kwargs)
    for k, v in kwargs.items():
        if k.endswith(('_file', '_table')):
            kwargs[k] = os.path.normpath(os.path.join(basedir, v))
    if gsim_name == 'FromFile':
        return FromFile()
    try:
        gsim_class = registry[gsim_name]
    except KeyError:
        raise NameError('Unknown GSIM: %s' % gsim_name)
    if inspect.isclass(gsim_class):
        gs = gsim_class(**kwargs)
    else:  # is an alias, i.e. a thunk
        gs = gsim_class()
    gs._toml = '\n'.join(line.strip() for line in value.splitlines())
    return gs


def modified_gsim(gmpe, **kwargs):
    """
    Builds a ModifiableGMPE from a gmpe. Used for instance in the GEESE project
    as follows:

    mgs = modified_gsim(gsim, add_between_within_stds={'with_betw_ratio':1.5})
    """
    name, *args = gmpe._toml.split('\n')
    text = name.replace('[', '[ModifiableGMPE.gmpe.')
    for arg in args:
        text += '\n' + arg
    text += '\n' + toml.dumps({'ModifiableGMPE': kwargs})
    return gsim(text)


def occurrence_model(value):
    """
    Converts a TOML string into a TOM instance

    >>> print(occurrence_model('[PoissonTOM]\\ntime_span=50.0'))
    [PoissonTOM]
    time_span = 50.0
    <BLANKLINE>
    """
    [(clsname, dic)] = toml.loads(value).items()
    return tom.registry[clsname](**dic)


def logic_tree_path(value):
    """
    >>> logic_tree_path('SM2_a3b1')
    ['SM2', 'a3b1']
    """
    return value.split('_')


def compose(*validators):
    """
    Implement composition of validators. For instance

    >>> utf8_not_empty = compose(utf8, not_empty)
    """
    def composed_validator(value):
        out = value
        for validator in reversed(validators):
            out = validator(out)
        return out
    composed_validator.__name__ = 'compose(%s)' % ','.join(
        val.__name__ for val in validators)
    return composed_validator


class NoneOr(object):
    """
    Accept the empty string (casted to None) or something else validated
    by the underlying `cast` validator.
    """
    def __init__(self, cast):
        self.cast = cast
        self.__name__ = cast.__name__

    def __call__(self, value):
        if value:
            return self.cast(value)


class Choice(object):
    """
    Check if the choice is valid (case sensitive).
    """
    @property
    def __name__(self):
        return 'Choice%s' % str(self.choices)

    def __init__(self, *choices):
        self.choices = choices

    def __call__(self, value):
        if value not in self.choices:
            raise ValueError("Got '%s', expected %s" % (
                             value, '|'.join(self.choices)))
        return value


class ChoiceCI(object):
    """
    Check if the choice is valid (case insensitive version).
    """
    def __init__(self, *choices):
        self.choices = choices
        self.__name__ = 'ChoiceCI%s' % str(choices)

    def __call__(self, value):
        value = value.lower()
        if value not in self.choices:
            raise ValueError("'%s' is not a valid choice in %s" % (
                             value, self.choices))
        return value


category = ChoiceCI('population', 'buildings')


class Choices(Choice):
    """
    Convert the choices, passed as a comma separated string, into a tuple
    of validated strings. For instance

    >>> Choices('xml', 'csv')('xml,csv')
    ('xml', 'csv')
    """
    def __call__(self, value):
        values = value.lower().split(',')
        for val in values:
            if val not in self.choices:
                raise ValueError("'%s' is not a valid choice in %s" % (
                    val, self.choices))
        return tuple(values)


export_formats = Choices('', 'xml', 'geojson', 'txt', 'csv', 'npz', 'hdf5')


class Regex(object):
    """
    Compare the value with the given regex
    """
    def __init__(self, regex):
        self.rx = re.compile(regex)
        self.__name__ = 'Regex[%s]' % regex

    def __call__(self, value):
        if self.rx.match(value) is None:
            raise ValueError("'%s' does not match the regex '%s'" %
                             (value, self.rx.pattern))
        return value


name = Regex(r'^[a-zA-Z_]\w*$')

name_with_dashes = Regex(r'^[a-zA-Z_][\w\-]*$')

# e.g. 2023-02-06 04:17:34+03:00
# +03:00 indicates the time zone offset from Coordinated Universal Time (UTC)
local_timestamp = Regex(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2})$")


class SimpleId(object):
    """
    Check if the given value is a valid ID.

    :param length: maximum length of the ID
    :param regex: accepted characters
    """
    def __init__(self, length, regex=r'^[\w_\-:]+$'):
        self.length = length
        self.regex = regex
        self.__name__ = 'SimpleId(%d, %s)' % (length, regex)

    def __call__(self, value):
        if len(value) == 0:
            raise ValueError('Invalid ID: can not be empty')
        if max(map(ord, value)) > 127:
            raise ValueError(
                'Invalid ID %r: the only accepted chars are %s' % (
                    value, self.regex))
        elif len(value) > self.length:
            raise ValueError("The ID '%s' is longer than %d character" %
                             (value, self.length))
        elif re.match(self.regex, value):
            return value
        raise ValueError(
            "Invalid ID '%s': the only accepted chars are %s" % (
                value, self.regex))


MAX_ID_LENGTH = 75  # length required for some sources in US14 collapsed model
ASSET_ID_LENGTH = 50  # length that makes Murray happy

simple_id = SimpleId(MAX_ID_LENGTH)
branch_id = SimpleId(MAX_ID_LENGTH, r'^[\w\:\#_\-\.]+$')
asset_id = SimpleId(ASSET_ID_LENGTH)
source_id = SimpleId(MAX_ID_LENGTH, r'^[\w\-_:]+$')
three_letters = SimpleId(3, r'^[A-Z]+$')
nice_string = SimpleId(  # nice for Windows, Linux, HDF5 and XML
    ASSET_ID_LENGTH, r'[a-zA-Z0-9\.`!#$%\(\)\+/,;@\[\]\^_{|}~-]+')
mod_func = SimpleId(MAX_ID_LENGTH, r'[\w_]+\.[\w_]+')


def risk_id(value):
    """
    A valid risk ID cannot contain the characters #'"
    """
    if '#' in value or '"' in value or "'" in value:
        raise ValueError('Invalid ID "%s" contains forbidden chars' % value)
    return value


class FloatRange(object):
    def __init__(self, minrange, maxrange, name='', accept=None):
        self.minrange = minrange
        self.maxrange = maxrange
        self.name = name
        self.accept = accept
        self.__name__ = 'FloatRange[%s:%s]' % (minrange, maxrange)

    def __call__(self, value):
        try:
            f = float_(value)
        except ValueError:  # passed a string
            if value == self.accept:
                return value
            else:
                raise
        if f > self.maxrange:
            raise ValueError("%s %s is bigger than the maximum (%s)" %
                             (self.name, f, self.maxrange))
        if f < self.minrange:
            raise ValueError("%s %s is smaller than the minimum (%s)" %
                             (self.name, f, self.minrange))
        return f


magnitude = FloatRange(0, 11, 'magnitude')


def not_empty(value):
    """Check that the string is not all blanks"""
    if value is None or value.strip() == '':
        raise ValueError('Got an empty string')
    return value


def utf8(value):
    r"""
    Check that the string is UTF-8. Returns an encode bytestring.

    >>> utf8(b'\xe0')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: Not UTF-8: ...
    """
    try:
        if isinstance(value, bytes):
            return value.decode('utf-8')
        else:
            return value
    except Exception:
        raise ValueError('Not UTF-8: %r' % value)


def utf8_not_empty(value):
    """Check that the string is UTF-8 and not empty"""
    return utf8(not_empty(value))


def namelist(value):
    """
    :param value: input string
    :returns: list of identifiers separated by whitespace or commas

    >>> namelist('a,b')
    ['a', 'b']
    >>> namelist('a1  b_2\t_c')
    ['a1', 'b_2', '_c']

    >>> namelist('a1 b_2 1c')
    ['a1', 'b_2', '1c']
    """
    names = value.replace(',', ' ').split()
    for n in names:
        try:
            source_id(n)
        except ValueError:
            raise ValueError('List of names containing an invalid name:'
                             ' %s' % n)
    return names


def namelists(value):
    """
    :param value: input string
    :returns: list of lists of identifiers

    >>> namelists('a,b')
    [['a', 'b']]
    >>> namelists('a1, b_2; _c')
    [['a1', 'b_2'], ['_c']]

    >>> namelists('a1; b_2; 1c')
    [['a1'], ['b_2'], ['1c']]
    """
    lists = []
    for string in value.split(';'):
        names = string.replace(',', ' ').split()
        for n in names:
            try:
                source_id(n)
            except ValueError:
                raise ValueError('Invalid name: %s' % n)
        lists.append(names)
    return lists


def float_(value):
    """
    :param value: input string
    :returns: a floating point number
    """
    try:
        return float(value)
    except Exception:
        raise ValueError("'%s' is not a float" % value)


def nonzero(value):
    """
    :param value: input string
    :returns: the value unchanged

    >>> nonzero('1')
    '1'
    >>> nonzero('0')
    Traceback (most recent call last):
      ...
    ValueError: '0' is zero
    """
    if float_(value) == 0:
        raise ValueError("'%s' is zero" % value)
    return value


# NB: numpy.round != round; for instance numpy.round(123.300795, 5)
# is 123.30080, different from round(123.300795, 5) = 123.30079
def longitude(value):
    """
    :param value: input string
    :returns: longitude float, rounded to 5 digits, i.e. 1 meter maximum

    >>> longitude('0.123456')
    0.12346
    """
    lon = round(float_(value), 5)
    if lon > 180.:
        raise ValueError('longitude %s > 180' % lon)
    elif lon < -180.:
        raise ValueError('longitude %s < -180' % lon)
    return lon


# NB: numpy.round != round; for instance numpy.round(123.300795, 5)
# is 123.30080, different from round(123.300795, 5) = 123.30079
def latitude(value):
    """
    :param value: input string
    :returns: latitude float, rounded to 5 digits, i.e. 1 meter maximum

    >>> latitude('-0.123456')
    -0.12346
    """
    lat = round(float_(value), 5)
    if lat > 90.:
        raise ValueError('latitude %s > 90' % lat)
    elif lat < -90.:
        raise ValueError('latitude %s < -90' % lat)
    return lat


def longitudes(value):
    """
    :param value: a comma separated string of longitudes
    :returns: a list of longitudes
    """
    return [longitude(v) for v in value.split(',')]


def latitudes(value):
    """
    :param value: a comma separated string of latitudes
    :returns: a list of latitudes
    """
    return [latitude(v) for v in value.split(',')]


depth = float_


def lon_lat(value):
    """
    :param value: a pair of coordinates
    :returns: a tuple (longitude, latitude)

    >>> lon_lat('12 14')
    (12.0, 14.0)
    >>> lon_lat('12,14')
    (12.0, 14.0)
    """
    lon, lat = value.replace(',', ' ').split()
    return longitude(lon), latitude(lat)


def point(value):
    """
    :param value: a tuple of coordinates as a string (2D or 3D)
    :returns: a tuple of coordinates as a string (2D or 3D)
    """
    lst = value.split()
    dim = len(lst)
    if dim == 2:
        return longitude(lst[0]), latitude(lst[1]), 0.
    elif dim == 3:
        return longitude(lst[0]), latitude(lst[1]), depth(lst[2])
    else:
        raise ValueError('Invalid point format: %s' % value)


def coordinates(value):
    """
    Convert a non-empty string into a list of lon-lat coordinates.

    >>> coordinates('')
    Traceback (most recent call last):
    ...
    ValueError: Empty list of coordinates: ''
    >>> coordinates('1.1 1.2')
    [(1.1, 1.2, 0.0)]
    >>> coordinates('1.1 1.2, 2.2 2.3')
    [(1.1, 1.2, 0.0), (2.2, 2.3, 0.0)]
    >>> coordinates('1.1 1.2 -0.4, 2.2 2.3 -0.5')
    [(1.1, 1.2, -0.4), (2.2, 2.3, -0.5)]
    >>> coordinates('0 0 0, 0 0 -1')
    Traceback (most recent call last):
    ...
    ValueError: Found overlapping site #2,  0 0 -1
    """
    if isinstance(value, list):  # assume list of lists/tuples
        return [point(' '.join(map(str, v))) for v in value]
    if not value.strip():
        raise ValueError('Empty list of coordinates: %r' % value)
    points = []
    pointset = set()
    for i, line in enumerate(value.split(','), 1):
        pnt = point(line)
        if pnt[:2] in pointset:
            raise ValueError("Found overlapping site #%d, %s" % (i, line))
        pointset.add(pnt[:2])
        points.append(pnt)
    return points


def wkt_polygon(value):
    """
    Convert a string with a comma separated list of coordinates into
    a WKT polygon, by closing the ring.
    """
    points = ['%s %s' % (lon, lat) for lon, lat, dep in coordinates(value)]
    # close the linear polygon ring by appending the first coord to the end
    points.append(points[0])
    return 'POLYGON((%s))' % ', '.join(points)


def positiveint(value):
    """
    :param value: input string
    :returns: positive integer
    """
    val = str(value).lower()
    if val == 'true':
        return 1
    elif val == 'false':
        return 0
    i = int(not_empty(val))
    if i < 0:
        raise ValueError('integer %d < 0' % i)
    return i


def positivefloat(value):
    """
    :param value: input string
    :returns: positive float
    """
    f = float(not_empty(value))
    if f < 0:
        raise ValueError('float %s < 0' % f)
    return f


def positivefloats(value):
    """
    :param value:
        string of whitespace separated floats
    :returns:
        a list of positive floats
    """
    values = value.strip('[]').split()
    floats = list(map(positivefloat, values))
    return floats


def positivefloatorsentinel(value):
    """
    :param value: input string
    :returns: positive float or -999 (sentinel)
    """
    f = float(not_empty(value))
    if f < 0 and f!= -999:
        msg = 'float %s < 0 or not equal to -999' % f
        raise ValueError(msg)
    return f


def positivefloatsorsentinels(value):
    """
    :param value:
        string of whitespace separated floats
    :returns:
        a list of positive floats or -999 (sentinel) values
    """
    values = value.strip('[]').split()
    floats = list(map(positivefloatorsentinel, values))
    return floats


def floats(value):
    """
    :param value:
        string of whitespace separated floats
    :returns:
        a list of floats
    """
    return list(map(float, value.split()))


_BOOL_DICT = {
    '': False,
    '0': False,
    '1': True,
    'false': False,
    'true': True,
}


def boolean(value):
    """
    :param value: input string such as '0', '1', 'true', 'false'
    :returns: boolean

    >>> boolean('')
    False
    >>> boolean('True')
    True
    >>> boolean('false')
    False
    >>> boolean('t')
    Traceback (most recent call last):
        ...
    ValueError: Not a boolean: t
    """
    value = str(value).strip().lower()
    try:
        return _BOOL_DICT[value]
    except KeyError:
        raise ValueError('Not a boolean: %s' % value)


def range01(value):
    """
    :param value: a string convertible to a float in the range 0..1
    """
    val = value.lower()
    if val == 'true':
        return 1.
    elif val == 'false':
        return 0.
    return FloatRange(0, 1)(val)


probability = FloatRange(0, 1)


def probabilities(value, rows=0, cols=0):
    """
    :param value: input string, comma separated or space separated
    :param rows: the number of rows if the floats are in a matrix (0 otherwise)
    :param cols: the number of columns if the floats are in a matrix (or 0
    :returns: a list of probabilities

    >>> probabilities('')
    []
    >>> probabilities('1')
    [1.0]
    >>> probabilities('0.1 0.2')
    [0.1, 0.2]
    >>> probabilities('[0.1, 0.2]')  # commas and brackets are ignored
    [0.1, 0.2]
    """
    val = value.replace('[', '').replace(']', '').replace(',', ' ')
    probs = list(map(probability, val.split()))
    if rows and cols:
        probs = numpy.array(probs).reshape((len(rows), len(cols)))
    return probs


def decreasing_probabilities(value):
    """
    :param value: input string, comma separated or space separated
    :returns: a list of decreasing probabilities

    >>> decreasing_probabilities('1')
    Traceback (most recent call last):
    ...
    ValueError: Not enough probabilities, found '1'
    >>> decreasing_probabilities('0.2 0.1')
    [0.2, 0.1]
    >>> decreasing_probabilities('0.1 0.2')
    Traceback (most recent call last):
    ...
    ValueError: The probabilities 0.1 0.2 are not in decreasing order
    """
    probs = probabilities(value)
    if len(probs) < 2:
        raise ValueError('Not enough probabilities, found %r' % value)
    elif sorted(probs, reverse=True) != probs:
        raise ValueError('The probabilities %s are not in decreasing order'
                         % value)
    return probs


def intensity_measure_type(value):
    """
    Make sure `value` is a valid intensity measure type and return it
    in a normalized form

    >>> intensity_measure_type('SA(0.10)')  # NB: strips the trailing 0
    'SA(0.1)'
    >>> intensity_measure_type('SA')  # this is invalid
    Traceback (most recent call last):
      ...
    ValueError: Invalid IMT: 'SA'
    """
    try:
        return str(imt.from_string(value))
    except Exception:
        raise ValueError("Invalid IMT: '%s'" % value)


def intensity_measure_types(value):
    """
    :param value: input string
    :returns: non-empty list of ordered Intensity Measure Type objects

    >>> intensity_measure_types('')
    []
    >>> intensity_measure_types('PGA')
    ['PGA']
    >>> intensity_measure_types('PGA, SA(1.00)')
    ['PGA', 'SA(1.0)']
    >>> intensity_measure_types('SA(0.1), SA(0.10)')
    Traceback (most recent call last):
      ...
    ValueError: Duplicated IMTs in SA(0.1), SA(0.10)
    >>> intensity_measure_types('PGV, SA(1), PGA')
    ['PGV', 'PGA', 'SA(1.0)']
    """
    if not value:
        return []
    imts = []
    for chunk in value.split(','):
        imts.append(imt.from_string(chunk.strip()))
    sorted_imts = sorted(imts, key=lambda im: getattr(im, 'period', 1))
    if len(distinct(imts)) < len(imts):
        raise ValueError('Duplicated IMTs in %s' % value)
    return [str(imt) for imt in sorted_imts]


def check_levels(imls, imt, min_iml=1E-10):
    """
    Raise a ValueError if the given levels are invalid.

    :param imls: a list of intensity measure and levels
    :param imt: the intensity measure type
    :param min_iml: minimum intensity measure level (default 1E-10)

    >>> check_levels([0.1, 0.2], 'PGA')  # ok
    >>> check_levels([], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: No imls for PGA: []
    >>> check_levels([0.2, 0.1], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: The imls for PGA are not sorted: [0.2, 0.1]
    >>> check_levels([0.2, 0.2], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: Found duplicated levels for PGA: [0.2, 0.2]
    """
    if imls == [0]:  # corresponds to intensity_measure_levels
        return
    if len(imls) < 1:
        raise ValueError('No imls for %s: %s' % (imt, imls))
    elif imls != sorted(imls):
        raise ValueError('The imls for %s are not sorted: %s' % (imt, imls))
    elif len(distinct(imls)) < len(imls):
        raise ValueError("Found duplicated levels for %s: %s" % (imt, imls))
    elif imls[0] == 0 and imls[1] <= min_iml:  # apply the cutoff
        raise ValueError("The min_iml %s=%s is larger than the second level "
                         "for %s" % (imt, min_iml, imls))
    elif imls[0] == 0 and imls[1] > min_iml:  # apply the cutoff
        imls[0] = min_iml


def intensity_measure_types_and_levels(value):
    """
    :param value: input string
    :returns: Intensity Measure Type and Levels dictionary

    >>> intensity_measure_types_and_levels('{"SA(0.10)": [0.1, 0.2]}')
    {'SA(0.1)': [0.1, 0.2]}
    """
    dic = dictionary(value)
    for imt_str, imls in list(dic.items()):
        norm_imt = str(imt.from_string(imt_str))
        if norm_imt != imt_str:
            dic[norm_imt] = imls
            del dic[imt_str]
        check_levels(imls, imt_str)  # ValueError if the levels are invalid
    return dic


def loss_ratios(value):
    """
    :param value: input string
    :returns: dictionary loss_type -> loss ratios

    >>> loss_ratios('{"structural": [0.1, 0.2]}')
    {'structural': [0.1, 0.2]}
    """
    dic = dictionary(value)
    for lt, ratios in dic.items():
        for ratio in ratios:
            if not 0 <= ratio <= 1:
                raise ValueError('Loss ratio %f for loss_type %s is not in '
                                 'the range [0, 1]' % (ratio, lt))
        check_levels(ratios, lt)  # ValueError if the levels are invalid
    return dic


def logscale(x_min, x_max, n):
    """
    :param x_min: minumum value
    :param x_max: maximum value
    :param n: number of steps
    :returns: an array of n values from x_min to x_max
    """
    if not (isinstance(n, int) and n > 0):
        raise ValueError('n must be a positive integer, got %s' % n)
    if x_min <= 0:
        raise ValueError('x_min must be positive, got %s' % x_min)
    if x_max <= x_min:
        raise ValueError('x_max (%s) must be bigger than x_min (%s)' %
                         (x_max, x_min))
    delta = numpy.log(x_max / x_min)
    return numpy.exp(delta * numpy.arange(n) / (n - 1)) * x_min


def linscale(x_min, x_max, n):
    """
    :param x_min: minumum value
    :param x_max: maximum value
    :param n: number of steps
    :returns: an array of n values from x_min to x_max
    """
    if not (isinstance(n, int) and n > 0):
        raise ValueError('n must be a positive integer, got %s' % n)
    if x_min <= 0:
        raise ValueError('x_min must be positive, got %s' % x_min)
    if x_max <= x_min:
        raise ValueError('x_max (%s) must be bigger than x_min (%s)' %
                         (x_max, x_min))
    return numpy.linspace(x_min, x_max, num=n)


def dictionary(value):
    """
    :param value:
        input string corresponding to a literal Python object
    :returns:
        the Python object

    >>> dictionary('')
    {}
    >>> dictionary('{}')
    {}
    >>> dictionary('{"a": 1}')
    {'a': 1}
    >>> dictionary('"vs30_clustering: true"')  # an error really done by a user
    Traceback (most recent call last):
       ...
    ValueError: '"vs30_clustering: true"' is not a valid Python dictionary
    >>> numpy.array(dictionary('{"ls": logscale(0.01, 2, 5)}')['ls'])
    array([0.01      , 0.03760603, 0.14142136, 0.53182959, 2.        ])
    """
    if not value:
        return {}

    if 'logscale' in value:
        value = value.replace('logscale(', '("logscale", ')  # dirty but quick
    if 'linscale' in value:
        value = value.replace('linscale(', '("linscale", ')  # dirty but quick

    try:
        dic = dict(ast.literal_eval(value))
    except Exception:
        raise ValueError('%r is not a valid Python dictionary' % value)

    for key, val in dic.items():
        if isinstance(val, tuple):
            if val[0] == 'logscale':
                dic[key] = list(logscale(*val[1:]))
            elif val[0] == 'linscale':
                dic[key] = list(linscale(*val[1:]))
    return dic


def uint8dict(value):
    """
    :param value:
        input string corresponding to a literal Python dictionary
    :returns:
        dictionary string -> uint8 number

    >>> uint8dict('')
    {}
    >>> uint8dict('{}')
    {}
    >>> uint8dict('{"a": 1}')
    {'a': 1}
    >>> uint8dict('{"a": 0}')
    Traceback (most recent call last):
       ...
    AssertionError: a must be in the range 1-255, got 0
    """
    if not value:
        return {}
    try:
        dic = dict(ast.literal_eval(value))
    except Exception:
        raise ValueError('%r is not a valid Python dictionary' % value)

    for key, val in dic.items():
        assert isinstance(val, int), f'{key} must be integer, got {val}'
        assert 0 < val < 256, f'{key} must be in the range 1-255, got {val}'
    return dic


def list_of_dict(value):
    """
    :param value:
        input string corresponding to a list of literal Python dictionaries
    :returns:
        the list
    """
    return json.loads(value)


# ########################### SOURCES/RUPTURES ############################# #

def mag_scale_rel(value):
    """
    :param value:
        a Magnitude-Scale relationship in hazardlib
    :returns:
        the corresponding hazardlib object

    Parametric MSR classes are supported with TOML syntax; for instance

    >>> mag_scale_rel("CScalingMSR.C=4.7")
    <CScalingMSR>
    """
    value = value.strip()
    if '.' in value or '[' in value:
        [(value, kwargs)] = toml.loads(value).items()
    else:
        kwargs = {}
    if value not in SCALEREL:
        raise ValueError(
            "'%s' is not a recognized magnitude-scale relationship" % value)
    return SCALEREL[value](**kwargs)


def pmf(value):
    """
    Comvert a string into a Probability Mass Function.

    :param value:
        a sequence of probabilities summing up to 1 (no commas)
    :returns:
        a list of pairs [(probability, index), ...] with index starting from 0

    >>> pmf("0.157 0.843")
    [(0.157, 0), (0.843, 1)]
    """
    probs = probabilities(value)
    if sum(probs) != 1:
        # avoid https://github.com/gem/oq-engine/issues/5901
        raise ValueError('The probabilities %s do not sum up to 1!' % value)
    return [(p, i) for i, p in enumerate(probs)]


def check_weights(nodes_with_a_weight):
    """
    Ensure that the sum of the values is 1

    :param nodes_with_a_weight: a list of Node objects with a weight attribute
    """
    weights = [n['weight'] for n in nodes_with_a_weight]
    if abs(sum(weights) - 1.) > PRECISION:
        raise ValueError('The weights do not sum up to 1: %s' % weights)
    return nodes_with_a_weight


def weights(value):
    """
    Space-separated list of weights:

    >>> weights('0.1 0.2 0.7')
    [0.1, 0.2, 0.7]

    >>> weights('0.1 0.2 0.8')
    Traceback (most recent call last):
      ...
    ValueError: The weights do not sum up to 1: [0.1, 0.2, 0.8]
    """
    probs = probabilities(value)
    if abs(sum(probs) - 1.) > PRECISION:
        raise ValueError('The weights do not sum up to 1: %s' % probs)
    return probs


def hypo_list(nodes):
    """
    :param nodes: a hypoList node with N hypocenter nodes
    :returns: a numpy array of shape (N, 3) with strike, dip and weight
    """
    check_weights(nodes)
    data = []
    for node in nodes:
        data.append([node['alongStrike'], node['downDip'], node['weight']])
    return numpy.array(data, float)


def slip_list(nodes):
    """
    :param nodes: a slipList node with N slip nodes
    :returns: a numpy array of shape (N, 2) with slip angle and weight
    """
    check_weights(nodes)
    data = []
    for node in nodes:
        data.append([slip_range(~node), node['weight']])
    return numpy.array(data, float)


def posList(value):
    """
    :param value:
        a string with the form `lon1 lat1 [depth1] ...  lonN latN [depthN]`
        without commas, where the depts are optional.
    :returns:
        a list of floats without other validations
    """
    values = value.split()
    num_values = len(values)
    if num_values % 3 and num_values % 2:
        raise ValueError('Wrong number: nor pairs not triplets: %s' % values)
    try:
        return list(map(float_, values))
    except Exception as exc:
        raise ValueError('Found a non-float in %s: %s' % (value, exc))


def point3d(value, lon, lat, depth):
    """
    This is used to convert nodes of the form
    <hypocenter lon="LON" lat="LAT" depth="DEPTH"/>

    :param value: None
    :param lon: longitude string
    :param lat: latitude string
    :returns: a validated triple (lon, lat, depth)
    """
    return longitude(lon), latitude(lat), positivefloat(depth)


strike_range = FloatRange(0, 360, 'strike')
slip_range = FloatRange(0, 360, 'slip')
dip_range = FloatRange(0, 90, 'dip')
rake_range = FloatRange(-180, 180, 'rake', 'undefined')


def ab_values(value):
    """
    a and b values of the GR magniture-scaling relation.
    a is a positive float, b is just a float.
    """
    a, b = value.split()
    return positivefloat(a), float_(b)


def integers(value):
    """
    :param value: input string
    :returns: non-empty list of integers

    >>> integers('1, 2')
    [1, 2]
    >>> integers(' ')
    Traceback (most recent call last):
       ...
    ValueError: Not a list of integers: ' '
    """
    if '.' in value:
        raise ValueError('There are decimal points in %s' % value)
    values = value.strip('[]').replace(',', ' ').split()
    if not values:
        raise ValueError('Not a list of integers: %r' % value)
    try:
        ints = [int(float(v)) for v in values]
    except Exception:
        raise ValueError('Not a list of integers: %r' % value)
    return ints


def positiveints(value):
    """
    >>> positiveints('1, -1')
    Traceback (most recent call last):
       ...
    ValueError: -1 is negative in '1, -1'
    """
    ints = integers(value)
    for val in ints:
        if val < 0:
            raise ValueError('%d is negative in %r' % (val, value))
    return ints


def indexes(value):
    """
    >>> indexes("1,2,A")
    ('1', '2', 'A')
    """
    return tuple(value.split(','))


def tile_spec(value):
    """
    Specify a tile with a string of format "no:nt"
    where `no` is an integer in the range `1..nt` and `nt`
    is the total number of tiles.

    >>> tile_spec('[1,2]')
    [1, 2]
    >>> tile_spec('[2,2]')
    [2, 2]
    """
    no, ntiles = ast.literal_eval(value)
    assert ntiles > 0, ntiles
    assert no > 0 and no <= ntiles, no
    return [no, ntiles]


def simple_slice(value):
    """
    >>> simple_slice('2:5')
    (2, 5)
    >>> simple_slice('0:None')
    (0, None)
    """
    try:
        start, stop = value.split(':')
        start = ast.literal_eval(start)
        stop = ast.literal_eval(stop)
        if start is not None and stop is not None:
            assert start < stop
    except Exception:
        raise ValueError('invalid slice: %s' % value)
    return (start, stop)


def uncertainty_model(value):
    """
    Format whitespace in XML nodes of kind uncertaintyModel
    """
    if value.lstrip().startswith('['):  # TOML, do not mess with newlines
        return value.strip()
    return ' '.join(value.split())  # remove newlines too


def host_port(value=None):
    """
    Returns a pair (host_IP, port_number).

    >>> host_port('localhost:1908')
    ('127.0.0.1', 1908)

    If value is missing returns the parameters in openquake.cfg
    """
    if not value:
        host = os.environ.get('OQ_DATABASE', config.dbserver.host)
        return (host, config.dbserver.port)
    host, port = value.split(':')
    return socket.gethostbyname(host), int(port)


# used for the exposure validation
cost_type_type = Choice('aggregated', 'per_area', 'per_asset')


def site_param(dic):
    """
    Convert a dictionary site_model_param -> string into a dictionary
    of valid casted site parameters.
    """
    new = {}
    for name, val in dic.items():
        if name == 'vs30Type':
            # avoid "Unrecognized parameter vs30Type"
            new['vs30measured'] = val == 'measured'
        elif name not in site.site_param_dt:
            raise ValueError('Unrecognized parameter %s' % name)
        else:
            new[name] = val
    return new


def version(value: str):
    """
    >>> version('3.22')
    (3, 22, 0)
    >>> version('3.22.0-gitXXX')
    (3, 22, 0)
    """
    vers = [0, 0, 0]
    for i, number in enumerate(value.split('.')):
        if 'git' not in number:
            vers[i] = int(number)
    return tuple(vers)


def secondary_perils(value: str):
    """
    >>> secondary_perils("Jibson2007ALandslides, AllstadtEtAl2022Liquefaction")
    ['Jibson2007ALandslides', 'AllstadtEtAl2022Liquefaction']
    """
    clsnames = namelist(value)
    out = []
    for name in clsnames:
        if name in RENAMED_SEPS:
            raise ValueError(
                f'{name} has been replaced with {RENAMED_SEPS[name]}')
        out.append(getattr(classes, name).__name__)
    return out


###########################################################################

class Param(object):
    """
    A descriptor for validated parameters with a default, to be
    used as attributes in ParamSet objects.

    :param validator: the validator
    :param default: the default value
    """
    NODEFAULT = object()

    def __init__(self, validator, default=NODEFAULT, name=None):
        if not callable(validator):
            raise ValueError(
                '%r for %s is not a validator: it is not callable'
                % (validator, name))
        if not hasattr(validator, '__name__'):
            raise ValueError(
                '%r for %s is not a validator: it has no __name__'
                % (validator, name))

        self.validator = validator
        self.default = default
        self.name = name  # set by ParamSet.__metaclass__

    def __get__(self, obj, objclass):
        if obj is not None:
            if self.default is self.NODEFAULT:
                raise AttributeError(self.name)
            return self.default
        return self


class MetaParamSet(type):
    """
    Set the `.name` attribute of every Param instance defined inside
    any subclass of ParamSet.
    """
    def __init__(cls, name, bases, dic):
        for name, val in dic.items():
            if isinstance(val, Param):
                val.name = name


# used in commonlib.oqvalidation
class ParamSet(metaclass=MetaParamSet):
    """
    A set of valid interrelated parameters. Here is an example
    of usage:

    >>> class MyParams(ParamSet):
    ...     a = Param(positiveint)
    ...     b = Param(positivefloat)
    ...
    ...     def is_valid_not_too_big(self):
    ...         "The sum of a and b must be under 10: a={a} and b={b}"
    ...         return self.a + self.b < 10

    >>> mp = MyParams(a='1', b='7.2')
    >>> mp
    <MyParams a=1, b=7.2>

    >>> MyParams(a='1', b='9.2').validate()
    Traceback (most recent call last):
    ...
    ValueError: The sum of a and b must be under 10: a=1 and b=9.2

    The constrains are applied in lexicographic order. The attribute
    corresponding to a Param descriptor can be set as usual:

    >>> mp.a = '2'
    >>> mp.a
    '2'

    A list with the literal strings can be extracted as follows:

    >>> mp.to_params()
    [('a', "'2'"), ('b', '7.2')]

    It is possible to build a new object from a dictionary of parameters
    which are assumed to be already validated:

    >>> MyParams.from_(dict(a="'2'", b='7.2'))
    <MyParams a='2', b=7.2>
    """
    params = {}
    KNOWN_INPUTS = {}

    @classmethod
    def check(cls, dic):
        """
        Check if a dictionary name->string can be converted into a dictionary
        name->value. If the name does not correspond to a known parameter,
        print a warning.

        :returns: a dictionary of converted parameters
        """
        out = {}
        for name, text in dic.items():
            try:
                p = getattr(cls, name)
            except AttributeError:
                logging.warning('Ignored unknown parameter %s', name)
            else:
                out[name] = p.validator(text)
        return out

    @classmethod
    def from_(cls, dic):
        """
        Build a new ParamSet from a dictionary of string-valued parameters
        which are assumed to be already valid.
        """
        self = cls.__new__(cls)
        for k, v in dic.items():
            setattr(self, k, ast.literal_eval(v))
        return self

    def to_params(self):
        """
        Convert the instance dictionary into a sorted list of pairs
        (name, valrepr) where valrepr is the string representation of
        the underlying value.
        """
        dic = self.__dict__
        return [(k, repr(dic[k])) for k in sorted(dic)
                if not k.startswith('_')]

    def __init__(self, **names_vals):
        for name, val in names_vals.items():
            if name.startswith(('_', 'is_valid_')):
                raise NameError('The parameter name %s is not acceptable'
                                % name)
            try:
                convert = getattr(self.__class__, name).validator
            except AttributeError:
                if name not in self.KNOWN_INPUTS:
                    logging.warning(
                        "The parameter '%s' is unknown, ignoring" % name)
                continue
            try:
                value = convert(val)
            except Exception as exc:
                raise ValueError('%s: could not convert to %s: %s=%s'
                                 % (exc, convert.__name__, name, val))
            setattr(self, name, value)

    def validate(self):
        """
        Apply the `is_valid` methods to self and possibly raise a ValueError.
        """
        # it is important to have the validator applied in a fixed order
        valids = [getattr(self, valid)
                  for valid in sorted(dir(self.__class__))
                  if valid.startswith('is_valid_')]
        for is_valid in valids:
            if not is_valid():
                docstring = '\n'.join(
                    line.strip() for line in is_valid.__doc__.splitlines())
                doc = docstring.format(**vars(self))
                raise ValueError(doc)

    def json(self):
        """
        :returns: the parameters as a JSON string
        """
        dic = {k: _fix_toml(v)
               for k, v in self.__dict__.items() if not k.startswith('_')}
        return json.dumps(dic)

    def __iter__(self):
        for item in sorted(vars(self).items()):
            yield item

    def __repr__(self):
        names = sorted(n for n in vars(self) if not n.startswith('_'))
        nameval = ', '.join('%s=%r' % (n, getattr(self, n)) for n in names)
        return '<%s %s>' % (self.__class__.__name__, nameval)


class RjbEquivalent(object):
    """
    A class to compute the equivalent Rjb distance. Usage:

    >> reqv = RjbEquivalent('lookup.hdf5')
    >> reqv.get(repi_distances, mag)
    """
    def __init__(self, filename):
        with hdf5.File(filename, 'r') as f:
            self.repi = f['default/repi'][()]  # shape D
            self.mags = f['default/mags'][()]  # shape M
            self.reqv = f['default/reqv'][()]  # shape D x M

    def get(self, repi, mag):
        """
        :param repi: an array of epicentral distances in the range self.repi
        :param mag: a magnitude in the range self.mags
        :returns: an array of equivalent distances
        """
        mag_idx = numpy.abs(mag - self.mags).argmin()
        dists = []
        for dist in repi:
            repi_idx = numpy.abs(dist - self.repi).argmin()
            dists.append(self.reqv[repi_idx, mag_idx])
        return numpy.array(dists)


def basename(src, splitchars='.:'):
    """
    :returns: the base name of a split source

    >>> basename('SC:10;0')
    'SC;0'
    """
    src_id = src if isinstance(src, str) else src.source_id
    for char in splitchars:
        src_id = re.sub(r'\%s\d+' % char, '', src_id)
    return src_id


def corename(src):
    """
    :param src: source object or source name
    :returns: the core name of a source
    """
    src = src if isinstance(src, str) else src.source_id
    # @ section of multifault source
    # ! source model logic tree branch
    # : component of mutex source
    # ; alternate logictree version of a source
    # . component of split source
    return re.split('[!:;.]', src)[0]


def fragmentno(src):
    "Postfix after :.; as an integer"
    # in disagg/case-12 one has source IDs like 'SL_kerton:665!b16'
    fragments = re.split('[:.;]', src.source_id)
    if len(fragments) == 1:  # no fragment number, like in AELO for NZL
        return -1
    fragment = fragments[1].split('!')[0]  # strip !b16
    return int(fragment)
