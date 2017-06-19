# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

import re
import ast
import logging
import textwrap
import collections
from decimal import Decimal
import numpy

from openquake.baselib.python3compat import with_metaclass
from openquake.baselib.general import distinct
from openquake.baselib import hdf5
from openquake.hazardlib import imt, scalerel, gsim
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.calc.filters import IntegrationDistance

SCALEREL = scalerel.get_available_magnitude_scalerel()

GSIM = gsim.get_available_gsims()

disagg_outs = ['_'.join(tup) for tup in sorted(disagg.pmf_map)]


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
        if val not in disagg_outs:
            raise ValueError('Invalid disagg output: %s' % val)
    return values


# more tests are in tests/valid_test.py
def gsim(value, **kwargs):
    """
    Make sure the given value is the name of an available GSIM class.

    >>> gsim('BooreAtkinson2011')
    'BooreAtkinson2011()'
    """
    if value == 'FromFile':
        return 'FromFile'
    elif value.endswith('()'):
        value = value[:-2]  # strip parenthesis
    try:
        gsim_class = GSIM[value]
    except KeyError:
        raise ValueError('Unknown GSIM: %s' % value)
    try:
        return gsim_class(**kwargs)
    except TypeError:
        raise ValueError('Could not instantiate %s%s' % (value, kwargs))


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

export_formats = Choices('', 'xml', 'geojson', 'txt', 'csv', 'npz')


def hazard_id(value):
    """
    >>> hazard_id('')
    ()
    >>> hazard_id('-1')
    (-1,)
    >>> hazard_id('42')
    (42,)
    >>> hazard_id('42,3')
    (42, 3)
    >>> hazard_id('42,3,4')
    (42, 3, 4)
    >>> hazard_id('42:3')
    Traceback (most recent call last):
       ...
    ValueError: Invalid hazard_id '42:3'
    """
    if not value:
        return ()
    try:
        return tuple(map(int, value.split(',')))
    except:
        raise ValueError('Invalid hazard_id %r' % value)


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


class SimpleId(object):
    """
    Check if the given value is a valid ID.

    :param length: maximum length of the ID
    :param regex: accepted characters
    """
    def __init__(self, length, regex=r'^[\w_\-]+$'):
        self.length = length
        self.regex = regex
        self.__name__ = 'SimpleId(%d, %s)' % (length, regex)

    def __call__(self, value):
        if max(map(ord, value)) > 127:
            raise ValueError(
                'Invalid ID %r: the only accepted chars are a-zA-Z0-9_-'
                % value)
        elif len(value) > self.length:
            raise ValueError("The ID '%s' is longer than %d character" %
                             (value, self.length))
        elif re.match(self.regex, value):
            return value
        raise ValueError(
            "Invalid ID '%s': the only accepted chars are a-zA-Z0-9_-" % value)

MAX_ID_LENGTH = 60
ASSET_ID_LENGTH = 100

simple_id = SimpleId(MAX_ID_LENGTH)
asset_id = SimpleId(ASSET_ID_LENGTH)
source_id = SimpleId(MAX_ID_LENGTH, r'^[\w\.\-_]+$')


