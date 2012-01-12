"""
Module :mod:`nhe.mfd.base` defines base class for MFD and a base exception
class.
"""
import abc


class MFDError(Exception):
    """
    An error happened during MFD constraint check.
    """


class BaseMFD(object):
    """
    Abstract base class for Magnitude-Frequency Distribution function.

    :param bin_width:
        After all every MFD is treated as a histogram with a specific
        bin width. This parameter defines that value.
    """
    __metaclass__ = abc.ABCMeta


    def __init__(self, bin_width):
        self.bin_width = bin_width
        self.check_constraints()


    def check_constraints(self):
        """
        Check MFD-specific constraints and raise :exc:`MFDError`
        in case of violation.

        Base class implementation only checks that ``bin_width``
        is more than 0.

        .. note::
            Subclasses willing to override this method
            are supposed to call the superclass' method
            before or after it's own implementation.
        """
        if not self.bin_width > 0:
            raise MFDError()


    @abc.abstractmethod
    def get_annual_occurrence_rates(self):
        """
        Return an MFD histogram.

        This method must be implemented by subclasses.

        :return:
            The list of tuples, each tuple containing a pair
            ``(magnitude, occurrence_rate)``. Each pair represents
            a single bin of the histogram with ``magnitude`` being
            the center of the bin. Magnitude values are monotonically
            increasing by value of bin width.
        """
