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
Validation library for the engine, the desktop tools, and anything else
"""

import re
import ast
import logging
import textwrap
import collections
from decimal import Decimal

from openquake.hazardlib import imt, scalerel, gsim
from openquake.baselib.general import distinct

SCALEREL = scalerel.get_available_magnitude_scalerel()

GSIM = gsim.get_available_gsims()


# more tests are in tests/valid_test.py
def gsim(value):
    """
    Make sure the given value is the name of an available GSIM class.

    >>> gsim('BooreAtkinson2011')  # doctest: +ELLIPSIS
    <openquake.hazardlib.gsim.boore_atkinson_2011.BooreAtkinson2011 ...>
    """
    if value.endswith(')'):
        gsim_name, argstr = value[:-1].split('(', 1)
        args = ast.literal_eval(argstr + ',') if argstr.strip() else ()
    else:
        gsim_name, args = value, ()
    try:
        gsim_class = GSIM[gsim_name]
    except KeyError:
        raise ValueError('Unknown GSIM: %s' % gsim_name)
    try:
        return gsim_class(*args)
    except TypeError:
        raise ValueError('Could not instantiate %s' % value)


def compose(*validators):
    """
    Implement composition of validators. For instance

    >>> utf8_not_empty = compose(utf8, not_empty)
    >>> utf8_not_empty  # doctest: +ELLIPSIS
    <function compose(utf8,not_empty) at ...>
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
        if not value in self.choices:
            raise ValueError('Got %r, expected %s' % (
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
        if not value in self.choices:
            raise ValueError('%r is not a valid choice in %s' % (
                             value, self.choices))
        return value

category = ChoiceCI('population', 'buildings')


class Regex(object):
    """
    Compare the value with the given regex
    """
    def __init__(self, regex):
        self.rx = re.compile(regex)
        self.__name__ = 'Regex[%s]' % regex

    def __call__(self, value):
        if self.rx.match(value) is None:
            raise ValueError('%r does not match the regex %r' %
                             (value, self.rx.pattern))
        return value

name = Regex(r'^[a-zA-Z_]\w*$')

name_with_dashes = Regex(r'^[a-zA-Z_][\w\-]*$')


class FloatRange(object):
    def __init__(self, minrange, maxrange):
        self.minrange = minrange
        self.maxrange = maxrange
        self.__name__ = 'FloatRange[%s:%s]' % (minrange, maxrange)

    def __call__(self, value):
        f = float_(value)
        if f > self.maxrange:
            raise ValueError('%r is bigger than the max, %r' %
                             (f, self.maxrange))
        if f < self.minrange:
            raise ValueError('%r is smaller than the min, %r' %
                             (f, self.minrange))
        return f


def not_empty(value):
    """Check that the string is not empty"""
    if value == '':
        raise ValueError('Got an empty string')
    return value


def utf8(value):
    r"""
    Check that the string is UTF-8. Returns an encode bytestring.

    >>> utf8('\xe0')
    Traceback (most recent call last):
    ...
    ValueError: Not UTF-8: '\xe0'
    """
    try:
        if isinstance(value, unicode):
            return value.encode('utf-8')
        else:
            return value.decode('utf-8').encode('utf-8')
    except:
        raise ValueError('Not UTF-8: %r' % value)


def utf8_not_empty(value):
    """Check that the string is UTF-8 and not empty"""
    return utf8(not_empty(value))


def namelist(value):
    """
    :param value: input string
    :returns: list of identifiers

    >>> namelist('a1  b_2\t_c')
    ['a1', 'b_2', '_c']

    >>> namelist('a1 b_2 1c')
    Traceback (most recent call last):
        ...
    ValueError: List of names containing an invalid name: 1c
    """
    names = value.split()
    if not names:
        raise ValueError('Got an empty name list')
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
        raise ValueError('%r is not a float' % value)


def longitude(value):
    """
    :param value: input string
    :returns: longitude float
    """
    lon = float_(value)
    if lon > 180.:
        raise ValueError('longitude %s > 180' % lon)
    elif lon < -180.:
        raise ValueError('longitude %s < -180' % lon)
    return lon


def latitude(value):
    """
    :param value: input string
    :returns: latitude float
    """
    lat = float_(value)
    if lat > 90.:
        raise ValueError('latitude %s > 90' % lat)
    elif lat < -90.:
        raise ValueError('latitude %s < -90' % lat)
    return lat


def depth(value):
    """
    :param value: input string
    :returns: float >= 0
    """
    dep = float_(value)
    if dep < 0:
        raise ValueError('depth %s < 0' % dep)
    return dep


def lon_lat(value):
    """
    :param value: a pair of coordinates
    :returns: a tuple (longitude, latitude)

    >>> lon_lat('12 14')
    (12.0, 14.0)
    """
    lon, lat = value.split()
    return longitude(lon), latitude(lat)


def lon_lat_iml(value, lon, lat, iml):
    """
    Used to convert nodes of the form <node lon="LON" lat="LAT" iml="IML" />
    """
    return longitude(lon), latitude(lat), positivefloat(iml)


def coordinates(value):
    """
    Convert a non-empty string into a list of lon-lat coordinates
    >>> coordinates('')
    Traceback (most recent call last):
    ...
    ValueError: Empty list of coordinates: ''
    >>> coordinates('1.1 1.2')
    [(1.1, 1.2)]
    >>> coordinates('1.1 1.2, 2.2 2.3')
    [(1.1, 1.2), (2.2, 2.3)]
    """
    if not value.strip():
        raise ValueError('Empty list of coordinates: %r' % value)
    return map(lon_lat, value.split(','))


def wkt_polygon(value):
    """
    Convert a string with a comma separated list of coordinates into
    a WKT polygon, by closing the ring.
    """
    points = ['%s %s' % lon_lat for lon_lat in coordinates(value)]
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
    :param value: string of whitespace separated floats
    :returns: a list of positive floats
    """
    return map(positivefloat, value.split())


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


def probabilities(value):
    """
    :param value: input string, comma separated or space separated
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
    return map(probability, value.replace(',', ' ').split())


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


def IML(value, IMT, minIML=None, maxIML=None, imlUnit=None):
    """
    Convert a node of the form

    <IML IMT="PGA" imlUnit="g" minIML="0.02" maxIML="1.5"/>

    into ("PGA", None, 0.02, 1.5) and a node

    <IML IMT="MMI" imlUnit="g">7 8 9 10 11</IML>

    into ("MMI", [7., 8., 9., 10., 11.], None, None)
    """
    imt_str = str(imt.from_string(IMT))
    if value:
        imls = positivefloats(value)
        check_levels(imls, imt_str)
    else:
        imls = None
    min_iml = positivefloat(minIML) if minIML else None
    max_iml = positivefloat(maxIML) if maxIML else None
    return (imt_str, imls, min_iml, max_iml, imlUnit)


def fragilityparams(value, mean, stddev):
    """
    Convert a node of the form <params mean="0.30" stddev="0.16" /> into
    a pair (0.30, 0.16)
    """
    return positivefloat(mean), positivefloat(stddev)


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

    >>> intensity_measure_types_and_levels('{"PGA": [0.1, 0.2]}')
    {'PGA': [0.1, 0.2]}
    """
    dic = dictionary(value)
    for imt_str, imls in dic.iteritems():
        check_levels(imls, imt_str)  # ValueError if the levels are invalid
    return dic


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
    """
    if not value:
        return {}
    try:
        dic = dict(ast.literal_eval(value))
    except:
        raise ValueError('%r is not a valid Python dictionary' % value)
    return dic


############################# SOURCES/RUPTURES ###############################

def mag_scale_rel(value):
    """
    :param value:
        name of a Magnitude-Scale relationship in hazardlib
    :returns:
        the corresponding hazardlib object
    """
    value = value.strip()
    if value not in SCALEREL:
        raise ValueError('%r is not a recognized magnitude-scale '
                         'relationship' % value)
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
        return map(float_, values)
    except Exception as exc:
        raise ValueError('Found a non-float in %s: %s' % (value, exc))


def point2d(value, lon, lat):
    """
    This is used to convert nodes of the form
    <location lon="LON" lat="LAT" />

    :param value: None
    :param lon: longitude string
    :param lat: latitude string
    :returns: a validated pair (lon, lat)
    """
    return longitude(lon), latitude(lat)


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


def probability_depth(value, probability, depth):
    """
    This is used to convert nodes of the form
    <hypoDepth probability="PROB" depth="DEPTH" />

    :param value: None
    :param probability: a probability
    :param depth: a depth
    :returns: a validated pair (probability, depth)
    """
    return (range01(probability), positivefloat(depth))


strike_range = FloatRange(0, 360)
dip_range = FloatRange(0, 90)
rake_range = FloatRange(-180, 180)


def nodal_plane(value, probability, strike, dip, rake):
    """
    This is used to convert nodes of the form
     <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0" />

    :param value: None
    :param probability: a probability
    :param strike: strike angle
    :param dip: dip parameter
    :param rake: rake angle
    :returns: a validated pair (probability, depth)
    """
    return (range01(probability), strike_range(strike),
            dip_range(dip), rake_range(rake))


def ab_values(value):
    """
    a and b values of the GR magniture-scaling relation.
    a is a positive float, b is just a float.
    """
    a, b = value.split()
    return positivefloat(a), float_(b)


################################ site model ##################################

vs30_type = ChoiceCI('measured', 'inferred')

SiteParam = collections.namedtuple(
    'SiteParam', 'z1pt0 z2pt5 measured vs30 lon lat backarc'.split())


def site_param(value, z1pt0, z2pt5, vs30Type, vs30, lon, lat, backarc="false"):
    """
    Used to convert a node like

       <site lon="24.7125" lat="42.779167" vs30="462" vs30Type="inferred"
       z1pt0="100" z2pt5="5" backarc="False"/>

    into a 7-tuple (z1pt0, z2pt5, measured, vs30, backarc, lon, lat)
    """
    return SiteParam(positivefloat(z1pt0), positivefloat(z2pt5),
                     vs30_type(vs30Type) == 'measured',
                     positivefloat(vs30), longitude(lon),
                     latitude(lat), boolean(backarc))


###########################################################################

def parameters(**names_vals):
    """
    Returns a dictionary {name: validator} by making sure
    that the validators are callable objects with a `__name__`.

    :param names_vals:
        keyword arguments parameter_name -> parameter_validator
    """
    for name, val in names_vals.iteritems():
        if not callable(val):
            raise ValueError(
                '%r for %s is not a validator: it is not callable'
                % (val, name))
        if not hasattr(val, '__name__'):
            raise ValueError(
                '%r for %s is not a validator: it has no __name__'
                % (val, name))
    return names_vals


# used in commonlib.oqvalidation
class ParamSet(object):
    """
    A set of valid interrelated parameters. Here is an example
    of usage:

    >>> class MyParams(ParamSet):
    ...     params = parameters(a=positiveint, b=positivefloat)
    ...
    ...     def is_valid_not_too_big(self):
    ...         "The sum of a and b must be under 10. "
    ...         return self.a + self.b < 10

    >>> MyParams(a='1', b='7.2')
    <MyParams a=1, b=7.2>

    >>> MyParams(a='1', b='9.2').validate()
    Traceback (most recent call last):
    ...
    ValueError: The sum of a and b must be under 10.
    Got:
    a=1
    b=9.2

    The constrains are applied in lexicographic order.
    """
    params = {}

    def __init__(self, **names_vals):
        for name, val in names_vals.iteritems():
            if name.startswith(('_', 'is_valid_')):
                raise NameError('The parameter name %s is not acceptable'
                                % name)
            try:
                convert = self.__class__.params[name]
            except KeyError:
                logging.warn('The parameter %r is unknown, ignoring' % name)
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
        valids = sorted(getattr(self, valid)
                        for valid in dir(self.__class__)
                        if valid.startswith('is_valid_'))
        for is_valid in valids:
            if not is_valid():
                dump = '\n'.join('%s=%s' % (n, v)
                                 for n, v in sorted(self.__dict__.items()))
                docstring = is_valid.__doc__.strip()
                doc = textwrap.fill(docstring.format(**vars(self)))
                raise ValueError(doc + '\nGot:\n' + dump)

    def __iter__(self):
        for item in sorted(vars(self).iteritems()):
            yield item

    def __repr__(self):
        names = sorted(n for n in vars(self) if not n.startswith('_'))
        nameval = ', '.join('%s=%s' % (n, getattr(self, n)) for n in names)
        return '<%s %s>' % (self.__class__.__name__, nameval)
