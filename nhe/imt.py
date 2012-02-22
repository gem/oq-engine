"""
Module :mod:`nhe.imt` defines different intensity measure types.
"""

__all__ = ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')


class _IMT(object):
    """
    Base class for intensity measure type.

    Subclasses must define __slots__ with names of parameters the specific
    intensity measure type requires.
    """
    # TODO: unittest this
    __slots__ = ()

    def __eq__(self, other):
        """
        Two intensity measure type objects are considered equal if they
        are of the same type and have all the parameters in their
        ``__slots__`` exactly equal.
        """
        if not type(other) is type(self):
            return False
        return all(getattr(other, param) == getattr(self, param)
                   for param in type(self).__slots__)

    def __ne__(self, other):
        """
        Two intensity measure type objects are considered not equal if
        :meth:`__eq__` for them returns ``False``.
        """
        return not self.__eq__(other)

    def __hash__(self):
        """
        Object's class name as well as all the attributes from ``__slots__``
        are used for calculating object's hash. That means that objects
        that are considered :meth:`equal <__eq__>` have the same hash.
        """
        cls = type(self)
        return hash((cls.__name__, tuple(getattr(self, param)
                                         for param in cls.__slots__)))


class PGA(_IMT):
    """
    Peak ground acceleration during an earthquake measured in units
    of ``g``, times of gravitational acceleration.
    """
    __slots__ = ()


class PGV(_IMT):
    """
    Peak ground velocity during an earthquake measured in units of ``cm/sec``.
    """
    __slots__ = ()


class PGD(_IMT):
    """
    Peak ground displacement during an earthquake measured in units of ``cm``.
    """
    __slots__ = ()


class SA(_IMT):
    """
    Spectral acceleration, defined as the maximum acceleration of a damped,
    single-degree-of-freedom harmonic oscillator. Units are ``g``, times
    of gravitational acceleration.

    :param period:
        The natural period of the oscillator in seconds.
    :param damping:
        The degree of damping for the oscillator in percents.
    """
    __slots__ = ('period', 'damping')

    def __init__(self, period, damping):
        # TODO: unittest this
        if not period > 0:
            raise ValueError('period must be positive')
        if not damping > 0:
            raise ValueError('damping must be positive')
        self.period = period
        self.damping = damping


class IA(_IMT):
    """
    Arias intensity. Determines the intensity of shaking by measuring
    the acceleration of transient seismic waves. Units are ``m/s``.
    """
    __slots__ = ()


class RSD(_IMT):
    """
    Relative significant duration, 5-95% of :class:`Arias intensity
    <IA>`, in seconds.
    """
    __slots__ = ()


class MMI(_IMT):
    """
    Modified Mercalli intensity, a Roman numeral describing the severity
    of an earthquake in terms of its effects on the earth's surface
    and on humans and their structures.
    """
    __slots__ = ()