class FloatRange(object):
    def __init__(self, minrange, maxrange):
        self.minrange = minrange
        self.maxrange = maxrange
        self.__name__ = 'FloatRange[%s:%s]' % (minrange, maxrange)

    def __call__(self, value):
        f = float_(value)
        if f > self.maxrange:
            raise ValueError("'%s' is bigger than the max, '%s'" %
                             (f, self.maxrange))
        if f < self.minrange:
            raise ValueError("'%s' is smaller than the min, '%s'" %
                             (f, self.minrange))
        return f


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
    except:
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
    Traceback (most recent call last):
        ...
    ValueError: List of names containing an invalid name: 1c
    """
    names = value.replace(',', ' ').split()
    for n in names:
        try:
            name(n)
        except ValueError:
            raise ValueError('List of names containing an invalid name:'
                             ' %s' % n)
    return names


def float_(value):
    """
    :param value: input string
    :returns: a floating point number
    """
    try:
        return float(value)
    except:
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
    """
    lon, lat = value.split()
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
    ValueError: There are overlapping points in 0 0 0, 0 0 -1
    """
    if not value.strip():
        raise ValueError('Empty list of coordinates: %r' % value)
    points = list(map(point, value.split(',')))
    num_distinct = len(set(pnt[:2] for pnt in points))
    if num_distinct < len(points):
        raise ValueError("There are overlapping points in %s" % value)
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
    i = int(not_empty(value))
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
    floats = list(map(positivefloat, value.split()))
    return floats


def floats32(value):
    """
    :param value:
        string of whitespace separated floats
    :returns:
        an array of 32 bit floats
    """
    return numpy.float32(value.split())


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
    value = value.strip().lower()
    try:
        return _BOOL_DICT[value]
    except KeyError:
        raise ValueError('Not a boolean: %s' % value)


range01 = FloatRange(0, 1)
probability = FloatRange(0, 1)
probability.__name__ = 'probability'


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
    >>> probabilities('0.1, 0.2')  # commas are ignored
    [0.1, 0.2]
    """
    probs = list(map(probability, value.replace(',', ' ').split()))
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
    except:
        raise ValueError("Invalid IMT: '%s'" % value)


def intensity_measure_types(value):
    """
    :param value: input string
    :returns: non-empty list of Intensity Measure Type objects

    >>> intensity_measure_types('PGA')
    ['PGA']
    >>> intensity_measure_types('PGA, SA(1.00)')
    ['PGA', 'SA(1.0)']
    >>> intensity_measure_types('SA(0.1), SA(0.10)')
    Traceback (most recent call last):
      ...
    ValueError: Duplicated IMTs in SA(0.1), SA(0.10)
    """
    imts = []
    for chunk in value.split(','):
        imts.append(str(imt.from_string(chunk.strip())))
    if len(distinct(imts)) < len(imts):
        raise ValueError('Duplicated IMTs in %s' % value)
    return imts


def check_levels(imls, imt):
    """
    Raise a ValueError if the given levels are invalid.

    :param imls: a list of intensity measure and levels
    :param imt: the intensity measure type

    >>> check_levels([0.1, 0.2], 'PGA')  # ok
    >>> check_levels([0.1], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: Not enough imls for PGA: [0.1]
    >>> check_levels([0.2, 0.1], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: The imls for PGA are not sorted: [0.2, 0.1]
    >>> check_levels([0.2, 0.2], 'PGA')
    Traceback (most recent call last):
       ...
    ValueError: Found duplicated levels for PGA: [0.2, 0.2]
    """
    if len(imls) < 2:
        raise ValueError('Not enough imls for %s: %s' % (imt, imls))
    elif imls != sorted(imls):
        raise ValueError('The imls for %s are not sorted: %s' % (imt, imls))
    elif len(distinct(imls)) < len(imls):
        raise ValueError("Found duplicated levels for %s: %s" % (imt, imls))


