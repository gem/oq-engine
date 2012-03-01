"""
Module :mod:`nhe.msr.wc1994` implements :class:`WC1994MSR`.
"""
from math import log10
from nhe.msr.base import BaseMSR


class WC1994MSR(BaseMSR):
    """
    Wells and Coppersmith magnitude -- rupture area relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.
    """
    def get_median_area(self, mag, rake, epsilon=0.0):
        """
        The values are a function of both magnitude, rake and
        epsilon when a value for that is provided.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.49 + 0.91 * mag + 0.24 * epsilon)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.42 + 0.90 * mag + 0.22 * epsilon)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.99 + 0.98 * mag + 0.26 * epsilon)
        else:
            # normal
            return 10.0 ** (-2.87 + 0.82 * mag + 0.22 * epsilon)

    @staticmethod
    def get_magnitude_from_area(area, rake, epsilon=0.0):
        """
        Returns magnitude (Mw) given the area, rake and epsilon

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        :param epsilon:
            Degree of uncertainty
        """

        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 4.07 + 0.98 * log10(area) + 0.24 * epsilon
        elif (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 3.98 + 1.02 * log10(area) + 0.23 * epsilon
        elif rake > 0:
            # thrust/reverse
            return 4.33 + 0.90 * log10(area) + 0.25 * epsilon
        else:
            # normal
            return 3.93 + 1.02 * log10(area) + 0.25 * epsilon
