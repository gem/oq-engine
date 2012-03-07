"""
Module :mod:`nhe.msr.base` defines an abstract base class for MSR.
"""
import abc
from math import log10


class BaseMSR(object):
    """
    A base class for Magnitude-Scaling Relationship.
    Allows calculation of rupture area from magnitude.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_median_area(self, mag, rake):
        """
        Return median area (in square km) from magnitude ``mag`` and ``rake``.

        To be overridden by subclasses.

        :param mag:
            Moment magnitude (Mw).
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    @abc.abstractmethod
    def get_std_dev_area(self, mag, rake):
        """
        Return the standard deviation of the area distribution
        given magnitude ``mag`` and rake.

        To be overridden by subclasses.

        :param mag:
            Moment magnitude (Mw).
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    def get_area(self, mag, rake, epsilon=0.0):
        """
        Return the area (in square km) from magnitude ``mag``, ``rake``,
        and uncertainty ``epsilon``. Assumes area to be log-normally
        distributed (with logarithmic function of base 10).

        :param mag:
            Moment magnitude (Mw)
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        :param epsilon:
            Uncertainty residual, which identifies the number
            of standard deviations from the median.
        """

        median_area = self.get_median_area(mag, rake)
        std_dev = self.get_std_dev_area(mag, rake)
        return 10 ** (log10(median_area) + epsilon * std_dev)
