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
import mock
import string
import unittest

from openquake import writer
from openquake.output import hazard as hazard_output
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


class CreateGMFWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for openquake.output.hazard.create_gmf_writer()."""

    create_function = SMWrapper(hazard_output.create_gmf_writer)
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

        writer = risk_output.create_loss_curve_writer(
            None, ['xml'], "fakepath.xml", "insured_loss_curve")
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


class CreateWriterTestCase(unittest.TestCase):
    """Tests the behaviour of output.hazard._create_writer()."""

    class _FDS(object):
        """Fake DB serializer class to be used for testing."""
        def __init__(self, identifier):
            self.identifier = identifier

        def __call__(self):
            """Return the `identifier` so we can compare and test."""
            return self.identifier

    class _FXS(_FDS):
        """Fake XML serializer class to be used for testing."""
        def set_mode(self, _mode):
            """Will be invoked by the function under test."""
            pass

    jobs = itertools.count(20)
    files = itertools.cycle(string.ascii_lowercase)
    dbs = itertools.count(1000)
    xmls = itertools.count(2000)

    def _init_curve(self):
        # Constructor for DB serializer.
        self.d = mock.Mock(spec=hazard_output.HazardCurveDBWriter)
        self.d.side_effect = lambda _p1, _p2: self._FDS(self.dbs.next())
        # Constructor for XML serializer.
        self.x = mock.Mock(spec=hazard_output.HazardCurveXMLWriter)
        self.x.side_effect = lambda _p1: self._FXS(self.xmls.next())

    def _init_map(self):
        # Constructor for DB serializer.
        self.d = mock.Mock(spec=hazard_output.HazardMapDBWriter)
        self.d.side_effect = lambda _p1, _p2: self._FDS(self.dbs.next())
        # Constructor for XML serializer.
        self.x = mock.Mock(spec=hazard_output.HazardMapXMLWriter)
        self.x.side_effect = lambda _p1: self._FXS(self.xmls.next())

    def test__create_writer_with_db_only_and_curve(self):
        """Only the db writer is created."""
        self._init_curve()
        result = hazard_output._create_writer(
            self.jobs.next(), ["db"], self.files.next(), self.x, self.d)
        self.assertEqual(0, self.x.call_count)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(self.dbs.next() - 1, result())

    def test__create_writer_with_db_only_and_map(self):
        """Only the db writer is created."""
        self._init_map()
        result = hazard_output._create_writer(
            self.jobs.next(), ["db"], self.files.next(), self.x, self.d)
        self.assertEqual(0, self.x.call_count)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(self.dbs.next() - 1, result())

    def test__create_writers_with_single_stage_and_curve(self):
        """
        Both serializers are created, no caching of the XML serializers.
        """
        self._init_curve()
        result = hazard_output._create_writer(
            self.jobs.next(), ["db", "xml"], self.files.next(), self.x, self.d)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, self.xmls.next() - 1],
                         [rw() for rw in result.writers])
        # Next time we call the method under test it will invoke the
        # constructors and the serializers returned are different.
        result = hazard_output._create_writer(
            self.jobs.next(), ["db", "xml"], self.files.next(), self.x, self.d)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(2, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, self.xmls.next() - 1],
                         [rw() for rw in result.writers])

    def test__create_writers_with_single_stage_and_map(self):
        """
        Both serializers are created, no caching of the XML serializers.
        """
        self._init_map()
        result = hazard_output._create_writer(
            self.jobs.next(), ["db", "xml"], self.files.next(), self.x, self.d)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, self.xmls.next() - 1],
                         [rw() for rw in result.writers])
        # Next time we call the method under test it will invoke the
        # constructors and the serializers returned are different.
        result = hazard_output._create_writer(
            self.jobs.next(), ["db", "xml"], self.files.next(), self.x, self.d)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(2, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, self.xmls.next() - 1],
                         [rw() for rw in result.writers])
