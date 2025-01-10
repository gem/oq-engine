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
Module :mod: openquake.hmtk.faults.mfd.youngs_coppersmith implements class
YoungsCoppersmithExponential and YoungsCoppersmithCharacteristic, the
exponential and characteristic forms of the Youngs & Coppersmith (1985)
models for calculating earthquake recurrence from slip rate

Youngs, R. R., and Coppersmith, K., J. (1985) "Implications of Fault Slip Rates
and Earthquake Recurrence Models to Probabilistic Seismic Hazard Estimates"
Bull. Seis. Soc. Am. 75(4) 939 - 964

"""

import numpy as np
from math import exp, log
from openquake.hmtk.faults.mfd.base import _scale_moment, BaseMFDfromSlip
from openquake.hazardlib.mfd.youngs_coppersmith_1985 import (
    YoungsCoppersmith1985MFD,
)

C_VALUE = 16.05
D_VALUE = 1.5


class YoungsCoppersmithExponential(BaseMFDfromSlip):
    """
    Calculates the activity rate on a fault with a given slip assuming the
    exponential model described in Youngs & Coppersmith (1985) Eq. 11

    :param str mfd_model:
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

    :param float b_value_sigma:
        Uncertainty on exponent (b-value) for the magnitude frequency
        distribution

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
            * 'Model_Weight' - Logic tree weight of model type (float)
            * 'MFD_spacing' - Width of MFD bin (float)
            * 'Minimum_Magnitude' - Minimum magnitude of activity rates (float)
            * 'b_value' - Tuple of (b-value, b-value uncertainty)
            * 'Maximum_Magnitude' - Maximum magnitude on fault (if not defined
            will use scaling relation)
            * 'Maximum_Magnitude_Uncertainty' - Uncertainty on
            maximum magnitude
            (If not defined and the MSR has a sigma term then this will be
            taken from sigma)
        """
        self.mfd_model = "Youngs & Coppersmith Exponential"
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
            Configuration file (see setUp for parameters)
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

    def get_mfd(self, slip, area, shear_modulus=30.0):
        """
        Calculates activity rate on the fault

        :param float slip:
            Slip rate in mm/yr

        :param area:
            Width of the fault (km)

        :param float shear_modulus:
            Shear modulus of the fault (GPa)

        :returns:
            * Minimum Magnitude (float)
            * Bin width (float)
            * Occurrence Rates (numpy.ndarray)
        """
        # Working in Nm so convert:  shear_modulus - GPa -> Nm
        # area - km ** 2. -> m ** 2.
        # slip - mm/yr -> m/yr
        moment_rate = (
            (shear_modulus * 1.0e9) * (area * 1.0e6) * (slip / 1000.0)
        )
        moment_mag = _scale_moment(self.mmax, in_nm=True)
        beta = self.b_value * log(10.0)
        mag = np.arange(
            self.mmin - (self.bin_width / 2.0),
            self.mmax + self.bin_width,
            self.bin_width,
        )
        if self.b_value > 1.5:
            print(
                "b-value larger than 1.5 will produce invalid results in "
                "Anderson & Luco models"
            )
            self.occurrence_rate = np.nan * np.ones(len(mag) - 1)
            return self.mmin, self.bin_width, self.occurrence_rate

        self.occurrence_rate = np.zeros(len(mag) - 1, dtype=float)
        for ival in range(0, len(mag) - 1):
            self.occurrence_rate[ival] = self.cumulative_value(
                mag[ival], moment_rate, beta, moment_mag
            ) - self.cumulative_value(
                mag[ival + 1], moment_rate, beta, moment_mag
            )

        return self.mmin, self.bin_width, self.occurrence_rate

    def cumulative_value(self, mag_val, moment_rate, beta, moment_mag):
        """
        Calculates the cumulative rate of events with M > m0 using
        equation 11 of Youngs & Coppersmith (1985)

        :param float mag_val:
            Magnitude

        :param float moment_rate:
            Moment rate on fault (in Nm) from slip rate

        :param float beta:
            Exponent (b log(10)

        :param float moment_mag:
            Moment of the upper bound magnitude
        """
        exponent = exp(-beta * (self.mmax - mag_val))
        return (moment_rate * (D_VALUE - self.b_value) * (1.0 - exponent)) / (
            self.b_value * moment_mag * exponent
        )


class YoungsCoppersmithCharacteristic(BaseMFDfromSlip):
    """
    Calculates the activity rate on a fault with a given slip assuming the
    characteristic model described in Youngs & Coppersmith (1985)
    Eqs. 16 and 17

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
        Exponent (b-value) for the exponential magnitude frequency distribution

    :param float b_value_sigma:
        Uncertainty on exponent (b-value) for the magnitude frequency
        distribution

    :param numpy.ndarray occurrence_rate:
        Activity rates for magnitude in the range mmin to mmax in steps of
        bin_width

    :param model:
        Maintains present instance of :class: YoungsCoppersmith1985MFD
    """

    def setUp(self, mfd_conf):
        """
        Input core configuration parameters as specified in the
        configuration file

        :param dict mfd_conf:
            Configuration file containing the following attributes:
            * 'Model_Weight' - Logic tree weight of model type (float)
            * 'MFD_spacing' - Width of MFD bin (float)
            * 'Minimum_Magnitude' - Minimum magnitude of activity rates (float)
            * 'b_value' - Tuple of (b-value, b-value uncertainty)
            * 'Maximum_Magnitude' - Characteristic magnitude on fault
            (if not defined, will use scaling relation)
            * 'Maximum_Magnitude_Uncertainty' - Uncertainty on
            maximum magnitude
            (If not defined and the MSR has a sigma term then this will be
            taken from sigma)
        """
        self.mfd_type = "Youngs & Coppersmith (1985) Characteristic"
        self.mfd_weight = mfd_conf["Model_Weight"]
        self.bin_width = mfd_conf["MFD_spacing"]
        self.mmin = mfd_conf["Minimum_Magnitude"]
        self.mmax = None
        self.mmax_sigma = None
        self.b_value = mfd_conf["b_value"][0]
        self.b_value_sigma = mfd_conf["b_value"][1]
        self.occurrence_rate = None
        self.model = None

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

    def get_mfd(self, slip, area, shear_modulus=30.0):
        """
        Calculates activity rate on the fault

        :param float slip:
            Slip rate in mm/yr

        :param area:
            Area of the fault (km)

        :param float shear_modulus:
            Shear modulus of the fault (GPa)

        :returns:
            * Minimum Magnitude (float)
            * Bin width (float)
            * Occurrence Rates (numpy.ndarray)

        Behavioural Notes: To use the openquake.hazardlib implementation the
        magnitudes returned will be the mid_point of the bins and not the
        original edge points. The minimum magnitude is update to reflect this!
        """
        # Calculate moment rate in N-m / year
        moment_rate = (
            (shear_modulus * 1.0e9) * (area * 1.0e6) * (slip / 1000.0)
        )
        # Get Youngs & Coppersmith rate from
        # youngs_coppersmith.YoungsCoppersmith1985MFD.from_total_moment_rate
        self.model = YoungsCoppersmith1985MFD.from_total_moment_rate(
            self.mmin - (self.bin_width / 2.0),
            self.b_value,
            self.mmax - 0.25,
            moment_rate,
            self.bin_width,
        )
        temp_data = self.model.get_annual_occurrence_rates()
        self.occurrence_rate = np.array([value[1] for value in temp_data])
        self.mmin = np.min(np.array([value[0] for value in temp_data]))
        return self.mmin, self.bin_width, self.occurrence_rate
