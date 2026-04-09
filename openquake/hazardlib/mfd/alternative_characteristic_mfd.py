# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
Module :mod:`openquake.hazardlib.mfd.alternative_characteristic_mfd`
defines an alternative characteristic MFD.
"""
import numpy as np

from openquake.baselib.general import round
from openquake.hazardlib.mfd.base import BaseMFD


class AlternativeCharacteristicMFD(BaseMFD):
    """
    Alternative characteristic (AC) magnitude-frequency distribution.

    Composed of two double-truncated exponential distributions
    "back-to-back":

    1. GR zone (min_mag to max_mag minus delta_m_AC): a standard
       truncated Gutenberg-Richter with b-value of b_GR.
    2. AC zone (delta_m_AC wide, up to max_mag): a second
       truncated exponential with its own b-value of b_AC.

    delta_m_AC is the width of the AC zone in magnitude units.

    The two zones are linked by the gamma value which is the fraction
    of the total seismic moment rate assigned to the AC zone according
    to equation 1.2 of the BC Hydro memo on AC MFDs::

        N_GR = ((1-gamma)/gamma) * N_AC
               * b_AC * (f_AC - g_AC) * (c - b_GR) * (1 - f_GR)
               / (b_GR * (c - b_AC) * g_AC * f_GR * (1 - f_AC))

    where

        f_GR = 10 ** (-b_GR * delta_m_GR)
        f_AC = 10 ** (-b_AC * delta_m_AC)
        delta_m_GR = max_mag - delta_m_AC - min_mag
        g_AC = 10 ** (-c * delta_m_AC)
        c = magnitude-moment relation exponent (1.5)

    Within each zone the annual occurrence rate for a magnitude bin
    [mag_lo, mag_hi] follows the truncated-GR form:

        rate = 10 ** (a - b * mag_lo) - 10 ** (a - b * mag_hi)

    using the zone-specific a and b values.

    :param min_mag:
        Minimum magnitude (m0). The first histogram bin will be aligned
        so its left border matches this value.
    :param max_mag:
        Maximum magnitude (mu). The last histogram bin will correspond
        to max_mag - bin_width / 2.
    :param bin_width:
        A positive float representing the width of a single histogram bin.
    :param b_GR:
        b-value for the GR zone.
    :param b_AC:
        b-value for the AC zone.
    :param gamma:
        Fraction of total seismic moment rate assigned to the AC zone
        (0 < gamma < 1).
    :param delta_m_AC:
        Width of the AC zone in magnitude units.
    :param total_rate:
        Total annual rate N(m0) of earthquakes with magnitude >= min_mag.

    The magnitude-moment relation exponent c is fixed at 1.5
    (i.e. log10(M0) = 1.5 * M + d).

    Values for ``min_mag`` and ``max_mag`` don't have to be aligned with
    respect to ``bin_width``. They get rounded accordingly anyway so that
    both are divisible by ``bin_width`` just before converting a function
    to a histogram. See :meth:`_get_min_mag_and_num_bins`.
    """
    MODIFICATIONS = {'set_max_mag',
                     'set_bGR',
                     'set_bAC',        
                     'increment_b_GR', 
                     'increment_b_AC', 
                     'increment_max_mag',
                     'increment_max_mag_no_mo_balance'}

    def __init__(self, min_mag, max_mag, bin_width, b_GR, b_AC,
                 gamma, delta_m_AC, total_rate):
        self.min_mag = min_mag
        self.max_mag = max_mag
        self.bin_width = bin_width
        self.b_GR = b_GR
        self.b_AC = b_AC
        self.gamma = gamma
        self.delta_m_AC = delta_m_AC
        self.total_rate = total_rate
        self.check_constraints()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Bin width is greater than 0.
        * Minimum magnitude is positive.
        * Maximum magnitude exceeds minimum magnitude by at least one
          bin width.
        * Both b-values are positive.
        * gamma is between 0 and 1.
        * delta_m_AC is positive and leaves room for the GR zone.
        * b_AC != 1.5 (would make moment integral diverge).
        * total_rate is positive.
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

        if self.b_GR <= 0:
            raise ValueError('b_GR %g must be positive' % self.b_GR)

        if self.b_AC <= 0:
            raise ValueError('b_AC %g must be positive' % self.b_AC)

        # AC MFD specific checks
        if self.b_AC == 1.5:
            raise ValueError('b_AC cannot equal c_val (1.5); the moment '
                             'rate integral for AC zone diverges')

        if not (0 < self.gamma < 1):
            raise ValueError('gamma %g must be between 0 and 1' % self.gamma)

        if self.delta_m_AC <= 0:
            raise ValueError('delta_m_AC %g must be positive' % self.delta_m_AC)

        m_c = self.max_mag - self.delta_m_AC
        if m_c <= self.min_mag:
            raise ValueError(
                'AC zone boundary (max_mag - delta_m_AC = %g) must be '
                'greater than min_mag %g' % (m_c, self.min_mag))

        if self.total_rate <= 0:
            raise ValueError('total_rate %g must be positive'
                             % self.total_rate)

    def _compute_zone_rates(self):
        """
        Partition total_rate into N_GR and N_AC using the
        moment-rate balance equation (1.2) of BC Hydro AC
        memo.

        :returns:
            Tuple (n_GR, n_AC) of annual occurrence rates.
        """
        c = 1.5
        m_c = self.max_mag - self.delta_m_AC # Boundary magnitude that seps
                                             # the GR zone from the AC zone
        delta_m_GR = m_c - self.min_mag # Width of the GR zone

        # Compute the truncation factor for each zone
        f_GR = 10.0 ** (-self.b_GR * delta_m_GR)
        f_AC = 10.0 ** (-self.b_AC * self.delta_m_AC)
        g_AC = 10.0 ** (-c * self.delta_m_AC)

        # Equation 1.2 in BCHydro AC memo
        gamma_part = (1.0 - self.gamma) / self.gamma
        numerator = self.b_AC * (f_AC - g_AC) * (c - self.b_GR) * (1.0 - f_GR)
        denominator = self.b_GR * (c - self.b_AC) * g_AC * f_GR * (1.0 - f_AC)
        ratio_nGR_nAC = gamma_part * (numerator / denominator)

        # Compute rates now we have partitioning ratio
        n_AC = self.total_rate / (ratio_nGR_nAC + 1.0)
        n_GR = ratio_nGR_nAC * n_AC

        return n_GR, n_AC

    def _get_zone_a_values(self):
        """
        Compute the cumulative a value for each zone.

        For a truncated-GR on [m_lo, m_hi] with rate N and b-value b:

            N = 10^(a - b*m_lo) - 10^(a - b*m_hi)
            a = log10(N) - log10(10^(-b*m_lo) - 10^(-b*m_hi))

        :returns:
            Tuple (a_GR, a_AC)
        """
        # Get the activity rate for each zone
        n_GR, n_AC = self._compute_zone_rates()

        # Get the boundary magnitude that seperates AC and GR zones
        m_c = self.max_mag - self.delta_m_AC

        # Compute the a-value for GR zone (use inputted mmin for GR zone
        # and m_c for mmax of GR zone)
        a_GR = (np.log10(n_GR) - np.log10(10.0 ** (
            -self.b_GR * self.min_mag) - 10.0 ** (-self.b_GR * m_c)))

        # Compute the a-value for AC zone (use m_c for mmin of AC zone
        # and inputted mmax for mmax of AC zone)
        a_AC = (np.log10(n_AC) - np.log10(10.0 ** (
            -self.b_AC * m_c) - 10.0 ** (-self.b_AC * self.max_mag)))

        return a_GR, a_AC

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
        Return the minimum and maximum magnitudes of the histogram.
        """
        min_mag, num_bins = self._get_min_mag_and_num_bins()
        return min_mag, min_mag + self.bin_width * (num_bins - 1)

    def get_annual_occurrence_rates(self):
        """
        Calculate and return the annual occurrence rates histogram.

        Bins that fall entirely in the GR zone use (a_GR, b_GR)

        Bins that fall entirely in the AC zone use (a_AC, b_AC)
        
        A bin that straddles the zone boundary of m_c (equal to
        max_mag - delta_m_AC) is split at this magnitude and the
        two contributions summed.

        :returns:
            See :meth:
            `openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`.
        """
        # Get the a-values
        a_GR, a_AC = self._get_zone_a_values()
        
        # Get the boundary between GR and AC zones
        m_c = self.max_mag - self.delta_m_AC

        def _bin_rate(a, b, m_lo, m_hi):
            return 10.0 ** (a - b * m_lo) - 10.0 ** (a - b * m_hi)

        # Get the histogram of annual rates for the MFD
        mag, num_bins = self._get_min_mag_and_num_bins()
        rates = []
        for _ in range(num_bins):

            # Get bin edges
            mag_lo = mag - self.bin_width / 2.0
            mag_hi = mag + self.bin_width / 2.0

            # Compute rate based on which zone the mag bin edges fall in
            if mag_hi <= m_c:
                # In GR zone
                rate = _bin_rate(a_GR, self.b_GR, mag_lo, mag_hi)
            elif mag_lo >= m_c:
                # In AC zone
                rate = _bin_rate(a_AC, self.b_AC, mag_lo, mag_hi)
            else:
                # Bin straddles boundary so split at m_c and sum rates
                rate = _bin_rate(a_GR, self.b_GR, mag_lo, m_c
                                 ) + _bin_rate(a_AC, self.b_AC, m_c, mag_hi)

            # Store the rates
            rates.append((mag, rate))
            
            # Increase the mag bin centre point using bin width
            mag += self.bin_width

        return rates

    def _get_total_moment_rate(self):
        """
        Calculate total moment rate (total energy released per
        unit time) in N*m/year (sum of both zones).

        For each zone [m_lo, m_hi] with a-value and b-value:

            ai = a + log10(b) + 9.05
            bi = 1.5 - b
            TMR = (10**ai / bi) * (10**(bi*m_hi) - 10**(bi*m_lo))

        In case of bi == 0 the following formula is applied:

            TMR = (10 ** ai) * (max_mag - min_mag)

        :returns:
            Float, calculated TMR value in N * m / year
            (Newton-meter per year).
        """
        # Get the a-value per zone
        a_GR, a_AC = self._get_zone_a_values()
        
        # Get the boundary magnitude of the zones
        m_c = self.max_mag - self.delta_m_AC

        def _zone_tmr(a, b, m_lo, m_hi):
            ai = 9.05 + a + np.log10(b)
            bi = 1.5 - b
            if bi == 0:
                # Avoid a division by zero in the integral
                return (10.0 ** ai) * np.log(10.0) * (m_hi - m_lo)
                
            return ((10.0 ** ai) / bi) * (
                10.0 ** (bi * m_hi) - 10.0 ** (bi * m_lo))
        
        return (_zone_tmr(a_GR, self.b_GR, self.min_mag, m_c)
                + _zone_tmr(a_AC, self.b_AC, m_c, self.max_mag))

    def modify_set_max_mag(self, value):
        """
        Apply absolute maximum magnitude modification.

        :param value:
            A float value to assign to ``max_mag``.

        No recalculation of other parameters is done after
        assigning a new value to ``max_mag``.
        """
        self.max_mag = value

    def modify_set_bGR(self, b_val: float):
        """
        Update the b-value of the GR zone.

        :param b_val:
            New GR zone b-value.
        """
        self.b_GR = b_val

    def modify_set_bAC(self, b_val: float):
        """
        Update the b-value of the AC zone.

        :param b_val:
            New AC zone b-value.
        """
        self.b_AC = b_val

    def modify_increment_b_GR(self, value):
        """
        Apply relative b_GR modification, preserving total moment rate.

        :param value:
            A float value to add to b_GR.

        After changing b_GR, total_rate is rescaled so that the
        total moment rate is unchanged.
        """
        # Get the TMR
        tmr = self._get_total_moment_rate()
        
        # Apply b-value delta to GR zone b-value
        self.b_GR += value

        # Check it's ok to apply the delta
        self.check_constraints() 

        # Rescale - TMR is linearly proportional to total_rate
        tmr_unit = self._get_total_moment_rate() / self.total_rate

        # Set the new total_rate to preserve the original TMR
        self.total_rate = tmr / tmr_unit

    def modify_increment_b_AC(self, value):
        """
        Apply relative b_AC modification, preserving total moment rate.

        :param value:
            A float value to add to b_AC.

        After changing b_AC, total_rate is rescaled so that the total
        moment rate is unchanged.
        """
        # Get the TMR
        tmr = self._get_total_moment_rate()
        
        # Apply b-value delta to AC zone b-value
        self.b_AC += value

        # Check it's ok to apply the delta
        self.check_constraints() 

        # Rescale - TMR is linearly proportional to total_rate
        tmr_unit = self._get_total_moment_rate() / self.total_rate

        # Set the new total_rate to preserve the original TMR
        self.total_rate = tmr / tmr_unit

    def modify_increment_max_mag(self, value):
        """
        Apply relative maximum magnitude modification, preserving
        total moment rate.

        :param value:
            A float value to add to max_mag.

        After changing max_mag, total_rate is rescaled so that
        the total moment rate is unchanged
        
        NOTE: because delta_m_AC is not changed, the GR zone
        inherently absorbs the change.
        """
        # Get the TMR
        tmr = self._get_total_moment_rate()

        # Apply max_mag delta
        self.max_mag += value

        # Check it's ok to apply the given delta
        self.check_constraints()

        # Rescale - TMR is linearly proportional to total_rate
        tmr_unit = self._get_total_moment_rate() / self.total_rate

        # Set the new total_rate to preserve the original TMR
        self.total_rate = tmr / tmr_unit

    def modify_increment_max_mag_no_mo_balance(self, value):
        """
        Apply relative maximum magnitude modification.

        :param value:
            A float value to add to ``max_mag``.
        """
        self.max_mag += value

    @classmethod
    def from_moment(cls, min_mag, max_mag, bin_width, b_GR, b_AC,
                    gamma, delta_m_AC, moment_rate):
        """
        :param min_mag:
            The lowest possible magnitude for this MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` will be
            aligned to make its left border match this value.
        :param max_mag:
            The highest possible magnitude. The same as for ``min_mag``: the
            last bin in the histogram will correspond to the magnitude value
            equal to ``max_mag - bin_width / 2``.
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :param b_GR:
            b-value for the GR zone.
        :param b_AC:
            b-value for the AC zone.
        :param gamma:
            Fraction of total seismic moment rate assigned to the AC zone
            (0 < gamma < 1).
        :param delta_m_AC:
            Width of the AC zone in magnitude units.
        :param moment_rate:
            The value of scalar seismic moment per year released by this MFD.
            Unit of measure is N * m.
        """
        unit = cls(min_mag, max_mag, bin_width,
                   b_GR, b_AC, gamma, delta_m_AC, total_rate=1.0)
        tmr_unit = unit._get_total_moment_rate()
        total_rate = moment_rate / tmr_unit
        return cls(min_mag, max_mag, bin_width,
                   b_GR, b_AC, gamma, delta_m_AC, total_rate)

    @classmethod
    def from_slip_rate(cls, min_mag, max_mag, bin_width, b_GR, b_AC,
                       gamma, delta_m_AC, slip_rate, rigidity, area):
        """
        Calls .from_moment with moment = slip_rate * rigidity * area

        :param min_mag:
            The lowest possible magnitude for this MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` will be
            aligned to make its left border match this value.
        :param max_mag:
            The highest possible magnitude. The same as for ``min_mag``: the
            last bin in the histogram will correspond to the magnitude value
            equal to ``max_mag - bin_width / 2``.
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :param b_GR:
            b-value for the GR zone.
        :param b_AC:
            b-value for the AC zone.
        :param gamma:
            Fraction of total seismic moment rate assigned to the AC zone
            (0 < gamma < 1).
        :param delta_m_AC:
            Width of the AC zone in magnitude units.
        :param slip_rate:
            A float defining the slip rate [mm/yr].
        :param rigidity:
            A float defining the rigidity [GPa].
        :param area:
            A float defining the area of the fault surface [km^2].
        """
        mm = 1E-3  # conversion millimiters -> meters
        moment_rate = (slip_rate * mm) * (rigidity * 1e9) * (area * 1e6)
        obj = cls.from_moment(min_mag, max_mag, bin_width, b_GR, b_AC,
                              gamma, delta_m_AC, moment_rate)
        obj.slip_rate = slip_rate
        obj.rigidity = rigidity
        return obj
