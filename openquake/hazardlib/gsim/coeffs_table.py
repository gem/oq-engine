# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import re
import math
import copy
import toml
import scipy
import numpy as np
from openquake.baselib.general import RecordBuilder
from openquake.hazardlib.imt import from_string

SA_LIKE_PREFIXES = ['SA', 'EA', 'FA', 'DR', 'Av', 'SD']


class CoeffsTable(object):
    r"""
    Instances of :class:`CoeffsTable` encapsulate tables of coefficients
    corresponding to different IMTs.

    Tables are defined in a space-separated tabular form in a simple string
    literal (heading and trailing whitespace does not matter). The first column
    in the table must be named "IMT" (or "imt") and thus should represent IMTs:

    >>> CoeffsTable(table='''imf z
    ...                      pga 1''')
    Traceback (most recent call last):
        ...
    ValueError: first column in a table must be IMT

    Names of other columns are used as coefficients dicts keys. The values
    in the first column should correspond to real intensity measure types,
    see :mod:`openquake.hazardlib.imt`:

    >>> CoeffsTable(table='''imt  z
    ...                      pgx  2''')
    Traceback (most recent call last):
        ...
    KeyError: 'PGX'

    Note that :class:`CoeffsTable` requires passing the arguments explicitly.

    >>> CoeffsTable(table='', foo=1)
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable got unexpected kwargs: {'foo': 1}

    If there are :class:`~openquake.hazardlib.imt.SA` IMTs in the table, they
    are not referenced by name, because they require parametrization:

    >>> CoeffsTable(table='''imt  x
    ...                      sa   15''')
    Traceback (most recent call last):
        ...
    ValueError: specify period as float value to declare SA IMT

    So proper table defining SA looks like this:

    >>> ct = CoeffsTable(sa_damping=5, table='''
    ...     imt   a    b     c   d
    ...     pga   1    2.4  -5   0.01
    ...     pgd  7.6  12     0  44.1
    ...     0.1  10   20    30  40
    ...     1.0   1    2     3   4
    ...     10    2    4     6   8
    ... ''')

    Table objects could be indexed by IMT objects (this returns a dictionary
    of coefficients):

    >>> from openquake.hazardlib import imt
    >>> ct[imt.PGA()]
    (1., 2.4, -5., 0.01)
    >>> ct[imt.PGD()]
    (7.6, 12., 0., 44.1)
    >>> ct[imt.SA(damping=5, period=0.1)]
    (10., 20., 30., 40.)
    >>> ct[imt.PGV()]
    Traceback (most recent call last):
        ...
    KeyError: PGV
    >>> ct[imt.SA(1.0, 4)]
    Traceback (most recent call last):
        ...
    KeyError: SA(1.0, 4)

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`openquake.hazardlib.imt.SA` with period
    value that is not specified in the table. The coefficients then
    get interpolated between the ones for closest higher and closest
    lower period. That scaling of coefficients works in a logarithmic
    scale of periods and only within the same damping:

    >>> '%.5f' % ct[imt.SA(period=0.2, damping=5)]['a']
    '7.29073'
    >>> '%.5f' % ct[imt.SA(period=0.9, damping=5)]['c']
    '4.23545'
    >>> '%.5f' % ct[imt.SA(period=5, damping=5)]['c']
    '5.09691'
    >>> ct[imt.SA(period=0.9, damping=15)]
    Traceback (most recent call last):
        ...
    KeyError: SA(0.9, 15)

    Extrapolation is not possible:

    >>> ct[imt.SA(period=0.01, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: SA(0.01)

    It is also possible to instantiate a table from a tuple of dictionaries,
    corresponding to the SA coefficients and non-SA coefficients:

    >>> coeffs = {imt.SA(0.1): {"a": 1.0, "b": 2.0},
    ...           imt.SA(1.0): {"a": 3.0, "b": 4.0},
    ...           imt.PGA(): {"a": 0.1, "b": 1.0},
    ...           imt.PGV(): {"a": 0.5, "b": 10.0}}
    >>> ct = CoeffsTable.fromdict(coeffs)
    """

    @classmethod
    def fromdict(cls, ddic, logratio=True, opt=0):
        """
        :param ddic: a dictionary of dictionaries
        :param logratio: flag (default True)
        :param opt: int (default 0)
        """
        firstdic = ddic[next(iter(ddic))]
        self = object.__new__(cls)
        self.rb = RecordBuilder(**firstdic)
        self._coeffs = {}
        for imt, dic in ddic.items():
            if isinstance(imt, str):
                imt = from_string(imt)
            self._coeffs[imt] = self.rb(**dic) 
        self.logratio = logratio
        self.opt = opt
        return self

    @classmethod
    def fromtoml(cls, string):
        """
        Builds a CoeffsTable from a TOML string
        """
        return cls.fromdict(toml.loads(string))

    def __init__(self, table, **kwargs):
        self._coeffs = {}  # cache
        self.opt = kwargs.pop('opt', 0)
        self.logratio = kwargs.pop('logratio', True)
        sa_damping = kwargs.pop('sa_damping', None)
        if kwargs:
            raise TypeError('CoeffsTable got unexpected kwargs: %r' % kwargs)
        self.rb = self._setup_table_from_str(table, sa_damping)
        if self.opt == 1:
            imts = list(self._coeffs)
            periods = np.array([imt.period for imt in imts])
            idxs = np.argsort(periods)
            # regular array, if you want a composite one use .to_array()
            self.cmtx = np.array([self._coeffs[imts[i]].tolist() for i in idxs])
            self.periods = periods[idxs]

    def _setup_table_from_str(self, table, sa_damping):
        """
        Builds the input tables from a string definition
        """
        lines = table.strip().splitlines()
        header = lines.pop(0).split()
        if not header[0].upper() == "IMT":
            raise ValueError('first column in a table must be IMT')
        dt = RecordBuilder(**{name: 0. for name in header[1:]})
        for line in lines:
            row = line.split()
            imt_name_or_period = (
                row[0] if row[0].startswith("AvgSA") or
                row[0].startswith("SDi") else row[0].upper())
            if imt_name_or_period == 'SA':  # protect against stupid mistakes
                raise ValueError('specify period as float value '
                                 'to declare SA IMT')
            imt = from_string(imt_name_or_period, sa_damping)
            self._coeffs[imt] = dt(*row[1:])
        return dt

    @property
    def sa_coeffs(self):
        return {imt: self._coeffs[imt] for imt in self._coeffs
                if imt.string[:2] in SA_LIKE_PREFIXES}

    @property
    def non_sa_coeffs(self):
        return {imt: self._coeffs[imt] for imt in self._coeffs
                if imt.string[:2] not in SA_LIKE_PREFIXES}

    def get_coeffs(self, coeff_list):
        """
        :param coeff_list:
            A list with the names of the coefficients
        """
        coeffs = []
        pof = []
        for imt in self._coeffs:
            if re.search('^(SA|EAS|FAS|DRVT)', imt.string):
                tmp = np.array(self._coeffs[imt])
                coeffs.append([tmp[i] for i in coeff_list])
                if re.search('^(SA|AvgSA|SDi)', imt.string):
                    pof.append(imt.period)
                elif re.search('^(EAS|FAS|DRVT)', imt.string):
                    pof.append(imt.frequency)
                else:
                    raise ValueError('Unknown IMT: {:s}'.format(imt.string))
        pof = np.array(pof)
        coeffs = np.array(coeffs)
        idx = np.argsort(pof)
        pof = pof[idx]
        coeffs = coeffs[idx, :]
        return pof, coeffs

    def __iter__(self):
        return iter(self._coeffs)

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``
        from this table (if there is a line for requested IMT in it),
        or the dictionary of interpolated coefficients, if ``imt`` is
        of type :class:`~openquake.hazardlib.imt.SA` and interpolation
        is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        try:  # see if already in cache
            return self._coeffs[imt]
        except KeyError:  # populate the cache
            pass

        if self.opt == 0:
            max_below = min_above = None
            for unscaled_imt in self.sa_coeffs:
                if unscaled_imt.damping != getattr(imt, 'damping', None):
                    pass
                elif unscaled_imt.period > imt.period:
                    if (min_above is None or
                           unscaled_imt.period < min_above.period):
                        min_above = unscaled_imt
                elif unscaled_imt.period < imt.period:
                    if (max_below is None or
                           unscaled_imt.period > max_below.period):
                        max_below = unscaled_imt
            if max_below is None or min_above is None:
                raise KeyError(imt)
            if self.logratio:  # regular case
                # ratio tends to 1 when target period tends to a minimum
                # known period above and to 0 if target period is close
                # to maximum period below.
                ratio = ((math.log(imt.period) - math.log(max_below.period)) /
                         (math.log(min_above.period) -
                          math.log(max_below.period)))
            else:  # in the ACME project
                ratio = ((imt.period - max_below.period) /
                         (min_above.period - max_below.period))
            below = self.sa_coeffs[max_below]
            above = self.sa_coeffs[min_above]
            lst = [(above[n] - below[n]) * ratio + below[n]
                   for n in self.rb.names]
            self._coeffs[imt] = c = self.rb(*lst)

        elif self.opt == 1:
            if imt.period < self.periods[0] or imt.period > self.periods[-1]:
                raise KeyError(imt)
            fit = scipy.interpolate.interp1d(np.log10(self.periods), self.cmtx,
                                             axis=0, kind='cubic')
            vals = fit(np.log10(imt.period))
            self._coeffs[imt] = c = self.rb(*vals)
        return c

    def update_coeff(self, coeff_name, value_by_imt):
        """
        Update a coefficient in the table.

        :param coeff_name: name of the coefficient
        :param value_by_imt: dictionary imt -> coeff_value
        """
        for imt, coeff_value in value_by_imt.items():
            self._coeffs[imt][coeff_name] = coeff_value

    def __or__(self, other):
        """
        :param other: a subtable of self
        :returns: a new table obtained by overriding self with other
        """
        for imt in other._coeffs:
            assert imt in self._coeffs, imt
        new = copy.deepcopy(self)
        for name in other.rb.names:
            by_imt = {imt: rec[name] for imt, rec in other._coeffs.items()}
            new.update_coeff(name, by_imt)
        return new

    def __ior__(self, other):
        """
        :param other: a subtable of self
        :returns: a new table obtained by overriding self with other
        """
        return self | other

    def assert_equal(self, other):
        """
        Compare two tables of coefficients
        """
        assert sorted(self) == sorted(other), (sorted(self), sorted(other))
        for imt in self:
            rec0 = self[imt]
            rec1 = other[imt]
            names = rec0.dtype.names
            assert rec1.dtype.names == names, (rec1.dtype.names, names)
            for name in names:
                assert rec0[name] == rec1[name], (name, rec0[name], rec1[name])

    def get_diffs(self, other):
        """
        :returns: a list of tuples [(imt, field, value_self, value_other), ...]
        """
        assert sorted(self) == sorted(other), (sorted(self), sorted(other))
        diffs = []
        for imt in self:
            rec0 = self[imt]
            rec1 = other[imt]
            names = rec0.dtype.names
            assert rec1.dtype.names == names, (rec1.dtype.names, names)
            for name in names:
                if rec0[name] != rec1[name]:
                    diffs.append((imt.string, name, rec0[name], rec1[name]))
        return diffs

    def to_array(self):
        """
        :returns: a composite array with the coefficient names as columns
        """
        return np.array([self[imt] for imt in self._coeffs])

    def to_dict(self):
        """
        :returns: a double dictionary imt -> coeff -> value
        """
        ddic = {}
        for imt, rec in self._coeffs.items():
            ddic[imt.string] = dict(zip(rec.dtype.names, map(float, rec)))
        return ddic

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, ' '.join(self.rb.names))
