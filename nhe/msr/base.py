"""
Module :mod:`nhe.msr.base` defines a base class for MSR.
"""
import abc


class BaseMSR(object):
    """
    A base class for Magnitude-Scaling Relationship.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_median_area(self, mag, rake):
        """
        Return median area (in square km) from magnitude ``mag`` and ``rake``.

        To be overridden by subclasses.

        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
