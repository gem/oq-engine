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
    def get_median_area(self, mag):
        """
        Return median area (in square km) from magnitude ``mag``.

        To be overridden by subclasses.
        """
