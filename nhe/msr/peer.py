"""
Module :mod:`nhe.msr.peer` implements :class:`PeerMSR`.
"""
from nhe.msr.base import BaseMSR


class PeerMSR(BaseMSR):
    """
    Magnitude-Scaling Relationship defined for PEER PSHA test cases.

    See "Verification of Probabilistic Seismic Hazard Analysis Computer
    Programs", Patricia Thomas and Ivan Wong, PEER Report 2010/106, May 2010.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median area as ``10 ** (mag - 4)``. Rake is ignored.
        """
        return 10 ** (mag - 4.0)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for PeerMSR. Mag and rake are ignored.

        >>> peer = PeerMSR()
        >>> 0.25 == peer.get_std_dev_area(4.0, 50)
        True
        """
        return 0.25
