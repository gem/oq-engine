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

from openquake.output import writer as output_writer
from openquake.output import hazard as hazard_output
from openquake.output import risk as risk_output


class ComposeWritersTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(None, output_writer.compose_writers([]))

    def test_writer_is_none(self):
        self.assertEqual(None, output_writer.compose_writers([None]))

    def test_single_writer(self):
        class W:
            pass

        w = W()
        self.assertEqual(w, output_writer.compose_writers([w]))

    def test_multiple_writers(self):
        class W:
            pass

        ws = [W(), W()]

        w = output_writer.compose_writers(ws)

        self.assertTrue(isinstance(w, output_writer.CompositeWriter))
        self.assertEqual(list(w.writers), ws)


class CreateWriterTestBase(object):
    def test_create_writer_with_xml(self):
        """
        A `*XMLWriter` instance is returned when the serialize_to parameter is
        set to 'xml'.
        """
        writer = self.create_function(None, ['xml'], "/tmp/b.xml")
        self.assertTrue(isinstance(writer, self.xml_writer_class))

    def test_create_writer_with_db(self):
        """
        A `*DBWriter` instance is returned when the serialize_to  parameter is
        set to 'db'.
        """
        writer = self.create_function(11, ['db'], "/tmp/c.xml")
        self.assertTrue(isinstance(writer, self.db_writer_class))

    def test_create_writer_with_db_and_no_job_id(self):
        """
        An AssertionError is raised when the serialize_to  parameter is set to
        'db'. but the job_id parameter is absent.
        """
        self.assertRaises(
            AssertionError, self.create_function, None, ['db'], "/tmp")

    def test_create_writer_with_db_and_invalid_job_id(self):
        """
        An exception is raised when the serialize_to parameter is set to 'db'
        but the job_id parameter could not be converted to an integer
        """
        self.assertRaises(
            ValueError, self.create_function, 'should_be_a_number', ['db'],
            "/tmp")


class CreateHazardmapWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_hazardmap_writer()."""

    create_function = staticmethod(hazard_output.create_hazardmap_writer)
    xml_writer_class = hazard_output.HazardMapXMLWriter
    db_writer_class = hazard_output.HazardMapDBWriter


class CreateHazardcurveWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_hazardcurve_writer()."""

    create_function = staticmethod(hazard_output.create_hazardcurve_writer)
    xml_writer_class = hazard_output.HazardCurveXMLWriter
    db_writer_class = hazard_output.HazardCurveDBWriter


class CreateGMFWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for hazard.opensha.create_gmf_writer()."""

    create_function = staticmethod(hazard_output.create_gmf_writer)
    xml_writer_class = hazard_output.GMFXMLWriter
    db_writer_class = hazard_output.GmfDBWriter


class CreateRiskWriterTest(unittest.TestCase):
    def test_loss_curve_writer_creation(self):
        # XML writers
        writer = risk_output.create_loss_curve_writer(
            None, ['xml'], "fakepath.xml", "loss_ratio")
        self.assertEqual(type(writer), risk_output.LossRatioCurveXMLWriter)
        writer = risk_output.create_loss_curve_writer(
            None, ['xml'], "fakepath.xml", "loss")
        self.assertEqual(type(writer), risk_output.LossCurveXMLWriter)

        # database writers
        writer = risk_output.create_loss_curve_writer(
            1, ['db'], "fakepath.xml", "loss_ratio")
        self.assertEqual(writer, None)
        writer = risk_output.create_loss_curve_writer(
            1, ['db'], "fakepath.xml", "loss")
        self.assertEqual(type(writer), risk_output.LossCurveDBWriter)

    def test_deterministic_loss_map_writer_creation(self):
        # XML writer
        writer = risk_output.create_loss_map_writer(
            None, ['xml'], "fakepath.xml", True)
        self.assertEqual(type(writer), risk_output.LossMapXMLWriter)

        # database writer
        writer = risk_output.create_loss_map_writer(
            1, ['db'], "fakepath.xml", True)
        self.assertEqual(type(writer), risk_output.LossMapDBWriter)

    def test_nondeterministic_loss_map_writer_creation(self):
        # XML writer
        writer = risk_output.create_loss_map_writer(
            None, ['xml'], "fakepath.xml", False)
        self.assertEqual(writer, None)

        # database writer
        writer = risk_output.create_loss_map_writer(
            1, ['db'], "fakepath.xml", False)
        self.assertEqual(type(writer), risk_output.LossMapDBWriter)
