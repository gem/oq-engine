# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
Database related unit tests for hazard computations with the hazard engine.
"""

import unittest

from openquake.hazard import opensha
from openquake.output import hazard as hazard_output


class CreateHazardmapWriterTestCase(unittest.TestCase):
    """Tests for hazard.opensha.create_hazardmap_writer()."""

    def test_create_hazardmap_writer_with_xml(self):
        """
        A `HazardMapXMLWriter` instance is returned in the absence of a
        SERIALIZE_MAPS_TO_DB setting.
        """
        writer = opensha.create_hazardmap_writer(dict(), "/tmp/a.xml")
        self.assertTrue(isinstance(writer, hazard_output.HazardMapXMLWriter))

    def test_create_hazardmap_writer_with_xml2(self):
        """
        A `HazardMapXMLWriter` instance is returned when the
        SERIALIZE_MAPS_TO_DB setting is set to 'False'.
        """
        writer = opensha.create_hazardmap_writer(
            dict(SERIALIZE_MAPS_TO_DB='False'), "/tmp/b.xml")
        self.assertTrue(isinstance(writer, hazard_output.HazardMapXMLWriter))

    def test_create_hazardmap_writer_with_db(self):
        writer = opensha.create_hazardmap_writer(
            dict(SERIALIZE_MAPS_TO_DB='True', OPENQUAKE_JOB_ID='11'),
            "/tmp/c.xml")
        self.assertTrue(isinstance(writer, hazard_output.HazardMapDBWriter))
