# The Hazard Library
# Copyright (C) 2012-2020 GEM Foundation
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

# pylint: disable=missing-docstring,protected-access

import math

import numpy as np
from scipy.special import gammaincc, gamma

from openquake.hazardlib.mfd.base import BaseMFD
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD


class TaperedGRMFD(BaseMFD):
    """
    Tapered Gutenberg-Richter MFD is defined as a typical Truncated
    Gutenberg-Richter MFD up to a ``corner_mag`` above which an exponential
    taper is applied; see Kagan (2002a, Geophysical Journal International)
    for details. This implementation is based on
    the United States National Seismic Hazard Map Project code
    (https://github.com/usgs/nshmp-haz).

    :param min_mag:
        The lowest possible magnitude for this MFD. The first bin in the
        :meth:`result histogram <get_annual_occurrence_rates>` will be aligned
        to make its left border match this value.
    :param max_mag:
        The highest possible magnitude. The same as for ``min_mag``: the last
        bin in the histogram will correspond to the magnitude value equal to
        ``max_mag - bin_width / 2``.
    :param corner_mag:
        The magnitude above which the exponential tapering of the earthquake
        frequency (rate) occurs. Rates below this magnitude are identical to
        a Gutenberg-Richter with the same ``a`` and ``b`` values.
    :param bin_width:
        A positive float value -- the width of a single histogram bin.

    Values for ``min_mag`` and ``max_mag`` don't have to be aligned with
    respect to ``bin_width``. They get rounded accordingly anyway so that
    both are divisible by ``bin_width`` just before converting a function
    to a histogram. See :meth:`_get_min_mag_and_num_bins`.
    """

    MODIFICATIONS = set(())

    def __init__(self, 
                 min_mag: float, 
                 max_mag: float, 
                 corner_mag: float,
                 bin_width: float,
                 a_val: float,
                 b_val: float,
                 c_val: float=9.05):

        self.min_mag = min_mag
        self.max_mag = max_mag
        self.corner_mag = corner_mag
        self.bin_width = bin_width
        self.a_val = a_val
        self.b_val = b_val
        self.c_val = c_val

        self.beta = 2. / 3. * self.b_val

        # constants from Mfds.java
        self.SMALL_MO_MAG: float = 4.
        self.TAPERED_LARGE_MAG: float = 9.05

        self.min_mo = mag_to_mo(self.SMALL_MO_MAG)
        self.large_mo = mag_to_mo(self.TAPERED_LARGE_MAG)
        self.corner_mo = mag_to_mo(corner_mag)

        # This class uses a Double Truncated GR distribution, and the
        # rates are modified per the tapering.
        self._dt_gr = TruncatedGRMFD(self.min_mag, self.max_mag,
                                     self.bin_width, self.a_val, self.b_val)
        self._get_min_mag_and_num_bins = self._dt_gr._get_min_mag_and_num_bins

        self.check_constraints()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Bin width is greater than 0.
        * Minimum magnitude is positive.
        * Maximum magnitude is greater than minimum magnitude
          by at least one bin width (or equal to that value).
        * Corner magnitude is greater than minimum magnitude
          by at least one bin width (or equal to that value).
        * ``b`` value is positive.
        """
        if not self.bin_width > 0:
            raise ValueError('bin width %g must be positive' % self.bin_width)

        if not self.min_mag >= 0:
            raise ValueError('minimum magnitude %g must be non-negative' %
                             self.min_mag)

        if not self.max_mag >= self.min_mag + self.bin_width:
            raise ValueError('maximum magnitude %g must be higher than '
                             'minimum magnitude %g by '
                             'bin width %g at least' %
                             (self.max_mag, self.min_mag, self.bin_width))

        if not self.b_val > 0.:
            raise ValueError('b-value %g must be non-negative' % self.b_val)

        if not self.corner_mag >= self.min_mag + self.bin_width:
            raise ValueError('corner magnitude %g must be higher than '
                             'minimum magnitude %g by '
                             'bin width %g at least' %
                             (self.corner_mag, self.min_mag, self.bin_width))

    def _pareto(self, mo, corner_mo):
        """'pareto' function from nhsmp-haz
        """
        return (self.min_mo / mo)**self.beta * math.exp(
            (self.min_mo - mo) / corner_mo)

    def _scale_mag_bin_rate(self, mag, rate):
        """
        This function scales the TruncatedGRMFD rate for that bin using
        a tapering scheme developed in the NSHM-HAZ function; see
        Mfds.java in the nshmp-haz codebase.
        """

        mag_mo_lo = mag_to_mo(mag - self.bin_width / 2., c=self.c_val)
        mag_mo_hi = mag_to_mo(mag + self.bin_width / 2., c=self.c_val)

        scale_num = (self._pareto(mag_mo_lo, self.corner_mo) -
                     self._pareto(mag_mo_hi, self.corner_mo))

        scale_denom = (self._pareto(mag_mo_lo, self.large_mo) -
                       self._pareto(mag_mo_hi, self.large_mo))

        scale = scale_num / scale_denom

        return rate * scale

    def _get_rate(self, mag):
        """
        Calculate and return an annual occurrence rate for a specific bin.

        :param mag:
            Magnitude value corresponding to the center of the bin of interest.
        :returns:
            Float number, the annual occurrence rate
        """
        gr_rate = self._dt_gr._get_rate(mag)
        return self._scale_mag_bin_rate(mag, gr_rate)

    def get_min_max_mag(self):
        """
        Return the minimum and maximum magnitudes
        """
        return self._dt_gr.get_min_max_mag()

    def get_annual_occurrence_rates(self):
        """
        Calculate and return the annual occurrence rates histogram.

        The result histogram has only one bin if minimum and maximum magnitude
        values appear equal after rounding.

        :returns:
            See :meth:
            `openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`.
        """
        mag_rates = []

        gr_rates = self._dt_gr.get_annual_occurrence_rates()

        for mag, rate in gr_rates:
            mag_rates.append((mag, self._scale_mag_bin_rate(mag, rate)))

        return mag_rates

    def _H_interval(self, m_lo: float, m_hi: float):
        s = 1.0 - self.beta
        x_lo = 10.0 ** (1.5 * (m_lo - self.corner_mag))
        x_hi = 10.0 ** (1.5 * (m_hi - self.corner_mag))
        U = lambda x: _upper_gamma(s, x) + np.exp(-x) * (x **(1.0 - self.beta))
        return U(x_lo) - U(x_hi)

    def _get_total_moment_rate(self) -> float:
        """
        Exact total scalar moment rate (Nm/yr) over [min_mag, max_mag]
        """
        Mc = mag_to_mo(self.corner_mag, c=self.c_val)
        C = (10.0 ** (self.a_val + self.beta * self.c_val)
             ) * (Mc ** (1.0-self.beta))
        return C * self._H_interval(self.min_mag, self.max_mag)

    def _set_a(self, target_moment_rate: float):
        """
        Sets a_val so that the total moment rate equals the target moment rate.
        """
        if target_moment_rate <= 0.0:
            raise ValueError(
                    f"target_moment_rate {target_moment_rate} must be positive"
                    )
        H = self._H_interval(self.min_mag, self.max_mag)
        # a = log10(total_moment_rate) - c - (1.5 - b) * m_c - log10(H)
        new_a = (np.log10(target_moment_rate)
                 - self.c_val
                 - (1.5 - self.b_val) * self.corner_mag
                 - np.log10(H)
                 )
        delta = new_a - self.a_val
        self.a_val = float(new_a)
        # keep internal GR in sync
        if hasattr(self, "_dt_gr") and hasattr(self._dt_gr, "a_val"):
            self._dt_gr.a_val += delta

    @classmethod
    def from_moment(cls,
                    min_mag: float,
                    max_mag: float,
                    corner_mag: float,
                    bin_width: float,
                    b_val: float,
                    moment_rate: float,
                    c_val: float = 9.05):
        self = cls(min_mag, max_mag, corner_mag, bin_width, 0.0, b_val)
        self._set_a(moment_rate)
        return self


def _upper_gamma(s, x):
    return gammaincc(s,x) * gamma(s)


def mag_to_mo(mag, c=9.05):
    """
    Scalar moment [in Nm] from moment magnitude

    :return:
        The computed scalar seismic moment
    """
    return 10**(1.5 * mag + c)


def mo_to_mag(mo, c=9.05):
    """
    From moment magnitude to scalar moment [in Nm]

    :return:
        The computed magnitude
    """
    return (math.log10(mo) - c) / 1.5
