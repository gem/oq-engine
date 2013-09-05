# The Hazard Library
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
Module :mod:`openquake.hazardlib.imt` defines different intensity measure
types.
"""
import operator


__all__ = ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'CSV', 'RSD', 'MMI')


class _IMT(tuple):
    """
    Base class for intensity measure type.

    Subclasses may define class attribute ``_fields`` as a tuple with names
    of parameters the specific intensity measure type requires (if there
    are any).
    """
    _fields = ()

    class __metaclass__(type):
        def __new__(mcs, name, bases, dct):
            dct['__slots__'] = ()
            cls = type.__new__(mcs, name, bases, dct)
            for index, field in enumerate(cls._fields):
                setattr(cls, field, property(operator.itemgetter(index)))
            return cls

    def __new__(cls, *args):
        salt = hash(('IMT', cls.__name__))
        return tuple.__new__(cls, args + (salt, ))

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__,
                           ', '.join('%s=%s' % (field, getattr(self, field))
                                     for field in type(self)._fields))


class PGA(_IMT):
    """
    Peak ground acceleration during an earthquake measured in units
    of ``g``, times of gravitational acceleration.
    """


class PGV(_IMT):
    """
    Peak ground velocity during an earthquake measured in units of ``cm/sec``.
    """


class PGD(_IMT):
    """
    Peak ground displacement during an earthquake measured in units of ``cm``.
    """


class SA(_IMT):
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
    _fields = ('period', 'damping')

    def __new__(cls, period, damping):
        if not period > 0:
            raise ValueError('period must be positive')
        if not damping > 0:
            raise ValueError('damping must be positive')
        return _IMT.__new__(cls, period, damping)


class IA(_IMT):
    """
    Arias intensity. Determines the intensity of shaking by measuring
    the acceleration of transient seismic waves. Units are ``m/s``.
    """


class CAV(_IMT):
    """
    Cumulative Absolute Velocity. Defins the integral of the absolute
    acceleration time series. Units are "g-sec"
    """

class RSD(_IMT):
    """
    Relative significant duration, 5-95% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class MMI(_IMT):
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """
