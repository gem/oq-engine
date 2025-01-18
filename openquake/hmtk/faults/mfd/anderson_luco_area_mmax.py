# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod: mfd.anderson_luco_1_mmax implements :class:
AndersonLucoType1Mmax. This calculates the magnitude occurrence rate on a fault
given a known slip value using the exponential models described by
Anderson & Luco (1983) referring to the rupture area of the maximum earthquake.

Anderson, J. G., and Luco, J. E. (1983) "Consequences of slip rate constraints
on earthquake recurrence relations". Bull. Seis. Soc. Am. 73(2) 471 - 496
"""
import abc
import numpy as np
from openquake.hmtk.faults.mfd.base import BaseMFDfromSlip

C_VALUE = 16.05
D_VALUE = 1.5


class BaseRecurrenceModel(object):
    """
    Abstract base class to implement cumulative value formula
    """

    @abc.abstractmethod
    def cumulative_value(self, slip, mmax, mag_value, bbar, dbar, beta):
        """
        Returns the rate of earthquakes with M > mag_value
        """
        raise NotImplementedError


class Type1RecurrenceModel(BaseRecurrenceModel):
    """
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula I.10 of Table 2 in Anderson & Luco (1993).
    """

    def cumulative_value(self, slip, mmax, mag_value, bbar, dbar, beta):
        """
        Returns the rate of events with M > mag_value

        :param float slip:
            Slip rate in mm/yr
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        :param float beta:
            Beta value of formula defined in Eq. 20 of Anderson & Luco (1983)
        """
        delta_m = mmax - mag_value
        a_1 = self._get_a1_value(bbar, dbar, slip / 10.0, beta, mmax)
        return a_1 * np.exp(bbar * delta_m) * (delta_m > 0.0)

    @staticmethod
    def _get_a1_value(bbar, dbar, slip, beta, mmax):
        """
        Returns the A1 value defined in I.9 (Table 2)
        """
        return (
            ((dbar - bbar) / dbar)
            * (slip / beta)
            * np.exp(-(dbar / 2.0) * mmax)
        )


class Type2RecurrenceModel(BaseRecurrenceModel):
    """
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula II.9 of Table 3 in Anderson & Luco (1993).
    """

    def cumulative_value(self, slip, mmax, mag_value, bbar, dbar, beta):
        """
        Returns the rate of events with M > mag_value

        :param float slip:
            Slip rate in mm/yr
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        :param float beta:
            Beta value of formula defined in Eq. 20 of Anderson & Luco (1983)
        """
        delta_m = mmax - mag_value
        a_2 = self._get_a2_value(bbar, dbar, slip / 10.0, beta, mmax)
        return a_2 * (np.exp(bbar * delta_m) - 1.0) * (delta_m > 0.0)

    @staticmethod
    def _get_a2_value(bbar, dbar, slip, beta, mmax):
        """
        Returns the A2 value defined in II.8 (Table 3)
        """
        return (
            ((dbar - bbar) / bbar)
            * (slip / beta)
            * np.exp(-(dbar / 2.0) * mmax)
        )


class Type3RecurrenceModel(BaseRecurrenceModel):
    """
    Calculate N(M > mag_value) using Anderson & Luco Type 1 formula as
    inverse of formula III.9 of Table 4 in Anderson & Luco (1993).
    """

    def cumulative_value(self, slip, mmax, mag_value, bbar, dbar, beta):
        """
        Returns the rate of events with M > mag_value

        :param float slip:
            Slip rate in mm/yr
        :param float mmax:
            Maximum magnitude
        :param float mag_value:
            Magnitude value
        :param float bbar:
            \bar{b} parameter (effectively = b * log(10.))
        :param float dbar:
            \bar{d} parameter
        :param float beta:
            Beta value of formula defined in Eq. 20 of Anderson & Luco (1983)
        """
        delta_m = mmax - mag_value
        a_3 = self._get_a3_value(bbar, dbar, slip / 10.0, beta, mmax)
        central_term = np.exp(bbar * delta_m) - 1.0 - (bbar * delta_m)
        return a_3 * central_term * (delta_m > 0.0)

    @staticmethod
    def _get_a3_value(bbar, dbar, slip, beta, mmax):
        """
        Returns the A3 value defined in III.4 (Table 4)
        """
        return (
            (dbar * (dbar - bbar) / (bbar**2.0))
            * (slip / beta)
            * np.exp(-(dbar / 2.0) * mmax)
        )


RECURRENCE_MAP = {
    "First": Type1RecurrenceModel(),
    "Second": Type2RecurrenceModel(),
    "Third": Type3RecurrenceModel(),
}


class AndersonLucoAreaMmax(BaseMFDfromSlip):
    """
    Class to implement the 1st fault activity rate calculator
    of Anderson & Luco (1983)

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
    """

    def setUp(self, mfd_conf):
        """
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
            * 'Maximum_Magnitude_Uncertainty' - Uncertainty
            on maximum magnitude
            (If not defined and the MSR has a sigma term then this will be
            taken from sigma)
        """
        self.mfd_type = mfd_conf["Model_Type"]
        self.mfd_model = "Anderson & Luco (Mmax) " + self.mfd_type
        self.mfd_weight = mfd_conf["Model_Weight"]
        self.bin_width = mfd_conf["MFD_spacing"]
        self.mmin = mfd_conf["Minimum_Magnitude"]
        self.mmax = None
        self.mmax_sigma = None
        self.b_value = mfd_conf["b_value"][0]
        self.b_value_sigma = mfd_conf["b_value"][1]
        self.occurrence_rate = None

    def get_mmax(self, mfd_conf, msr, rake, area):
        """
        Gets the mmax for the fault - reading directly from the config file
        or using the msr otherwise

        :param dict mfd_config:
            Configuration file (see setUp for paramters)
        :param msr:
            Instance of :class: nhlib.scalerel
        :param float rake:
            Rake of the fault (in range -180 to 180)
        :param float area:
            Area of the fault surface (km^2)
        """
        if mfd_conf["Maximum_Magnitude"]:
            self.mmax = mfd_conf["Maximum_Magnitude"]
        else:
            self.mmax = msr.get_median_mag(area, rake)

        self.mmax_sigma = mfd_conf.get(
            "Maximum_Magnitude_Uncertainty", None
        ) or msr.get_std_dev_mag(None, rake)

    def get_mfd(
        self, slip, fault_width, shear_modulus=30.0, disp_length_ratio=1.25e-5
    ):
        """
        Calculates activity rate on the fault

        :param float slip:
            Slip rate in mm/yr

        :param fault_width:
            Width of the fault (km)

        :param float shear_modulus:
            Shear modulus of the fault (GPa)

        :param float disp_length_ratio:
            Displacement to length ratio (dimensionless)

        :returns:
            * Minimum Magnitude (float)
            * Bin width (float)
            * Occurrence Rates (numpy.ndarray)
        """
        beta = np.sqrt(
            (disp_length_ratio * (10.0**C_VALUE))
            / ((shear_modulus * 1.0e10) * (fault_width * 1e5))
        )
        dbar = D_VALUE * np.log(10.0)
        bbar = self.b_value * np.log(10.0)
        mag = np.arange(
            self.mmin - (self.bin_width / 2.0),
            self.mmax + self.bin_width,
            self.bin_width,
        )

        if bbar > dbar:
            print(
                "b-value larger than 1.5 will produce invalid results in "
                "Anderson & Luco models"
            )
            self.occurrence_rate = np.nan * np.ones(len(mag) - 1)
            return self.mmin, self.bin_width, self.occurrence_rate

        self.occurrence_rate = np.zeros(len(mag) - 1, dtype=float)
        for ival in range(0, len(mag) - 1):
            self.occurrence_rate[ival] = RECURRENCE_MAP[
                self.mfd_type
            ].cumulative_value(
                slip, self.mmax, mag[ival], bbar, dbar, beta
            ) - RECURRENCE_MAP[self.mfd_type].cumulative_value(
                slip, self.mmax, mag[ival + 1], bbar, dbar, beta
            )
            if self.occurrence_rate[ival] < 0.0:
                self.occurrence_rate[ival] = 0.0
        return self.mmin, self.bin_width, self.occurrence_rate
