# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.imt` defines different intensity measure
types.
"""
import ast
import operator
import functools

# NB: (MS) the management of the IMTs implemented here is complex, it would
# be better to have a single IMT class, but it is as it is for legacy reasons

registry = {}  # IMT string -> IMT class


def positivefloat(val):
    """
    Raise a ValueError if val <= 0
    """
    if val <= 0:
        raise ValueError(val)


def imt2tup(string):
    """
    >>> imt2tup('PGA')
    ('PGA',)
    >>> imt2tup('SA(1.0)')
    ('SA', 1.0)
    >>> imt2tup('SA(1)')
    ('SA', 1.0)
    """
    s = string.strip()
    if not s.endswith(')'):
        # no parenthesis, PGA is considered the same as PGA()
        return (s,)
    name, rest = s.split('(', 1)
    return (name,) + tuple(float(x) for x in ast.literal_eval(rest[:-1] + ','))


def from_string(imt):
    """
    Convert an IMT string into an hazardlib object.

    :param str imt:
        Intensity Measure Type.
    """
    tup = imt2tup(imt)
    return registry[tup[0]](*tup[1:])


class IMTMeta(type):
    """
    Metaclass setting __slots__, __new__ and the properties of IMT classes
    """
    def __new__(mcs, name, bases, dct):
        dct['__slots__'] = ()
        cls = type.__new__(mcs, name, bases, dct)
        fields = ''
        for index, (field, check) in enumerate(cls._fields):
            setattr(cls, field, property(operator.itemgetter(index + 1)))
            fields += field + ','
        evaldic = {}
        code = '''def __new__(cls, %s):
    self = tuple.__new__(cls, (%r, %s))
    for arg, (field, check) in zip(self[1:], self._fields):
        check(arg)
    return self
    ''' % (fields, name, fields)
        exec(code, evaldic)
        cls.__new__ = evaldic['__new__']
        cls.__new__.__defaults__ = cls._defaults
        registry[name] = cls
        return cls


@functools.total_ordering
class IMT(tuple, metaclass=IMTMeta):
    """
    Base class for intensity measure type.

    Subclasses may define class attribute ``_fields`` as a tuple with names
    of parameters the specific intensity measure type requires (if there
    are any).
    """
    _fields = ()
    _defaults = None

    @property
    def name(self):
        """The name of the Intensity Measure Type (ex. "PGA", "SA", ...)"""
        return self[0]

    def __getnewargs__(self):
        return tuple(getattr(self, field) for field, check in self._fields)

    def __lt__(self, other):
        return (self[0], self[1] or 0, self[2] or 0) < (
            other[0], other[1] or 0, other[2] or 0)

    def __repr__(self):
        if not self._fields:  # return the name
            return self[0]
        return '%s(%s)' % (type(self).__name__,
                           ', '.join(str(getattr(self, field))
                                     for field, check in self._fields))


class PGA(IMT):
    """
    Peak ground acceleration during an earthquake measured in units
    of ``g``, times of gravitational acceleration.
    """
    period = 0.0


class PGV(IMT):
    """
    Peak ground velocity during an earthquake measured in units of ``cm/sec``.
    """


class PGD(IMT):
    """
    Peak ground displacement during an earthquake measured in units of ``cm``.
    """


class SA(IMT):
    """
    Spectral acceleration, defined as the maximum acceleration of a damped,
    single-degree-of-freedom harmonic oscillator. Units are ``g``, times
    of gravitational acceleration.

    :param period:
        The natural period of the oscillator in seconds.
    :param damping:
        The degree of damping for the oscillator in percents.

    :raises ValueError:
        if period or damping is not positive.
    """
    _fields = (('period', positivefloat), ('damping', positivefloat))
    _defaults = (5.0,)  # damping

    def __repr__(self):
        if self.damping != 5.0:
            return '%s(%s, %s)' % (self.name, self.period, self.damping)
        else:
            return '%s(%s)' % (self.name, self.period)


class AvgSA(IMT):
    """
    Dummy spectral acceleration to compute average ground motion over
    several spectral ordinates.
    """


class IA(IMT):
    """
    Arias intensity. Determines the intensity of shaking by measuring
    the acceleration of transient seismic waves. Units are ``m/s``.
    """


class CAV(IMT):
    """
    Cumulative Absolute Velocity. Defins the integral of the absolute
    acceleration time series. Units are "g-sec"
    """


class RSD(IMT):
    """
    Relative significant duration, 5-95% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class RSD595(IMT):
    """
    Alias for RSD
    """


class RSD575(IMT):
    """
    Relative significant duration, 5-75% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class RSD2080(IMT):
    """
    Relative significant duration, 20-80% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class MMI(IMT):
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """

# geotechnical IMTs


class PGDfLatSpread(IMT):
    """
    Permanent ground defomation (m) from lateral spread
    """


class PGDfSettle(IMT):
    """
    Permanent ground defomation (m) from settlement
    """


class PGDfSlope(IMT):
    """
    Permanent ground deformation (m) from slope failure
    """


class PGDfRupture(IMT):
    """
    Permanent ground deformation (m) from co-seismic rupture
    """


# Volcanic IMTs

class ASH(IMT):
    """
    Level of the ash fall in millimeters
    """


class LAVA(IMT):
    """
    Boolean value for the lava flow (1 if affected 0 otherwise)
    """


class LAHAR(IMT):
    """
    Boolean value for the lahars (1 if affected 0 otherwise)
    """


class PYRO(IMT):
    """
    Boolean value for the pyroclastic flow (1 if affected 0 otherwise)
    """
