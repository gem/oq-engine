"""
Module :mod:`mfd.evenly_discretized` defines an evenly discretized MFD.
"""
from mfd.base import BaseMFD, MFDError


class EvenlyDiscretized(BaseMFD):
    """
    Evenly discretized MFD is defined as a precalculated histogram.

    :param min_mag:
        Positive float value representing the middle point of the first
        bin in the histogram.
    :param bin_width:
        See :class:`mfd.base.BaseMFD`.
    :param occurence_rates:
        The list of non-negative float values representing the actual
        occurrence rates. The resulting histogram has as many bins
        as this list length.
    """
    def __init__(self, min_mag, bin_width, occurence_rates):
        self.min_mag = min_mag
        self.occurence_rates = occurence_rates
        super(EvenlyDiscretized, self).__init__(bin_width=bin_width)


    def check_constraints(self):
        """
        Checks the following constraints:

        * Occurrence rates list is not empty.
        * Each number in occurrence rates list is non-negative.
        * Minimum magnitude is positive.
        """
        super(EvenlyDiscretized, self).check_constraints()

        if not self.occurence_rates:
            raise MFDError()

        if not all(value >= 0 for value in self.occurence_rates):
            raise MFDError()

        if not self.min_mag > 0:
            raise MFDError()


    def get_annual_occurence_rates(self):
        """
        Returns the predefined occurrence rates.
        """
        return [
            (self.min_mag + i * self.bin_width, occurence_rate)
            for i, occurence_rate in enumerate(self.occurence_rates)
        ]
