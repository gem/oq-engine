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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod: openquake.hmtk.faults.mfd.characteristic implements
:class:Characteristic the simple characteristic earthquake calculator
of recurrence.
"""

import numpy as np
from scipy.stats import truncnorm
from math import fabs
from openquake.hmtk.faults.mfd.base import _scale_moment, BaseMFDfromSlip


class Characteristic(BaseMFDfromSlip):
    """
    Class to implement the characteristic earthquake model assuming a truncated
    Gaussian distribution

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

    :param float lower_bound:
        Lower bound of Gaussian distribution (as number of standard deviations)

    :param float upper_bound:
        Upper bound of Gaussian distribution (as number of standard deviations)

    :param float sigma:
        Standard deviation (in magnitude units) of the Gaussian distribution

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
            * 'Maximum_Magnitude' - Characteristic magnituded (float)
            (if not defined will use scaling relation)
            * 'Maximum_Magnitude_Uncertainty' - Uncertainty on
            maximum magnitude
            (If not defined and the MSR has a sigma term then this will be
            taken from sigma)
            * 'Lower_Bound' - Lower bound in terms of number of sigma (float)
            * 'Upper_Bound' - Upper bound in terms of number of sigma (float)
            * 'Sigma' - Standard deviation (in magnitude units) of distribution
        """
        self.mfd_model = "Characteristic"
        self.mfd_weight = mfd_conf["Model_Weight"]
        self.bin_width = mfd_conf["MFD_spacing"]
        self.mmin = None
        self.mmax = None
        self.mmax_sigma = None
        self.lower_bound = mfd_conf["Lower_Bound"]
        self.upper_bound = mfd_conf["Upper_Bound"]
        self.sigma = mfd_conf["Sigma"]
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

    def get_mfd(self, slip, area, shear_modulus=30.0):
        """
        Calculates activity rate on the fault

        :param float slip:
            Slip rate in mm/yr

        :param fault_width:
            Width of the fault (km)

        :param float disp_length_ratio:
            Displacement to length ratio (dimensionless)

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
        characteristic_rate = moment_rate / moment_mag
        if self.sigma and (fabs(self.sigma) > 1e-5):
            self.mmin = self.mmax + (self.lower_bound * self.sigma)
            mag_upper = self.mmax + (self.upper_bound * self.sigma)
            mag_range = np.arange(
                self.mmin, mag_upper + self.bin_width, self.bin_width
            )
            self.occurrence_rate = characteristic_rate * (
                truncnorm.cdf(
                    mag_range + (self.bin_width / 2.0),
                    self.lower_bound,
                    self.upper_bound,
                    loc=self.mmax,
                    scale=self.sigma,
                )
                - truncnorm.cdf(
                    mag_range - (self.bin_width / 2.0),
                    self.lower_bound,
                    self.upper_bound,
                    loc=self.mmax,
                    scale=self.sigma,
                )
            )
        else:
            # Returns only a single rate
            self.mmin = self.mmax
            self.occurrence_rate = np.array([characteristic_rate], dtype=float)

        return self.mmin, self.bin_width, self.occurrence_rate
