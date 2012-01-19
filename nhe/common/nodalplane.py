"""
Module :mod:`nhe.common.nodalplane` implements :class:`NodalPlane`.
"""

class NodalPlane(object):
    """
    Nodal plane represents earthquake rupture orientation and propagation
    direction.

    :param strike:
        Angle between line created by the intersection of rupture plane
        and the North direction (defined between 0 and 360 degrees).
    :param dip:
        Angle between earth surface and fault plane (defined between 0 and 90
        degrees).
    :param rake:
        Angle describing rupture propagation direction (defined between -180
        and +180 degrees).
    :raises RuntimeError:
        If any of parameters exceeds the definition range.
    """
    __slots__ = ('strike', 'dip', 'rake')

    def __init__(self, strike, dip, rake):
        if not 0 <= strike <= 360:
            raise RuntimeError('strike is out of range [0, 360]')
        if not 0 < dip <= 90:
            raise RuntimeError('dip is out of range (0, 90]')
        if not -180 <= rake <= 180:
            raise RuntimeError('rake is out of range [-180, 180]')
        self.strike = strike
        self.dip = dip
        self.rake = rake
