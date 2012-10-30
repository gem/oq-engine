# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Database related unit tests for hazard computations with the hazard engine.
"""

import itertools
import string
import unittest

from openquake import writer
from openquake.output import risk as risk_output


class ComposeWritersTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(None, writer.compose_writers([]))

    def test_writer_is_none(self):
        self.assertEqual(None, writer.compose_writers([None]))

    def test_single_writer(self):

        class W:
            pass

        w = W()
        self.assertEqual(w, writer.compose_writers([w]))

    def test_multiple_writers(self):

        class W:
            pass

        ws = [W(), W()]

        w = writer.compose_writers(ws)

        self.assertTrue(isinstance(w, writer.CompositeWriter))
        self.assertEqual(list(w.writers), ws)


class CreateWriterTestBase(object):

    jobs = itertools.count(10)
    files = itertools.cycle(string.ascii_lowercase)

    def test_create_writer_with_xml(self):
        """
        A `*XMLWriter` instance is returned when the serialize_to parameter is
        set to 'xml'.
        """
        job_id = self.jobs.next()
        nrml_path = "/tmp/%s.xml" % self.files.next()
        writer = self.create_function(job_id, ['xml'], nrml_path)
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


class SMWrapper(object):
    """Pretend that the wrapped function is a `CreateWriterTestBase` method."""

    def __init__(self, func):
        self.func = func
        self.im_class = CreateWriterTestBase

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


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

    def test_scenario_loss_map_writer_creation(self):
        # XML writer
        writer = risk_output.create_loss_map_writer(
            None, ['xml'], "fakepath.xml", True)
        self.assertEqual(type(writer), risk_output.LossMapXMLWriter)

        # database writer
        writer = risk_output.create_loss_map_writer(
            1, ['db'], "fakepath.xml", True)
        self.assertEqual(type(writer), risk_output.LossMapDBWriter)

    def test_nonscenario_loss_map_writer_creation(self):
        # XML writer
        writer = risk_output.create_loss_map_writer(
            None, ['xml'], "fakepath.xml", False)
        self.assertEqual(type(writer),
                risk_output.LossMapNonScenarioXMLWriter)

        # database writer is the same for scenario and non-scenario
        writer = risk_output.create_loss_map_writer(
            1, ['db'], "fakepath.xml", False)

        self.assertEqual(type(writer),
                risk_output.LossMapDBWriter)
