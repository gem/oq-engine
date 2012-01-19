"""
Module :mod:`nhe.common.pdf` contains implementations of PDFs.
"""
import abc
import math


class BasePDF(object):
    """
    A base class for PDF -- probability density function.

    :param time_span:
        The time interval of interest, in years.
    :raises RuntimeError:
        If ``time_span`` is not positive.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, time_span):
        if time_span <= 0:
            raise RuntimeError('time_span must be positive')
        self.time_span = time_span

    @abc.abstractmethod
    def get_probability(self, occurrence_rate):
        """
        Calculate and return the probability of event to happen.

        :param occurrence_rate:
            The average number of events per year.
        :return:
            Float value between 0 and 1 inclusive.

        The way the probability is defined is up to an actual implementation
        of PDF. Some can count it as a probability of one or more events
        to occur (like in :class:`Poisson`), others could count a probability
        of exactly one event to happen.
        """


class Poisson(BasePDF):
    """
    Poisson probability density function.
    """
    def get_probability(self, occurrence_rate):
        """
        Calculates probability as ``1 - e ** (-occurrence_rate*time_span)``.
        """
        return 1 - math.exp(- occurrence_rate * self.time_span)
