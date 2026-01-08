# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2026 GEM Foundation, G. Weatherill, M. Pagani,
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
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

""" Test GCMT Catalogue """


import os
import unittest
import tempfile

from openquake.hmtk.parsers.catalogue.gcmt_ndk_parser import ParseNDKtoGCMT


class TestGCMTCatalogue(unittest.TestCase):
    """Class for testing seismicity utilities"""

    rel_path = os.path.join("..", "parsers", "catalogue", "gcmt_data")
    FILE_PATH = os.path.dirname(__file__)
    BASE_DATA_PATH = os.path.join(FILE_PATH, rel_path)

    def setUp(self):
        # Parse catalogue
        fname = os.path.join(self.BASE_DATA_PATH, "test_gcmt_catalogue_01.txt")

        # Parse GCMT file
        prs = ParseNDKtoGCMT(fname)
        self.cat = prs.read_file()

    def test_serialise_to_csv_centroid(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            fname_csv = os.path.join(tmpdirname, "catalogue_cen.csv")
            self.cat.serialise_to_hmtk_csv(fname_csv, centroid_location=True)

    def test_serialise_to_csv_hypocenter(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            fname_csv = os.path.join(tmpdirname, "catalogue_hyp.csv")
            self.cat.serialise_to_hmtk_csv(fname_csv, centroid_location=False)
