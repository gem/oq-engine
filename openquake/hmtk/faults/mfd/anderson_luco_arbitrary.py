# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod: mfd.anderson_luco_1_mmax implements :class:
AndersonLucoType1Mmax. This calculates the magnitude occurrence rate on a fault
given a known slip value using the exponential models described by
Anderson & Luco (1983) referring to the whole fault area.

Anderson, J. G., and Luco, J. E. (1983) "Consequences of slip rate constraints
on earthquake recurrence relations". Bull. Seis. Soc. Am. 73(2) 471 - 496
"""
import abc
import numpy as np
from openquake.hmtk.faults.mfd.base import _scale_moment, BaseMFDfromSlip

C_VALUE = 16.05
D_VALUE = 1.5


class BaseRecurrenceModel(object):
    '''
    Abstract base class to implement cumulative value formula
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def cumulative_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        '''
        Returns the rate of earthquakes with M > mag_value

        :param float slip_moment:
            Product of slip (cm/yr) * Area (cm ^ 2) * shear_modulus (dyne-cm)
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def incremental_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        """
        Returns the incremental rate of earthquakes with M = mag_value
        """
        raise NotImplementedError


class Type1RecurrenceModel(BaseRecurrenceModel):
    '''
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula I.5 of Table 2 in Anderson & Luco (1993).
    '''

    def cumulative_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        '''
        Returns the rate of events with M > mag_value

        :param float slip_moment:
        :param float slip_moment:
            Product of slip (cm/yr) * Area (cm ^ 2) * shear_modulus (dyne-cm)
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        '''
        delta_m = mmax - mag_value
        a_1 = self._get_a1(bbar, dbar, slip_moment, mmax)
        return a_1 * np.exp(bbar * (delta_m)) * (delta_m > 0.0)

    @staticmethod
    def _get_a1(bbar, dbar, slip_moment, mmax):
        """
        Returns the A1 term (I.4 of Table 2 in Anderson & Luco)
        """
        return ((dbar - bbar) / dbar) * (slip_moment / _scale_moment(mmax))

    def incremental_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        """
        Returns the incremental rate of earthquakes with M = mag_value
        """
        delta_m = mmax - mag_value
        dirac_term = np.zeros_like(mag_value)
        dirac_term[np.fabs(delta_m) < 1.0E-12] = 1.0
        a_1 = self._get_a1(bbar, dbar, slip_moment, mmax)
        return a_1 * (bbar * np.exp(bbar * delta_m) * (delta_m > 0.0)) +\
            a_1 * dirac_term
    

class Type2RecurrenceModel(BaseRecurrenceModel):
    '''
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula II.5 of Table 3 in Anderson & Luco (1993).
    '''

    def cumulative_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        '''
        Returns the rate of events with M > mag_value

        :param float slip_moment:
            Product of slip (cm/yr) * Area (cm ^ 2) * shear_modulus (dyne-cm)
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        '''
        delta_m = mmax - mag_value
        a_2 = self._get_a2(bbar, dbar, slip_moment, mmax)
        return a_2 * (np.exp(bbar * delta_m) - 1.) * (delta_m > 0.0)

    @staticmethod
    def _get_a2(bbar, dbar, slip_moment, mmax):
        """
        Returns the A2 value defined in II.4 of Table 2
        """
        return ((dbar - bbar) / bbar) * (slip_moment / _scale_moment(mmax))

    def incremental_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        """
        Returns the incremental rate with Mmax = Mag_value
        """
        delta_m = mmax - mag_value
        a_2 = self._get_a2(bbar, dbar, slip_moment, mmax)
        return a_2 * bbar * np.exp(bbar * delta_m) * (delta_m > 0.0) 


class Type3RecurrenceModel(BaseRecurrenceModel):
    '''
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula III.5 of Table 4 in Anderson & Luco (1993).
    '''

    def cumulative_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        '''
        Returns the rate of events with M > mag_value

        :param float slip_moment:
            Product of slip (cm/yr) * Area (cm ^ 2) * shear_modulus (dyne-cm)
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        '''
        delta_m = mmax - mag_value
        a_3 = self._get_a3(bbar, dbar, slip_moment, mmax)
        central_term = np.exp(bbar * delta_m) - 1.0 - (bbar * delta_m)
        return a_3 * central_term * (delta_m > 0.0)

    @staticmethod
    def _get_a3(bbar, dbar, slip_moment, mmax):
        """
        Returns the A3 term (III.4 in Table  4)
        """
        return ((dbar * (dbar - bbar)) / (bbar ** 2.)) * (slip_moment /
                                                          _scale_moment(mmax))

    def incremental_value(self, slip_moment, mmax, mag_value, bbar, dbar):
        """
        Returns the incremental rate with Mmax = Mag_value
        """
        delta_m = mmax - mag_value
        a_3 = self._get_a3(bbar, dbar, slip_moment, mmax)
        return a_3 * bbar * (np.exp(bbar * delta_m) - 1.0) * (delta_m > 0.0)


RECURRENCE_MAP = {'First': Type1RecurrenceModel(),
                  'Second': Type2RecurrenceModel(),
                  'Third': Type3RecurrenceModel()}


class AndersonLucoArbitrary(BaseMFDfromSlip):
    '''
    Class to implement the fault activity rate calculators of Anderson & Luco
    (1983) referring to the whole fault

    :param str mfd_type:
        Type of magnitude frequency distribution

    :param float mfd_weight:
        Weight of the mfd distribution (for subsequent logic tree processing)

    :param float bin_width:
        Width of the magnitude bin (rates are given for the centre point)

    :param float mmin:
        Minimum magnitude

    :param float mmax:
        Maximum magnitude

    :param float mmax_sigma:
        Uncertainty on maximum magnitude

    :param float b_value:
        Exponent (b-value) for the magnitude frequency distribution

    :param numpy.ndarray occurrence_rate:
        Activity rates for magnitude in the range mmin to mmax in steps of
        bin_width
    '''

    def setUp(self, mfd_conf):
        '''
        Input core configuration parameters as specified in the
        configuration file

        :param dict mfd_conf:
            Configuration file containing the following attributes:
            * 'Type' - Choose between the 1st, 2nd or 3rd type of recurrence
            model {'First' | 'Second' | 'Third'}
            * 'Model_Weight' - Logic tree weight of model type (float)
            * 'MFD_spacing' - Width of MFD bin (float)
            * 'Minimum_Magnitude' - Minimum magnitude of activity rates (float)
            * 'b_value' - Tuple of (b-value, b-value uncertainty)
            * 'Maximum_Magnitude' - Maximum magnitude on fault (if not defined
            will use scaling relation)
            * 'Maximum_Magnitude_Uncertainty' - Uncertainty on maximum
            magnitude (If not defined and the MSR has a sigma term then this
            will be taken from sigma)
        '''
        self.mfd_type = mfd_conf['Model_Type']
        self.mfd_model = 'Anderson & Luco (Arbitrary) ' + self.mfd_type
        self.mfd_weight = mfd_conf['Model_Weight']
        self.bin_width = mfd_conf['MFD_spacing']
        self.mmin = mfd_conf['Minimum_Magnitude']
        self.mmax = None
        self.mmax_sigma = None
        self.b_value = mfd_conf['b_value'][0]
        self.b_value_sigma = mfd_conf['b_value'][1]
        self.occurrence_rate = None

    def get_mmax(self, mfd_conf, msr, rake, area):
        '''
        Gets the mmax for the fault - reading directly from the config file
        or using the msr otherwise

        :param dict mfd_config:
            Configuration file (see setUp for paramters)

        :param msr:
            Instance of :class:`nhlib.scalerel`

        :param float rake:
            Rake of the fault (in range -180 to 180)

        :param float area:
            Area of the fault surface (km^2)
        '''
        if mfd_conf['Maximum_Magnitude']:
            self.mmax = mfd_conf['Maximum_Magnitude']
        else:
            self.mmax = msr.get_median_mag(area, rake)

        if ('Maximum_Magnitude_Uncertainty' in mfd_conf and
                mfd_conf['Maximum_Magnitude_Uncertainty']):
            self.mmax_sigma = mfd_conf['Maximum_Magnitude_Uncertainty']
        else:
            self.mmax_sigma = msr.get_std_dev_mag(rake)

    def get_mfd(self, slip, area, shear_modulus=30.0):
        '''
        Calculates activity rate on the fault

        :param float slip:
            Slip rate in mm/yr

        :param fault_area:
            Width of the fault (km)

        :param float shear_modulus:
            Shear modulus of the fault (GPa)

        :returns:
            * Minimum Magnitude (float)
            * Bin width (float)
            * Occurrence Rates (numpy.ndarray)
        '''

        # Convert shear modulus GPa -> dyne-cm, area km ** 2 -> cm ** 2 and
        # slip mm/yr -> cm/yr
        slip_moment = (shear_modulus * 1E10) * (area * 1E10) * (slip / 10.)
        dbar = D_VALUE * np.log(10.0)
        bbar = self.b_value * np.log(10.0)

        mags = np.arange(self.mmin - (self.bin_width / 2.),
                         self.mmax + self.bin_width,
                         self.bin_width)
        if bbar >= dbar:
            print('b-value larger than 1.5 will produce invalid results in '
                  'Anderson & Luco models')
            self.occurrence_rate = np.nan * np.ones(len(mags) - 1)
            return self.mmin, self.bin_width, self.occurrence_rate
        self.occurrence_rate = np.zeros(len(mags) - 1, dtype=float)
        for ival in range(0, len(mags) - 1):
            self.occurrence_rate[ival] = \
                RECURRENCE_MAP[self.mfd_type].cumulative_value(
                    slip_moment, self.mmax, mags[ival], bbar, dbar) - \
                RECURRENCE_MAP[self.mfd_type].cumulative_value(
                    slip_moment, self.mmax, mags[ival + 1], bbar, dbar)
        return self.mmin, self.bin_width, self.occurrence_rate
