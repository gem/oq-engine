# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
import collections
import numpy


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
    ('SA(1.0)', 1.0)
    >>> imt2tup('SA(1)')
    ('SA(1.0)', 1.0)
    """
    s = string.strip()
    name, *rest = s.split('(')
    if name not in globals():
        raise KeyError(name)
    elif len(name) > 12:
        raise NameError('IMT class name longer than 12 chars: %s' % name)
    elif not rest:
        if name == 'SA':
            raise ValueError('Missing period in SA')
        # no parenthesis, PGA is considered the same as PGA()
        return (s,)
    period = float(rest[0][:-1])
    return ('SA(%s)' % period, period)


def from_string(imt, _damping=5.0):
    """
    Convert an IMT string into an hazardlib object.

    :param str imt:
        Intensity Measure Type.
    """
    if re.match(r'[ \+\d\.]+', imt):
        return SA(float(imt))
    return IMT(*imt2tup(imt))


def repr(self):
    if self.period and self.damping != 5.0:
        return 'SA(%s, %s)' % (self.period, self.damping)
    return self.string


IMT = collections.namedtuple('IMT', 'string period damping')
IMT.__new__.__defaults__ = (0., 5.0)
IMT.__lt__ = lambda self, other: self[1] < other[1]
IMT.__gt__ = lambda self, other: self[1] > other[1]
IMT.__le__ = lambda self, other: self[1] <= other[1]
IMT.__ge__ = lambda self, other: self[1] >= other[1]
IMT.__repr__ = repr


def PGA():
    """
    Peak ground acceleration during an earthquake measured in units
    of ``g``, times of gravitational acceleration.
    """
    return IMT('PGA')


def PGV():
    """
    Peak ground velocity during an earthquake measured in units of ``cm/sec``.
    """
    return IMT('PGV')


def PGD():
    """
    Peak ground displacement during an earthquake measured in units of ``cm``.
    """
    return IMT('PGD')


def SA(period, damping=5.0):
    """
    Spectral acceleration, defined as the maximum acceleration of a damped,
    single-degree-of-freedom harmonic oscillator. Units are ``g``, times
    of gravitational acceleration.
    """
    period = float(period)
    return IMT('SA(%s)' % period, period, damping)


def AvgSA():
    """
    Dummy spectral acceleration to compute average ground motion over
    several spectral ordinates.
    """
    return IMT('AvgSA')


def IA():
    """
    Arias intensity. Determines the intensity of shaking by measuring
    the acceleration of transient seismic waves. Units are ``m/s``.
    """
    return IMT('IA')


def CAV():
    """
    Cumulative Absolute Velocity. Defins the integral of the absolute
    acceleration time series. Units are "g-sec"
    """
    return IMT('CAV')


def RSD():
    """
    Relative significant duration, 5-95% of :class:`Arias intensity<IA>`,
    in seconds.
    """
    return IMT('RDS')


def RSD595(IMT):
    """
    Alias for RSD
    """
    return IMT('RSD595')


def RSD575():
    """
    Relative significant duration, 5-75% of :class:`Arias intensity<IA>`,
    in seconds.
    """
    return IMT('RSD575')


def RSD2080():
    """
    Relative significant duration, 20-80% of :class:`Arias intensity<IA>`,
    in seconds.
    """
    return IMT('RSD2080')


def MMI():
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """
    return IMT('MMI')


def JMA():
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """
    return IMT('JMA')


# Volcanic IMTs

def ASH():
    """
    Level of the ash fall in millimeters
    """
    return IMT('ASH')


# secondary perils

def Disp():
    """
    Displacement
    """
    return IMT('Disp')


def DispProb():
    """
    Displacement probability
    """
    return IMT('RSD595')


def LiqProb():
    """
    Liquefaction probability
    """
    return IMT('LiqProb')


def PGDMax(vert_settlement, lat_spread):
    """
    Maximum between vert_settlement and lat_spread
    """
    return numpy.maximum(vert_settlement, lat_spread)


def PGDGeomMean(vert_settlement, lat_spread):
    """
    Geometric mean between vert_settlement and lat_spread
    """
    return numpy.sqrt(vert_settlement * lat_spread)
