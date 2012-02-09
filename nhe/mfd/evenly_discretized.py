"""
Module :mod:`nhe.mfd.evenly_discretized` defines an evenly discretized MFD.
"""
from nhe.mfd.base import BaseMFD


class EvenlyDiscretizedMFD(BaseMFD):
    """
    Evenly discretized MFD is defined as a precalculated histogram.

    :param min_mag:
        Positive float value representing the middle point of the first
        bin in the histogram.
    :param bin_width:
        A positive float value -- the width of a single histogram bin.
    :param occurrence_rates:
        The list of non-negative float values representing the actual
        annual occurrence rates. The resulting histogram has as many bins
        as this list length.
    """

    PARAMETERS = ('min_mag', 'bin_width', 'occurrence_rates')

    MODIFICATIONS = set()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Bin width is positive.
        * Occurrence rates list is not empty.
        * Each number in occurrence rates list is non-negative.
        * Minimum magnitude is positive.
        """
        if not self.bin_width > 0:
            raise ValueError()

        if not self.occurrence_rates:
            raise ValueError()

        if not all(value >= 0 for value in self.occurrence_rates):
            raise ValueError()

        if not self.min_mag >= 0:
            raise ValueError()

    def get_annual_occurrence_rates(self):
        """
        Returns the predefined annual occurrence rates.
        """
        return [
            (self.min_mag + i * self.bin_width, occurence_rate)
            for i, occurence_rate in enumerate(self.occurrence_rates)
        ]
