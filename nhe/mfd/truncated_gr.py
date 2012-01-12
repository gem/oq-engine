"""
Module :mod:`nhe.mfd.truncated_gr` defines a Truncated Gutenberg-Richter MFD.
"""
from nhe.mfd.base import BaseMFD, MFDError


class TruncatedGR(BaseMFD):
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
        :meth:`result histogram <get_annual_occurence_rates>` will be aligned
        to make its left border match this value.
    :param max_mag:
        The highest possible magnitude. The same as for ``min_mag``: the last
        bin in the histogram will correspond to the magnitude value equal to
        ``max_mag - bin_width / 2``.

    Values for ``min_mag`` and ``max_mag`` don't have to be aligned with
    respect to ``bin_width``. They get rounded accordingly anyway so that
    both are divisible by ``bin_width``.
    """
    def __init__(self, min_mag, max_mag, a_val, b_val, bin_width):
        self.min_mag = min_mag
        self.max_mag = max_mag
        self.a_val = a_val
        self.b_val = b_val
        super(TruncatedGR, self).__init__(bin_width=bin_width)

    def check_constraints(self):
        """
        Checks the following constraints:

        * Minimum magnitude is positive.
        * Maximum magnitude is equal or greater than minimum magnitude.
        * ``b`` value is positive.
        """
        super(TruncatedGR, self).check_constraints()

        if not self.min_mag >= 0:
            raise MFDError()

        if not self.max_mag >= self.min_mag:
            raise MFDError()

        if not self.b_val > 0:
            raise MFDError()

    def _get_rate(self, mag):
        """
        Calculate and return an occurrence rate for a specific bin.

        :param mag:
            Magnitude value corresponding to the center of the bin of interest.
        """
        mag_lo = mag - self.bin_width / 2
        mag_hi = mag + self.bin_width / 2
        return (10 ** (self.a_val - self.b_val * mag_lo)
                - 10 ** (self.a_val - self.b_val * mag_hi))

    def get_annual_occurrence_rates(self):
        """
        Calculate and return the annual occurrence rates histogram.

        The result histogram has only one bin if minimum and maximum magnitude
        values appear equal after rounding.

        :returns:
            See :meth:`nhe.mfd.BaseMFD.get_annual_occurence_rates`.
        """
        min_mag = round(self.min_mag / self.bin_width) * self.bin_width
        max_mag = round(self.max_mag / self.bin_width) * self.bin_width
        if min_mag != max_mag:
            min_mag += self.bin_width / 2
            max_mag -= self.bin_width / 2
        n_bins = int(round((max_mag - min_mag) / self.bin_width)) + 1
        rates = []
        for i in xrange(n_bins):
            mag = min_mag + i * self.bin_width
            rate = self._get_rate(mag)
            rates.append((mag, rate))
        return rates
