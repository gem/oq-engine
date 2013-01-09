# -*- coding: utf-8 -*-

"""
"""

import abc

class SeismicityRecurrence(object):
    '''Implements recurrence calculations for instrumental seismicity'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def calculate(self, catalogue, config, completeness=None):
        '''Implements recurrence calculation'''
        return
