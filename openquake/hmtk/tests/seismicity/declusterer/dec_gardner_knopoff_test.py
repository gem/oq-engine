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
"""

import unittest
import os
import numpy as np

from openquake.hmtk.seismicity.declusterer.dec_gardner_knopoff import \
    GardnerKnopoffType1
from openquake.hmtk.seismicity.declusterer.distance_time_windows import \
    GardnerKnopoffWindow
from openquake.hmtk.parsers.catalogue import CsvCatalogueParser


class GardnerKnopoffType1TestCase(unittest.TestCase):
    """
    Unit tests for the Gardner and Knopoff declustering algorithm class.
    """

    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        """
        Read the sample catalogue
        """
        flnme = 'gardner_knopoff_test_catalogue.csv'
        filename = os.path.join(self.BASE_DATA_PATH, flnme)
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()

    def test_dec_gardner_knopoff(self):
        # Testing the Gardner and Knopoff algorithm
        config = {'time_distance_window': GardnerKnopoffWindow(),
                  'fs_time_prop': 1.0}
        # Instantiate the declusterer and process the sample catalogue
        dec = GardnerKnopoffType1()
        vcl, flagvector = dec.decluster(self.cat, config)
        print('vcl:', vcl)
        print('flagvector:', flagvector, self.cat.data['flag'])
        np.testing.assert_allclose(flagvector, self.cat.data['flag'])
