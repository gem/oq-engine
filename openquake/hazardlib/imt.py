# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
from openquake.baselib.general import DictArray

FREQUENCY_PATTERN = '^(EAS|FAS|DRVT|AvgSA)\\((\\d+\\.*\\d*)\\)'


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

    if len(rest[0][:-1].split(',')) == 1:
        period = float(rest[0][:-1])
    elif len(rest[0][:-1].split(',')) == 2:
        period = float(rest[0][:-1].split(',')[0])
        strength_ratio = float(rest[0][:-1].split(',')[1])
    else:
        raise NameError('IMT attributes not recognizable: %s' % rest[0][:-1])
    if name.startswith("Sa_avg2") or name.startswith("SA_avg2"):
        return ('Sa_avg2(%s)' % period, period)
    elif name.startswith("Sa_avg3") or name.startswith("SA_avg3"):
        return ('Sa_avg3(%s)' % period, period)
    elif name.startswith("SA") or name.startswith("Sa"):
        return ('SA(%s)' % period, period)
    elif name.startswith("FIV3"):
        return ('FIV3(%s)' % period, period)
    elif name.startswith("SDi"):
        return ('SDi(%s,%s)' % (period, strength_ratio), period, strength_ratio)
    else:
        raise NameError('IMT class name not recognizable: %s' % name)


def from_string(imt, _damping=5.0):
    """
    Convert an IMT string into an hazardlib object.

    :param str imt:
        Intensity Measure Type.
    """
    m = re.match(FREQUENCY_PATTERN, imt)
    if m:  # passed float interpreted as frequency
        if m.group(1) == 'EAS':
            im = EAS(float(m.group(2)))
        elif m.group(1) == 'FAS':
            im = FAS(float(m.group(2)))
        elif m.group(1) == 'DRVT':
            im = DRVT(float(m.group(2)))
        elif m.group(1) == 'AvgSA':
            im = AvgSA(float(m.group(2)))
        return im
    elif re.match(r'^SDi\((\d+\.?\d*),(\d+\.?\d*)\)$', imt):
        m = re.match(r'^SDi\((\d+\.?\d*),(\d+\.?\d*)\)$', imt)
        return SDi(float(m.group(1)), float(m.group(2)))
    elif re.match(r'[ \+\d\.]+', imt):  # passed float interpreted as period
        return SA(float(imt))
    return IMT(*imt2tup(imt))


def sort_by_imt(imtls):
    """
    :param imtls: a dictionary keyed by IMT string
    :returns: a new dictionary with the keys sorted by period

    >>> sort_by_imt({'SA(10.0)': 1, 'SA(2.0)': 2})
    {'SA(2.0)': 2, 'SA(10.0)': 1}
    """
    imts = sorted(imtls, key=lambda imt: from_string(imt).period)
    return {imt: imtls[imt] for imt in imts}


def dictarray(imtls):
    """
    :returns: a DictArray sorted by IMT
    """
    return DictArray(sort_by_imt(imtls))


def repr(self):
    if self.period and self.damping != 5.0:
        if self.string.startswith('SDi'):
            return 'SDi(%s, %s, %s)' % (self.period, self.strength_ratio,
                                        self.damping)
        return 'SA(%s, %s)' % (self.period, self.damping)
    return self.string


IMT = collections.namedtuple('IMT', 'string period damping strength_ratio')
IMT.__new__.__defaults__ = (0., 5.0, None)
IMT.__lt__ = lambda self, other: self[1] < other[1]
IMT.__gt__ = lambda self, other: self[1] > other[1]
IMT.__le__ = lambda self, other: self[1] <= other[1]
IMT.__ge__ = lambda self, other: self[1] >= other[1]
IMT.__repr__ = repr
IMT.frequency = property(lambda self: 1. / self.period)


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


def EAS(frequency):
    """
    Effective Amplitude Spectrum in terms of a frequency (in Hz).
    """
    period = 1. / frequency
    return IMT('EAS(%.6f)' % frequency, period, 5.0)


