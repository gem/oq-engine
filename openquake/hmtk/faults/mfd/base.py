# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
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
