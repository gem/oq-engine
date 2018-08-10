# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2018 GEM Foundation, G. Weatherill, M. Pagani,
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

import unittest
from collections import OrderedDict
from openquake.hmtk.faults import mfd


class TestAvailableMFDs(unittest.TestCase):
    '''
    Simple test of the module openquake.hmtk.faults.get_available_mfds(), which should
    return an OrderedDict containing instances of all the available mfd classes
    '''

    def setUp(self):
        '''
        '''
        self.mfds = None

    def test_available_mfds(self):
        '''
        As of May 2013 the following MFDs should be available:
        AndersonLucoArbitrary
        AndersonLucoAreaMmax
        YoungsCoppersmithExponential
        YoungsCoppersmithCharacteristic
        Characteristic
        '''
        self.mfds = mfd.get_available_mfds()
        expected_dict = OrderedDict(
            [('AndersonLucoArbitrary',
              mfd.anderson_luco_arbitrary.AndersonLucoArbitrary),
             ('AndersonLucoAreaMmax',
              mfd.anderson_luco_area_mmax.AndersonLucoAreaMmax),
             ('BaseMFDfromSlip', mfd.base.BaseMFDfromSlip),
             ('Characteristic', mfd.characteristic.Characteristic),
             ('YoungsCoppersmithCharacteristic',
              mfd.youngs_coppersmith.YoungsCoppersmithCharacteristic),
             ('YoungsCoppersmithExponential',
              mfd.youngs_coppersmith.YoungsCoppersmithExponential)])
        self.assertDictEqual(self.mfds, expected_dict)
