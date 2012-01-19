"""
Module :mod:`nhe.common.tom` contains implementations of probability
density functions for earthquake temporal occurrence modeling.
"""
import math


class PoissonTOM(object):
    """
    Poissonian temporal occurrence model.

    :param time_span:
        The time interval of interest, in years.
    :raises RuntimeError:
        If ``time_span`` is not positive.
    """
    def __init__(self, time_span):
        if time_span <= 0:
            raise RuntimeError('time_span must be positive')
        self.time_span = time_span

    def get_probability(self, occurrence_rate):
        """
        Calculate and return the probability of event to happen one or more
        times within the time range defined by constructor's ``time_span``
        parameter value.

        Calculates probability as ``1 - e ** (-occurrence_rate*time_span)``.

        :param occurrence_rate:
            The average number of events per year.
        :return:
            Float value between 0 and 1 inclusive.
        """
        return 1 - math.exp(- occurrence_rate * self.time_span)
