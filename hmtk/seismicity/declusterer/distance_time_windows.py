# -*- coding: utf-8 -*-

"""
"""

import abc
import numpy as np

class BaseDistanceTimeWindow(object):
    """
    Defines the space and time windows, within which an event is identified
    as a cluster.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def calc(self, magnitude):
        """
        Allows to calculate distance and time windows (sw_space, sw_time)
        see reference: `Van Stiphout et al (2011)`.

        :param magnitude: magnitude
        :type magnitude: numpy.ndarray
        :returns: distance and time windows
        :rtype: numpy.ndarray
        """
        return

class GardnerKnopoffWindow(BaseDistanceTimeWindow):
    """
    Gardner Knopoff method for calculating distance and time windows
    """
    
    def calc(self, magnitude):
        sw_space = np.power(10.0, 0.1238 * magnitude + 0.983)
        sw_time = np.power(10.0, 0.032 * magnitude + 2.7389) / 364.75
        sw_time[magnitude < 6.5] = np.power(
            10.0, 0.5409 * magnitude[magnitude < 6.5] - 0.547) / 364.75
        return sw_space, sw_time


class GruenthalWindow(BaseDistanceTimeWindow):
    """
    Gruenthal method for calculating distance and time windows
    """

    def calc(self, magnitude):
        sw_space = np.exp(1.77 + np.sqrt(0.037 + 1.02 * magnitude))
        sw_time = np.abs(
            (np.exp(-3.95 + np.sqrt(0.62 + 17.32 * magnitude))) / 364.75)
        sw_time[magnitude >= 6.5] = np.power(
            10, 2.8 + 0.024 * magnitude[magnitude >= 6.5]) / 364.75
        return sw_space, sw_time


class UhrhammerWindow(BaseDistanceTimeWindow):
    """
    Uhrhammer method for calculating distance and time windows
    """

    def calc(self, magnitude):
        sw_space = np.exp(-1.024 + 0.804 * magnitude)
        sw_time = np.exp(-2.87 + 1.235 * magnitude / 364.75)
        return sw_space, sw_time
