# -*- coding: utf-8 -*-

"""
"""

import abc

class SeismicityOccurrence(object):
    '''Implements recurrence calculations for instrumental seismicity'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def calculate(self, catalogue, config, completeness=None):
        """Implements recurrence calculation

        :param catalogue:
            An instance of :class:`hmtk.seismicity.catalogue`

        :param dict config:
            The config contains the necessary information to run a specific 
            algorithm.     

        :param numpy.ndarray completeness:
            The completeness matrix
        """
        return
