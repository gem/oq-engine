# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.mfd.truncated_gr` defines a Truncated
Gutenberg-Richter MFD.
"""
import math
import numpy as np
from openquake.baselib.python3compat import round
from openquake.hazardlib.mfd.base import BaseMFD


class TruncatedGRMFD(BaseMFD):
    """
    Truncated Gutenberg-Richter MFD is defined in a functional form.

    The annual occurrence rate for a specific bin (magnitude band)
    is defined as ::

        rate = 10 ** (a_val - b_val * mag_lo) - 10 ** (a_val - b_val * mag_hi)

    where

    * ``a_val`` is the cumulative ``a`` value (``10 ** a`` is the number
      of earthquakes per year with magnitude greater than or equal to 0),
    * ``b_val`` is Gutenberg-Richter ``b`` value -- the decay rate
      of exponential distribution. It describes the relative size distribution
      of earthquakes: a higher ``b`` value indicates a relatively larger
      proportion of small events and vice versa.
    * ``mag_lo`` and ``mag_hi`` are lower and upper magnitudes of a specific
      bin respectively.

    :param min_mag:
        The lowest possible magnitude for this MFD. The first bin in the
        :meth:`result histogram <get_annual_occurrence_rates>` will be aligned
        to make its left border match this value.
    :param max_mag:
        The highest possible magnitude. The same as for ``min_mag``: the last
        bin in the histogram will correspond to the magnitude value equal to
        ``max_mag - bin_width / 2``.
    :param bin_width:
        A positive float value -- the width of a single histogram bin.

    Values for ``min_mag`` and ``max_mag`` don't have to be aligned with
    respect to ``bin_width``. They get rounded accordingly anyway so that
    both are divisible by ``bin_width`` just before converting a function
    to a histogram. See :meth:`_get_min_mag_and_num_bins`.
    """
    MODIFICATIONS = {'increment_max_mag', 'set_max_mag', 'increment_b',
                     'set_ab', 'set_bGR', 'increment_max_mag_no_mo_balance'}

    def __init__(self, min_mag, max_mag, bin_width, a_val, b_val):
        self.min_mag = min_mag
        self.max_mag = max_mag
        self.bin_width = bin_width
        self.a_val = a_val
        self.b_val = b_val
        self.check_constraints()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Bin width is greater than 0.
        * Minimum magnitude is positive.
        * Maximum magnitude is greater than minimum magnitude
          by at least one bin width (or equal to that value).
        * ``b`` value is positive.
        """
        if not self.bin_width > 0:
            raise ValueError('bin width %g must be positive' % self.bin_width)

        if not self.min_mag >= 0:
            raise ValueError('minimum magnitude %g must be non-negative'
                             % self.min_mag)

        if not self.max_mag >= self.min_mag + self.bin_width:
            raise ValueError('maximum magnitude %g must be higher than '
                             'minimum magnitude %g by '
                             'bin width %g at least'
                             % (self.max_mag, self.min_mag, self.bin_width))

        if self.b_val <= 0:
            raise ValueError('b-value %g must be non-negative' % self.b_val)
        if not np.isfinite(self.a_val):
            raise ValueError(self.a_val)

    def _get_rate(self, mag):
        """
        Calculate and return an annual occurrence rate for a specific bin.

        :param mag:
            Magnitude value corresponding to the center of the bin of interest.
        :returns:
            Float number, the annual occurrence rate calculated using formula
            described in :class:`TruncatedGRMFD`.
        """
        mag_lo = mag - self.bin_width / 2.0
        mag_hi = mag + self.bin_width / 2.0
        return (10 ** (self.a_val - self.b_val * mag_lo)
                - 10 ** (self.a_val - self.b_val * mag_hi))

    def _get_min_mag_and_num_bins(self):
        """
        Estimate the number of bins in the histogram and return it
        along with the first bin center abscissa (magnitude) value.

        Rounds ``min_mag`` and ``max_mag`` with respect to ``bin_width``
        to make the distance between them include integer number of bins.

        :returns:
            A tuple of two items: first bin center and total number of bins.
        """
        min_mag = round(self.min_mag / self.bin_width) * self.bin_width
        max_mag = round(self.max_mag / self.bin_width) * self.bin_width
        if min_mag != max_mag:
            min_mag += self.bin_width / 2.0
            max_mag -= self.bin_width / 2.0
        # here we use math round on the result of division and not just
        # cast it to integer because for some magnitude values that can't
        # be represented as an IEEE 754 double precisely the result can
        # look like 7.999999999999 which would become 7 instead of 8
        # being naively casted to int so we would lose the last bin.
        num_bins = int(round((max_mag - min_mag) / self.bin_width)) + 1
        return min_mag, num_bins

    def get_min_max_mag(self):
        """
        Return the minum magnitude
        """
        min_mag, num_bins = self._get_min_mag_and_num_bins()
        return min_mag, min_mag + self.bin_width * (num_bins - 1)

    def get_annual_occurrence_rates(self):
        """
        Calculate and return the annual occurrence rates histogram.

        The result histogram has only one bin if minimum and maximum magnitude
        values appear equal after rounding.

        :returns:
            See :meth:
            `openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`.
        """
        mag, num_bins = self._get_min_mag_and_num_bins()
        rates = []
        for i in range(num_bins):
            rate = self._get_rate(mag)
            rates.append((mag, rate))
            mag += self.bin_width
        return rates

    def _get_total_moment_rate(self):
        """
        Calculate total moment rate (total energy released per unit time) ::

            TMR = ((10**ai) / bi) * (10 ** (bi*max_mag) - 10 ** (bi*min_mag))

        where ``ai = a + log10(b) + 9.05`` and ``bi = 1.5 - b``.
        In case of ``bi == 0`` the following formula is applied::

            TMR = (10 ** ai) * (max_mag - min_mag)

        :returns:
            Float, calculated TMR value in ``N * m / year``
            (Newton-meter per year).
        """
        ai = 9.05 + self.a_val + math.log10(self.b_val)
        bi = 1.5 - self.b_val
        if bi == 0.0:
            return (10 ** ai) * (self.max_mag - self.min_mag)
        else:
            return (((10 ** ai) / bi) *
                    (10 ** (bi * self.max_mag) - 10 ** (bi * self.min_mag)))

    def _set_a(self, tmr):
        """
        Recalculate an ``a`` value preserving a total moment rate ``tmr`` ::

            a = (log10((tmr * bi) / (10 ** (bi*max_mag) - 10 ** (bi*min_mag)))
                 - 9.05 - log10(b))

        where ``bi = 1.5 - b``. If ``bi == 0`` the following formula is used:

            a = log10(tmr / (max_mag - min_mag)) - 9.05 - log10(b)
        """
        bi = 1.5 - self.b_val
        if bi == 0.0:
            self.a_val = (math.log10(tmr / (self.max_mag - self.min_mag))
                          - 9.05
                          - math.log10(self.b_val))
        else:
            self.a_val = (math.log10(tmr * bi / (10 ** (bi * self.max_mag)
                                                 - 10 ** (bi * self.min_mag)))
                          - 9.05
                          - math.log10(self.b_val))

    def modify_increment_max_mag_no_mo_balance(self, value):
        """
        Apply relative maximum magnitude modification.

        :param value:
            A float value to add to ``max_mag``.
        """
        self.max_mag += value


    def modify_increment_max_mag(self, value):
        """
        Apply relative maximum magnitude modification.

        :param value:
            A float value to add to ``max_mag``.

        The Gutenberg-Richter ``a`` value is :meth:`recalculated <_set_a>`
        with respect to old :meth:`total moment rate <_get_total_moment_rate>`.
        """
        tmr = self._get_total_moment_rate()
        self.max_mag += value
        # need to check constraints here because _set_a() would die
        # if new max_mag <= min_mag.
        self.check_constraints()
        self._set_a(tmr)

    def modify_set_max_mag(self, value):
        """
        Apply absolute maximum magnitude modification.

        :param value:
            A float value to assign to ``max_mag``.

        No specific recalculation of other Gutenberg-Richter parameters
        is done after assigning a new value to ``max_mag``.
        """
        self.max_mag = value

    def modify_set_bGR(self, b_val: float):
        """
        Updates the b_value of the GR relationship.

        :param b_val:
            The value of the new maximum magnitude
        """
        self.b_val = b_val

    def modify_increment_b(self, value):
        """
        Apply relative ``b``-value modification.

        :param value:
            A float value to add to ``b_val``.

        After changing ``b_val`` the ``a_val`` is recalculated the same
        way as for :meth:`modify_increment_max_mag` (with
        respect to TMR).
        """
        tmr = self._get_total_moment_rate()
        self.b_val += value
        self.check_constraints()
        self._set_a(tmr)

    def modify_set_ab(self, a_val, b_val):
        """
        Apply absolute ``a`` and ``b`` values modification.

        :param a_val:
            A float value to use as a new ``a_val``.
        :param b_val:
            A float value to use as a new ``b_val``.

        No recalculation of other Gutenberg-Richter parameters is done.
        """
        self.b_val = b_val
        self.a_val = a_val

    @classmethod
    def from_moment(cls, min_mag, max_mag, bin_width, b_val, moment_rate,
                    d_val=9.1):
        """
        :param min_mag:
            The lowest possible magnitude for this MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` will be
            aligned  to make its left border match this value.
        :param max_mag:
            The highest possible magnitude. The same as for ``min_mag``: the
            last bin in the histogram will correspond to the magnitude value
            equal to ``max_mag - bin_width / 2``.
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :param b_val:
            The slope of the GR relationship
        :param moment_rate:
            The value of scalar seismic moment per year released by this MFD.
            Unit of measure is N ・m
        :param d_val:
            The constant term of the equation used to compute moment from
            magnitude. Set to 9.1 for backcompatibility.
        """
        c_val = 1.5
        tmp = 0
        mou = 10**(c_val * max_mag + d_val)
        beta = b_val * np.log(10.0)
        term2 = np.exp(-beta*(max_mag - tmp))
        rate = (moment_rate * (c_val - b_val) * (1 - term2) /
                (b_val * mou * term2))
        a_val = np.log10(rate)
        self = cls(min_mag, max_mag, bin_width, a_val, b_val)
        return self

    @classmethod
    def from_slip_rate(cls, min_mag, max_mag, bin_width, b_val,
                       slip_rate, rigidity, area, constant_term=9.1):
        """
        Calls .from_moment with moment = slip_rate * rigidity * area

        :param min_mag:
            The lowest possible magnitude for this MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` will be
            aligned  to make its left border match this value.
        :param max_mag:
            The highest possible magnitude. The same as for ``min_mag``: the
            last bin in the histogram will correspond to the magnitude value
            equal to ``max_mag - bin_width / 2``.
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :param b_val:
            The slope of the GR relationship
        :param slip_rate:
            A float defining the slip rate [mm/yr]
        :param rigidity:
            A float defining the rigidity [GPa]
        :param area:
            A float defining the area of the fault surface [km^2]
        :param constant_term:
            A float defining the constant term of the equation used to
            compute the log M0 from magnitude.
        """
        mm = 1E-3  # conversion millimiters -> meters
        moment_rate = (slip_rate * mm) * (rigidity * 1e9) * (area * 1e6)
        self = cls.from_moment(min_mag, max_mag, bin_width, b_val, moment_rate,
                               constant_term)
        self.slip_rate = slip_rate
        self.rigidity = rigidity
        return self
