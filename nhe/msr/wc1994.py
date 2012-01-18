"""
Module :mod:`nhe.msr.wc1994` implements :class:`WC1994`.
"""
from nhe.msr.base import BaseMSR


class WC1994(BaseMSR):
    """
    Wells and Coppersmith magnitude -- rupture area relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.49 + 0.91 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.42 + 0.90 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.99 + 0.98 * mag)
        else:
            # normal
            return 10.0 ** (-2.87 + 0.82 * mag)
