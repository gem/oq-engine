# coding: utf-8
# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.mfd.youngs_coppersmith_1985` defines the
Youngs and Coppersmith 1985 MFD.
"""
import numpy

from openquake.baselib.python3compat import range, round
from openquake.hazardlib.mfd.base import BaseMFD

# width of the boxcar function representing the characteristic
# distribution
DELTA_CHAR = 0.5


class YoungsCoppersmith1985MFD(BaseMFD):
    """
    Class implementing the MFD for the 'Characteristic Earthquake Model' as
    described in: "Implications of fault slip rates and earthquake recurrence
    models to probabilistic seismic hazard estimates", by Robert R. Youngs and
    Kevin J. Coppersmith and published in Bulletin of the Seismological
    Society of America, Vol. 75, No. 4, pages 939-964, 1985.
    The class implements the MFD under the following assumptions as reported
    at page 954:

    1) Δ_mc (width of the boxcar distribution representing characteristic
       rate) is equal to 0.5 magnitude unit
    2) m' (maximum magnitude value for the Gutenberg-Richeter part of the
       distribution) is equal to the absolute maximum magnitude minus Δ_mc
       (that is there is no gap between the Gutenberg-Richter distribution and
       the boxcar distribution)
    3) the rate of events at the characteristic magnitude is equal to the
       rate of events for magnitude equal to m' - 1

    :param min_mag:
        The lowest possible magnitude for the MFD. The first bin in the
        :meth:`result histogram <get_annual_occurrence_rates>` is aligned
        to make its left border match this value.
    :param a_val:
        The Gutenberg-Richter ``a`` value -- the intercept of the loglinear
        cumulative G-R relationship.
    :param b_val:
        The Gutenberg-Richter ``b`` value -- the gradient of the loglinear
        G-R relationship.
    :param char_mag:
        The characteristic magnitude defining the middle point of the
        characteristic distribution. That is the boxcar function representing
        the characteristic distribution is defined in the range
        [char_mag - 0.25, char_mag + 0.25].
    :param char_rate:
        The characteristic rate associated to the characteristic magnitude,
        to be distributed over the domain of the boxcar function representing
        the characteristic distribution (that is λ_char = char_rate / 0.5)
    :param bin_width:
        A positive float value -- the width of a single histogram bin.

    Values for ``min_mag`` and the maximum magnitude (char_mag + 0.25) don't
    have to be aligned with respect to ``bin_width``. They get rounded
    accordingly anyway so that both are divisible by ``bin_width`` just before
    converting a function to a histogram.
    See :meth:`_get_min_mag_and_num_bins`.
    """

    MODIFICATIONS = set()

    def __init__(self, min_mag, a_val, b_val, char_mag, char_rate, bin_width):
        self.min_mag = min_mag
        self.a_val = a_val
        self.b_val = b_val
        self.char_mag = char_mag
        self.char_rate = char_rate
        self.bin_width = bin_width

        self.check_constraints()

    def get_min_max_mag(self):
        "Return the minimum and maximum magnitudes"
        mag, num_bins = self._get_min_mag_and_num_bins()
        return mag, mag + self. bin_width * (num_bins - 1)

    def check_constraints(self):
        """
        Checks the following constraints:

        * minimum magnitude is positive.
        * ``b`` value is positive.
        * characteristic magnitude is positive
        * characteristic rate is positive
        * bin width is in the range (0, 0.5] to allow for at least one bin
          representing the characteristic distribution
        * characteristic magnitude minus 0.25 (that is the maximum magnitude
          of the G-R distribution) is greater than the minimum magnitude by at
          least one magnitude bin.
        * rate of events at the characteristic magnitude is equal to the
          rate of events for magnitude equal to m_prime - 1. This is done
          by asserting the equality (up to 7 digit precision) ::

            10 ** (a_incr - b * (m' - 1)) == char_rate / 0.5

          where ``a_incr`` is the incremental a value obtained from the
          cumulative a value using the following formula ::

            a_incr = a_val + log10(b_val * ln(10))

          and ``m' - 1 = char_mag - 1.25``
        """
        if not self.min_mag > 0:
            raise ValueError('minimum magnitude must be positive')

        if not self.b_val > 0:
            raise ValueError('b value must be positive')

        if not self.char_mag > 0:
            raise ValueError('characteristic magnitude must be positive')

        if not self.char_rate > 0:
            raise ValueError('characteristic rate must be positive')

        if not 0 < self.bin_width <= DELTA_CHAR:
            err_msg = 'bin width must be in the range (0, %s] to allow for ' \
                      'at least one magnitude bin representing the ' \
                      'characteristic distribution' % DELTA_CHAR
            raise ValueError(err_msg)

        if not self.char_mag - DELTA_CHAR / 2 >= self.min_mag + self.bin_width:
            err_msg = 'Maximum magnitude of the G-R distribution (char_mag ' \
                      '- 0.25) must be greater than the minimum magnitude ' \
                      'by at least one magnitude bin.'
            raise ValueError(err_msg)

        a_incr = self.a_val + numpy.log10(self.b_val * numpy.log(10))
        actual = 10 ** (a_incr - self.b_val * (self.char_mag - 1.25))
        desired = self.char_rate / DELTA_CHAR
        if not numpy.allclose(actual, desired, rtol=0.0, atol=1e-07):
            err_msg = 'Rate of events at the characteristic magnitude is ' \
                      'not equal to the rate of events for magnitude equal ' \
                      'to char_mag - 1.25'
            raise ValueError(err_msg)

    @classmethod
    def from_total_moment_rate(cls, min_mag, b_val, char_mag,
                               total_moment_rate, bin_width):
        """
        Define Youngs and Coppersmith 1985 MFD by constraing cumulative a
        value and characteristic rate from total moment rate.
        The cumulative a value and characteristic rate are obtained by
        solving equations (16) and (17), page 954, for the cumulative rate of
        events with magnitude greater than the minimum magnitude - N(min_mag)
        - and the cumulative rate of characteristic earthquakes - N(char_mag).
        The difference ``N(min_mag) - N(char_mag)`` represents the rate of
        noncharacteristic, exponentially distributed earthquakes and is used
        to derive the cumulative a value by solving the following equation ::

            10 ** (a_val - b_val * min_mag) -
            10 ** (a_val - b_val * (char_mag - 0.25))
            = N(min_mag) - N(char_mag)

        which can be written as ::

            a_val =
            log10(N(min_mag) - N(char_mag)) /
            (10 ** (- b_val * min_mag) - 10 ** (- b_val * (char_mag - 0.25))

        In the calculation of N(min_mag) and N(char_mag), the Hanks and
        Kanamori (1979) formula ::

            M0 = 10 ** (1.5 * Mw + 9.05)

        is used to convert moment magnitude (Mw) to seismic moment (M0,
        Newton × m)

        :param min_mag:
            The lowest magnitude for the MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` is aligned
            to make its left border match this value.
        :param b_val:
            The Gutenberg-Richter ``b`` value -- the gradient of the loglinear
            G-R relationship.
        :param char_mag:
            The characteristic magnitude defining the middle point of
            characteristic distribution. That is the boxcar function
            representing the characteristic distribution is defined in the
            range [char_mag - 0.25, char_mag + 0.25].
        :param total_moment_rate:
            Total moment rate in N * m / year.
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :returns:
            An instance of :class:`YoungsCoppersmith1985MFD`.

        Values for ``min_mag`` and the maximum magnitude (char_mag + 0.25)
        don't have to be aligned with respect to ``bin_width``. They get
        rounded accordingly anyway so that both are divisible by ``bin_width``
        just before converting a function to a histogram.
        See :meth:`_get_min_mag_and_num_bins`.
        """
        beta = b_val * numpy.log(10)
        mu = char_mag + DELTA_CHAR / 2
        m0 = min_mag

        # seismic moment (in Nm) for the maximum magnitude
        c = 1.5
        d = 9.05
        mo_u = 10 ** (c * mu + d)

        # equations (16) and (17) solved for N(min_mag) and N(char_mag)
        c1 = numpy.exp(-beta * (mu - m0 - 0.5))
        c2 = numpy.exp(-beta * (mu - m0 - 1.5))
        c3 = beta * c2 / (2 * (1 - c1) + beta * c2)
        c4 = (b_val * (10 ** (-c / 2)) / (c - b_val)) + \
             (b_val * numpy.exp(beta) * (1 - (10 ** (-c / 2))) / c)
        n_min_mag = (1 - c1) * total_moment_rate / ((1 - c3) * c1 * mo_u * c4)
        n_char_mag = c3 * n_min_mag

        a_val = numpy.log10(
            (n_min_mag - n_char_mag) /
            (10 ** (- b_val * min_mag) - 10 ** (- b_val * (char_mag - 0.25)))
        )

        return cls(min_mag, a_val, b_val, char_mag, n_char_mag, bin_width)

    @classmethod
    def from_characteristic_rate(cls, min_mag, b_val, char_mag, char_rate,
                                 bin_width):
        """
        Define Youngs and Coppersmith 1985 MFD by constraing cumulative a
        value from characteristic rate.
        The cumulative a value is obtained by making use of the property that
        the rate of events at m' - 1 must be equal to the rate at the
        characteristic magnitude, and therefore by first computing the
        incremental a value, using the following equation::

            10 ** (a_incr - b_val * (m_prime - 1)) == char_rate / 0.5

        where ``m' - 1 = char_mag - 1.25``.
        The cumulative a value is then obtained as ::

            a_val = a_incr - log10(b_val * ln(10))

        :param min_mag:
            The lowest magnitude for the MFD. The first bin in the
            :meth:`result histogram <get_annual_occurrence_rates>` is aligned
            to make its left border match this value.
        :param b_val:
            The Gutenberg-Richter ``b`` value -- the gradient of the loglinear
            G-R relationship.
        :param char_mag:
            The characteristic magnitude defining the middle point of
            characteristic distribution. That is the boxcar function
            representing the characteristic distribution is defined in the
            range [char_mag - 0.25, char_mag + 0.25].
        :param char_rate:
            The characteristic rate associated to the characteristic magnitude,
            to be distributed over the domain of the boxcar function
            representing the characteristic distribution (that is λ_char =
            char_rate / 0.5)
        :param bin_width:
            A positive float value -- the width of a single histogram bin.
        :returns:
            An instance of :class:`YoungsCoppersmith1985MFD`.

        Values for ``min_mag`` and the maximum magnitude (char_mag + 0.25)
        don't have to be aligned with respect to ``bin_width``. They get
        rounded accordingly anyway so that both are divisible by ``bin_width``
        just before converting a function to a histogram.
        See :meth:`_get_min_mag_and_num_bins`.
        """
        a_incr = b_val * (char_mag - 1.25) + numpy.log10(char_rate /
                                                         DELTA_CHAR)
        a_val = a_incr - numpy.log10(b_val * numpy.log(10))

        return cls(min_mag, a_val, b_val, char_mag, char_rate, bin_width)

    def _get_rate(self, mag):
        """
        Calculate and return the annual occurrence rate for a specific bin.

        :param mag:
            Magnitude value corresponding to the center of the bin of interest.
        :returns:
            Float number, the annual occurrence rate for the :param mag value.
        """
        mag_lo = mag - self.bin_width / 2.0
        mag_hi = mag + self.bin_width / 2.0

        if mag >= self.min_mag and mag < self.char_mag - DELTA_CHAR / 2:
            # return rate according to exponential distribution
            return (10 ** (self.a_val - self.b_val * mag_lo)
                    - 10 ** (self.a_val - self.b_val * mag_hi))
        else:
            # return characteristic rate (distributed over the characteristic
            # range) for the given bin width
            return (self.char_rate / DELTA_CHAR) * self.bin_width

    def _get_min_mag_and_num_bins(self):
        """
        Estimate the number of bins in the histogram and return it along with
        the first bin center value.

        Rounds ``min_mag`` and ``max_mag`` with respect to ``bin_width`` to
        make the distance between them include integer number of bins.

        :returns:
            A tuple of 2 items: first bin center, and total number of bins.
        """
        min_mag = round(self.min_mag / self.bin_width) * self.bin_width
        max_mag = (round((self.char_mag + DELTA_CHAR / 2) /
                   self.bin_width) * self.bin_width)
        min_mag += self.bin_width / 2.0
        max_mag -= self.bin_width / 2.0
        # here we use math round on the result of division and not just
        # cast it to integer because for some magnitude values that can't
        # be represented as an IEEE 754 double precisely the result can
        # look like 7.999999999999 which would become 7 instead of 8
        # being naively casted to int so we would lose the last bin.
        num_bins = int(round((max_mag - min_mag) / self.bin_width)) + 1
        return min_mag, num_bins

    def get_annual_occurrence_rates(self):
        """
        Calculate and return the annual occurrence rates histogram.

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
