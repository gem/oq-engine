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


class CreateWriterTestBase(object):
    def test_create_writer_with_xml(self):
        """
        A `*XMLWriter` instance is returned when the
        SERIALIZE_RESULTS_TO_DB parameter is set to 'False'.
        """
        writer = self.create_function(
            dict(SERIALIZE_RESULTS_TO_DB='False'), "/tmp/b.xml")
        self.assertTrue(isinstance(writer, self.xml_writer_class))

    def test_create_writer_with_db(self):
        """
        A `*DBWriter` instance is returned when the
        SERIALIZE_RESULTS_TO_DB parameter is set to 'True'.
        """
        writer = self.create_function(
            dict(SERIALIZE_RESULTS_TO_DB='True', OPENQUAKE_JOB_ID='11'),
            "/tmp/c.xml")
        self.assertTrue(isinstance(writer, self.db_writer_class))

    def test_create_writer_with_db_and_no_job_id(self):
        """
        An AssertionError is raised when the SERIALIZE_RESULTS_TO_DB parameter
        is set to 'True'. but the OPENQUAKE_JOB_ID parameter is absent.
        """
        config = dict(SERIALIZE_RESULTS_TO_DB='True')
        self.assertRaises(
            AssertionError, self.create_function, config, "/tmp")

    def test_create_writer_with_db_and_invalid_job_id(self):
        """
        An exception is raised when the SERIALIZE_RESULTS_TO_DB parameter is
        set to 'True'. but the OPENQUAKE_JOB_ID parameter could not be
        converted to an integer
        """
        config = dict(SERIALIZE_RESULTS_TO_DB='True',
                      OPENQUAKE_JOB_ID="number")
        self.assertRaises(
            ValueError, self.create_function, config, "/tmp")


class CreateHazardmapWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_hazardmap_writer()."""

    create_function = staticmethod(opensha.create_hazardmap_writer)
    xml_writer_class = hazard_output.HazardMapXMLWriter
    db_writer_class = hazard_output.HazardMapDBWriter


class CreateHazardcurveWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_hazardcurve_writer()."""

    create_function = staticmethod(opensha.create_hazardcurve_writer)
    xml_writer_class = hazard_output.HazardCurveXMLWriter
    db_writer_class = hazard_output.HazardCurveDBWriter


class CreateGMFWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_gmf_writer()."""

    create_function = staticmethod(opensha.create_gmf_writer)
    xml_writer_class = hazard_output.GMFXMLWriter
    db_writer_class = hazard_output.GMFDBWriter
