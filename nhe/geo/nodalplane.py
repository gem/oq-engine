"""
Module :mod:`nhe.source.nodalplane` implements :class:`NodalPlane`.
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
    :raises ValueError:
        If any of parameters exceeds the definition range.
    """
    __slots__ = ('strike', 'dip', 'rake')

    def __init__(self, strike, dip, rake):
        self.check_dip(dip)
        self.check_rake(rake)
        self.check_strike(strike)
        self.strike = strike
        self.dip = dip
        self.rake = rake

    @classmethod
    def check_dip(cls, dip):
        """
        Check if ``dip`` is in range ``(0, 90]``
        and raise ``ValueError`` otherwise.
        """
        if not 0 < dip <= 90:
            raise ValueError('dip is out of range (0, 90]')

    @classmethod
    def check_strike(cls, strike):
        """
        Check if ``strike`` is in range ``[0, 360]``
        and raise ``ValueError`` otherwise.
        """
        if not 0 <= strike <= 360:
            raise ValueError('strike is out of range [0, 360]')

    @classmethod
    def check_rake(cls, rake):
        """
        Check if ``rake`` is in range ``(-180, 180]``
        and raise ``ValueError`` otherwise.
        """
        if not -180 < rake <= 180:
            raise ValueError('rake is out of range (-180, 180]')
