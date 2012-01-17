"""
Module :mod:`nhe.msr.peer` implements :class:`Peer`.
"""
from nhe.msr.base import BaseMSR


class Peer(BaseMSR):
    """
    Magnitude-Scaling Relationship defined for PEER PSHA test cases.
    """
    def get_median_area(self, mag):
        """
        Calculates median area as ``10 ** (mag - 4)``.
        """
        return 10 ** (mag - 4.0)
