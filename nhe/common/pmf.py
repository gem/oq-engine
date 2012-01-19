"""
Module :mod:`nhe.common.pmf` implements :class:`PMF`.
"""


class PMF(object):
    """
    Probability mass function is a function that gives the probability
    that a discrete random variable is exactly equal to some value.

    :param data:
        The PMF data in a form of list of tuples. Each tuple must contain
        two items with the first item being the probability of the implied
        random variable to take value of the second item.

        There must be at least one tuple in the list. All probabilities
        must sum up to 1. In order to guarantee that regardless of float
        values representation on a machine in use using of type Decimal
        is recommended.

        The type of values (second items in tuples) is not strictly defined,
        those can be objects of any (mixed or homogeneous) type.

    :raises RuntimeError:
        If probabilities do not sum up to 1 or there is zero or negative
        probability.
    """

    __slots__ = ('data', )

    def __init__(self, data):
        if not data or (sum(prob for (prob, value) in data) != 1.0):
            raise RuntimeError('values do not sum up to 1.0')
        if any(prob <= 0 for (prob, value) in data):
            raise RuntimeError('probability is not positive')
        self.data = data