def FAS(frequency):
    """
    Fourier Amplitude Spectrum in terms of a frequency (in Hz).
    """
    period = 1. / frequency
    return IMT('FAS(%.6f)' % frequency, period, 5.0)


def DRVT(frequency):
    """
    Duration as defined in Bora et al. (2019)
    """
    period = 1. / frequency
    return IMT('DRVT(%.6f)' % frequency, period, 5.0)


def SA(period, damping=5.0):
    """
    Spectral acceleration, defined as the maximum acceleration of a damped,
    single-degree-of-freedom harmonic oscillator. Units are ``g``, times
    of gravitational acceleration.
    """
    period = float(period)
    return IMT('SA(%s)' % period, period, damping)


def FIV3(period, damping=5.0):
    """
    Filtered incremental velocity, as defined in: Dávalos, H. and Miranda,
    E. (2019) ‘Filtered incremental velocity: A novel approach in
    intensity measures for seismic collapse estimation’, Earthquake
    Engineering and Structural Dynamics, 48(12), pp. 1384–1405. Available
    at: https://doi.org/10.1002/eqe.3205. Units are ``cm/s``.
    """
    period = float(period)
    return IMT('FIV3(%s)' % period, period, damping)


def Sa_avg2(period, damping=5.0):
    period = float(period)
    return IMT('Sa_avg2(%s)' % period, period, damping)


def Sa_avg3(period, damping=5.0):
    period = float(period)
    return IMT('Sa_avg3(%s)' % period, period, damping)


def SDi(period, strength_ratio, damping=5.0):
    """
    Inelastic spectral displacement, defined as the maximum displacement
    of a damped, single-degree-of-freedom inelastic oscillator. Units
    are ``cm``.
    """
    period = float(period)
    strength_ratio = float(strength_ratio)
    return IMT('SDi(%s,%s)' % (period, strength_ratio), period, damping,
               strength_ratio)


def AvgSA(period=None, damping=5.0):
    """
    Dummy spectral acceleration to compute average ground motion over
    several spectral ordinates. Depending on the choice of AvgSA GMPE, this
    can operate as a scalar value or as a vector quantity.
    """
    return IMT('AvgSA(%s)' % period, period, damping)\
        if period else IMT('AvgSA')


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
    return IMT('RSD')


def RSD595():
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

# secondary IMTs
sec_imts = '''ASH LAVA LAHAR PYRO
Disp DispProb LiqProb LiqOccur LSE PGDMax LSD PGDGeomMean LsProb
'''.split()
for sec in sec_imts:
    assert '_' not in sec, sec


# Volcanic IMTs

def ASH():
    """
    Level of the ash fall in millimeters
    """
    return IMT('ASH')


def LAVA():
    """
    Lava Intensity
    """
    return IMT('LAVA')


def LAHAR():
    """
    Lahar Intensity
    """
    return IMT('LAHAR')


def PYRO():
    """
    Pyroclastic Flow Intensity
    """
    return IMT('PYRO')


# Liquefaction IMTs

def Disp():
    """
    Displacement
    """
    return IMT('Disp')


def DispProb():
    """
    Displacement probability
    """
    return IMT('DispProb')


def LiqProb():
    """
    Liquefaction probability
    """
    return IMT('LiqProb')


def LiqOccur():
    """
    Liquefaction occurrence class
    """
    return IMT('LiqOccur')


def LSE():
    """
    Liquefaction or Landslide spatial extent.
    """
    return IMT('LSE')


def PGDMax(vert_settlement, lat_spread):
    """
    Maximum between vert_settlement and lat_spread
    """
    return numpy.maximum(vert_settlement, lat_spread)


def LSD():
    """
    Liquefaction-induced lateral spread displacements measured in units of
    ``m``.
    """
    return IMT('LSD')


def PGDGeomMean(vert_settlement, lat_spread):
    """
    Geometric mean between vert_settlement and lat_spread
    """
    return numpy.sqrt(vert_settlement * lat_spread)


def LsProb():
    """
    Probability of landsliding.
    """
    return IMT('LsProb')
