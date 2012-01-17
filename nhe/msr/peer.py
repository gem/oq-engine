"""
Module :mod:`nhe.msr.peer` implements :class:`Peer`.
"""
from nhe.msr.base import BaseMSR


class Peer(BaseMSR):
    """
    Magnitude-Scaling Relationship defined for PEER PSHA test cases.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median area as ``10 ** (mag - 4)``. Rake is ignored.
        """
        return 10 ** (mag - 4.0)
