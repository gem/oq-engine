# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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
import re
import operator
import functools

# NB: (MS) the management of the IMTs implemented here is horrible and will
# be thrown away when we will need to introduce a new IMT.

__all__ = ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'CAV', 'RSD', 'MMI',
           'PGDfLatSpread', 'PGDfSettle', 'PGDfSlope', 'PGDfRupture',
           'SDI','SAAVG','FIV3')

DEFAULT_SA_DAMPING = 5.0

imt_cache = {}  # used in from_string


def from_string(imt):
    """
    Convert an IMT string into a hazardlib object. It is fast because cached.

    :param str imt:
        Intensity Measure Type.
    """
    try:
        return imt_cache[imt]
    except KeyError:
        if imt.startswith('SA'):
            match = re.match(r'^SA\(([^)]+?)\)$', imt)
            period = float(match.group(1))
            instance = SA(period, DEFAULT_SA_DAMPING)
        elif imt.startswith('SDI'):
            match = re.match(r'^SDI\(([^)]+?)\)$', imt)
            aux = match.group(1).split(",")
            period = float(aux[0])
            Cy = float(aux[1])
            instance = SDI(period, Cy, DEFAULT_SA_DAMPING)
        elif imt.startswith('SAAVG'):
            match = re.match(r'^SAAVG\(([^)]+?)\)$', imt)
            period = float(match.group(1))
            instance = SAAVG(period, DEFAULT_SA_DAMPING)
        elif imt.startswith('FIV3'):
            match = re.match(r'^FIV3\(([^)]+?)\)$', imt)
            period = float(match.group(1))
            instance = FIV3(period)
        else:
            try:
                imt_class = globals()[imt]
            except KeyError:
                raise ValueError('Unknown IMT: ' + repr(imt))
            instance = imt_class(None, None)
        imt_cache[imt] = instance
        return instance


class IMTMeta(type):
    """Metaclass setting the _slots_ and the properties of IMT classes"""
    def __new__(mcs, name, bases, dct):
        dct['__slots__'] = ()
        cls = type.__new__(mcs, name, bases, dct)
        for index, field in enumerate(cls._fields):
            setattr(cls, field, property(operator.itemgetter(index + 1)))
        return cls


@functools.total_ordering
class _IMT(tuple, metaclass=IMTMeta):
    """
    Base class for intensity measure type.

    Subclasses may define class attribute ``_fields`` as a tuple with names
    of parameters the specific intensity measure type requires (if there
    are any).
    """
    _fields = ()

    def __new__(cls, sa_period=None, sa_damping=None, Cy=None):
        return tuple.__new__(cls, (cls.__name__, sa_period, sa_damping, Cy))

    def __getnewargs__(self):
        return tuple(getattr(self, field) for field in self._fields)

    def __str__(self):
        if self[0] == 'SA':
            return 'SA(%s)' % self[1]
        elif self[0] == 'SDI':
            return 'SDI(%s,%s)' % (self[1], self[3])
        elif self[0] == 'SAAVG':
            return 'SAAVG(%s)' % self[1]
        elif self[0] == 'FIV3':
            return 'FIV3(%s)' % self[1]
        else:
    	    return self[0]

    def __lt__(self, other):
        return (self[0], self[1] or 0, self[2] or 0) < (
            other[0], other[1] or 0, other[2] or 0)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__,
                           ', '.join('%s=%s' % (field, getattr(self, field))
                                     for field in type(self)._fields))


class PGA(_IMT):
    """
    Peak ground acceleration during an earthquake measured in units
    of ``g``, times of gravitational acceleration.
    """
    period = 0.0


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

    def __new__(cls, period, damping=DEFAULT_SA_DAMPING):
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


class RSD595(_IMT):
    """
    Alias for RSD
    """


class RSD575(_IMT):
    """
    Relative significant duration, 5-75% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class RSD2080(_IMT):
    """
    Relative significant duration, 20-80% of :class:`Arias intensity
    <IA>`, in seconds.
    """


class MMI(_IMT):
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """

class PGDfLatSpread(_IMT):
    """
    Permanent ground defomation (m) from lateral spread
    """

class PGDfSettle(_IMT):
    """
    Permanent ground defomation (m) from settlement
    """

class PGDfSlope(_IMT):
    """
    Permanent ground deformation (m) from slope failure
    """

class PGDfRupture(_IMT):
    """
    Permanent ground deformation (m) from co-seismic rupture
    """

class SDI(_IMT):
    """
    Spectral inelastic displacement, defined as the maximum displacement of
    a single-degree-of-freedom system with bilinear behavior (3% postelastic
	stiffness ratio).
    Units are ``cm``.

    :param period:
        The natural period of the oscillator in seconds.
	:param Cy:
		The yield strengh coefficient, defined as Fy/W, where 
		Fy is the lateral yield strengh of the system, and W 
		is the weight of the system.
    :param damping:
        The degree of damping for the oscillator in percents.
  
    :raises ValueError:
        if period or damping is not positive.
		if Cy is out of the bounds of Cy_min - Cy_max for the given period
    """
    _fields = ('period', 'damping', 'Cy')

    def __new__(cls, period, Cy, damping=DEFAULT_SA_DAMPING):
        Cy_max = round(min(1.5, 1.5*0.6/period),4)
        Cy_min = round(Cy_max/15,4)
        if not period > 0:
            raise ValueError('period must be positive')
        if not damping > 0:
            raise ValueError('damping must be positive')
        if not Cy > 0:
            raise ValueError('Cy must be positive')
        if not Cy_min <= Cy <= Cy_max:
            raise ValueError('Cy should be between {0:.4f} and {1:.4f}.  \
                             Used Cy = {2:.5f}'.format(Cy_min, Cy_max, Cy))
        return _IMT.__new__(cls, sa_period=period, Cy=Cy, sa_damping=damping)


class SAAVG(_IMT):
    """
    Sa_avg, defined as the geometric mean of 10 equally spaced spectral 
    accelerations between one fifth and three times the input period, 
    Units are ``g``, times of gravitational acceleration.

    :param period:
        Input period in seconds.
    :param damping:
        The degree of damping for the spectral accelerations.

    :raises ValueError:
        if period or damping is not positive.
    """
    _fields = ('period', 'damping')

    def __new__(cls, period, damping=DEFAULT_SA_DAMPING):
        if not period > 0:
            raise ValueError('period must be positive')
        if not damping > 0:
            raise ValueError('damping must be positive')
        return _IMT.__new__(cls, period, damping)


class FIV3(_IMT):
    """
    Filtered Incremental Velocity (3), defined as the absolute sum of either
	the three local maximum or three local minimum period-dependent 
	accumulated acceleration areas, in a period range of 70% of the input
	period, computed at all instants t, from a low-pass filtered acceleration
	time series using a 2nd order Butterworth filter and a 1Hz cut-off 
	frequency.
    Units are ``cm/s``.

    :param period:
        Input period.

    :raises ValueError:
        if period or damping is not positive.
    """
    _fields = ('period',)

    def __new__(cls, period):
        if not period > 0:
            raise ValueError('period must be positive')
        return _IMT.__new__(cls, period)


