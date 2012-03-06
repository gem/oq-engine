"""
Module :mod:`nhe.msr.magarea_base` defines an abstract base class for MSR,
magnitude-area relationship.
"""
import abc


class BaseASR(object):
    """
    A base class for Area Scaling Relationship.
    Allows calculation of rupture magnitude
    from area.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_std_dev_mag_from_area(self, rake):
        """
        Return the standard deviation on the magnitude.

        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    @abc.abstractmethod
    def get_median_mag_from_area(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    def get_mag_from_area(self, area, rake, epsilon=0.0):
        """
        Return the Moment magnitude given the area, rake
        and uncertainty epsilon.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        :param epsilon:
            Uncertainty residual, which identifies the number
            of standard deviations from the median.
        """
        median_mag = self.get_median_mag_from_area(area, rake)
        std_dev = self.get_std_dev_mag_from_area(rake)
        return median_mag + epsilon * std_dev