def intensity_measure_types_and_levels(value):
    """
    :param value: input string
    :returns: Intensity Measure Type and Levels dictionary

    >>> intensity_measure_types_and_levels('{"SA(0.10)": [0.1, 0.2]}')
    {'SA(0.1)': [0.1, 0.2]}
    """
    dic = dictionary(value)
    for imt_str, imls in dic.items():
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
    >>> dictionary('{"ls": logscale(0.01, 2, 5)}')
    {'ls': [0.01, 0.037606030930863933, 0.14142135623730948, 0.53182958969449856, 1.9999999999999991]}
    """
    if not value:
        return {}
    value = value.replace('logscale(', '("logscale", ')  # dirty but quick
    try:
        dic = dict(ast.literal_eval(value))
    except:
        raise ValueError('%r is not a valid Python dictionary' % value)
    for key, val in dic.items():
        try:
            has_logscale = (val[0] == 'logscale')
        except:  # no val[0]
            continue
        if has_logscale:
            dic[key] = list(logscale(*val[1:]))
    return dic


# used for the maximum distance parameter in the job.ini file
def floatdict(value):
    """
    :param value:
        input string corresponding to a literal Python number or dictionary
    :returns:
        a Python dictionary key -> number

    >>> floatdict("200")
    {'default': 200}

    >>> text = "{'active shallow crust': 250., 'default': 200}"
    >>> sorted(floatdict(text).items())
    [('active shallow crust', 250.0), ('default', 200)]
    """
    value = ast.literal_eval(value)
    if isinstance(value, (int, float, list)):
        return {'default': value}
    return value


def maximum_distance(value):
    """
    :param value:
        input string corresponding to a valid maximum distance
    :returns:
        a IntegrationDistance mapping
    """
    return IntegrationDistance(floatdict(value))


# ########################### SOURCES/RUPTURES ############################# #

def mag_scale_rel(value):
    """
    :param value:
        name of a Magnitude-Scale relationship in hazardlib
    :returns:
        the corresponding hazardlib object
    """
    value = value.strip()
    if value not in SCALEREL:
        raise ValueError(
            "'%s' is not a recognized magnitude-scale relationship" % value)
    return value


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
    if sum(map(Decimal, value.split())) != 1:
        raise ValueError('The probabilities %s do not sum up to 1!' % value)
    return [(p, i) for i, p in enumerate(probs)]


def check_weights(nodes_with_a_weight):
    """
    Ensure that the sum of the values is 1

    :param nodes_with_a_weight: a list of Node objects with a weight attribute
    """
    weights = [n['weight'] for n in nodes_with_a_weight]
    if abs(sum(weights) - 1.) > 1E-12:
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
    if abs(sum(probs) - 1.) > 1E-12:
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


strike_range = FloatRange(0, 360)
slip_range = strike_range
dip_range = FloatRange(0, 90)
rake_range = FloatRange(-180, 180)


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
    values = value.replace(',', ' ').split()
    if not values:
        raise ValueError('Not a list of integers: %r' % value)
    try:
        ints = [int(float(v)) for v in values]
    except:
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
    except:
        raise ValueError('invalid slice: %s' % value)
    return (start, stop)

# ############################## site model ################################ #

vs30_type = ChoiceCI('measured', 'inferred')

SiteParam = collections.namedtuple(
    'SiteParam', 'lon lat depth z1pt0 z2pt5 measured vs30 backarc'.split())


def site_param(z1pt0, z2pt5, vs30Type, vs30, lon, lat,
               depth=0, backarc="false"):
    """
    Used to convert a node like

       <site lon="24.7125" lat="42.779167" vs30="462" vs30Type="inferred"
       z1pt0="100" z2pt5="5" backarc="False"/>

    into a 7-tuple (z1pt0, z2pt5, measured, vs30, backarc, lon, lat)
    """
    return SiteParam(z1pt0=positivefloat(z1pt0), z2pt5=positivefloat(z2pt5),
                     measured=vs30_type(vs30Type) == 'measured',
                     vs30=positivefloat(vs30), lon=longitude(lon),
                     lat=latitude(lat), depth=float_(depth),
                     backarc=boolean(backarc))

# used for the exposure validation
cost_type = Choice('structural', 'nonstructural', 'contents',
                   'business_interruption')

cost_type_type = Choice('aggregated', 'per_area', 'per_asset')


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
class ParamSet(with_metaclass(MetaParamSet, hdf5.LiteralAttrs)):
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

    @classmethod
    def check(cls, dic):
        """
        Convert a dictionary name->string into a dictionary name->value
        by converting the string. If the name does not correspond to a
        known parameter, just ignore it and print a warning.
        """
        res = {}
        for name, text in dic.items():
            try:
                p = getattr(cls, name)
            except AttributeError:
                logging.warn('Ignored unknown parameter %s', name)
            else:
                res[name] = p.validator(text)
        return res

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
                logging.warn("The parameter '%s' is unknown, ignoring" % name)
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
                docstring = is_valid.__doc__.strip()
                doc = textwrap.fill(docstring.format(**vars(self)))
                raise ValueError(doc)

    def __iter__(self):
        for item in sorted(vars(self).items()):
            yield item
