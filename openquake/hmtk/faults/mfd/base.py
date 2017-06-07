"""
Module :mod:`mfd.base` defines an abstract base classes
for :class:`BaseMFDfromSlip>`
"""
import abc
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD

def _scale_moment(magnitude, in_nm=False):
    '''Returns the moment for a given magnitude.
    :param float magnitude:
        Earthquake magnitude
    :param bool in_nm:
        To return the value in newton metres set to true - otherwise in
        dyne-cm
    '''
    if in_nm:
        return 10.0 ** ((1.5 * magnitude) + 9.05)
    else:
        return 10.0 ** ((1.5 * magnitude) + 16.05)


class BaseMFDfromSlip(object):
    '''Base class for calculating magnitude frequency distribution
    from a given slip value'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self, mfd_conf):
        '''Initialises the parameters from the mfd type'''

    @abc.abstractmethod
    def get_mmax(self, mfd_conf, msr, rake, area):
        '''Gets the mmax for the fault - reading directly from the config file
        or using the msr otherwise'''

    @abc.abstractmethod
    def get_mfd(self):
        '''Calculates the magnitude frequency distribution'''

    def to_evenly_discretized_mfd(self):
        """
        Returns the activity rate as an instance of the :class:
        openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD
        """
        return EvenlyDiscretizedMFD(self.mmin + self.bin_width / 2.,
                                    self.bin_width,
                                    self.occurrence_rate.tolist())
