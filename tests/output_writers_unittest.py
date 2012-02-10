# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
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

from collections import namedtuple
import itertools
import mock
import string
import unittest

from openquake import writer
from openquake.output import hazard as hazard_output
from openquake.output import risk as risk_output

from tests.utils import helpers


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


class CreateHazardmapWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for openquake.output.hazard.create_hazardmap_writer()."""

    create_function = SMWrapper(hazard_output.create_hazardmap_writer)
    xml_writer_class = hazard_output.HazardMapXMLWriter
    db_writer_class = hazard_output.HazardMapDBWriter


class CreateHazardcurveWriterTestCase(unittest.TestCase, CreateWriterTestBase):
    """Tests for openquake.output.hazard.create_hazardcurve_writer()."""

    create_function = SMWrapper(hazard_output.create_hazardcurve_writer)
    xml_writer_class = hazard_output.HazardCurveXMLWriter
    db_writer_class = hazard_output.HazardCurveDBWriter


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


class GetModeTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of output.hazard.get_mode()."""

    # XML serialization context
    XSC = namedtuple("XSC", "blocks, cblock, i_total, i_done, i_next")

    def test_get_mode_at_start(self):
        """
        At the first block, no data serialized yet, the mode
        returned has only the 'start' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=3, cblock=1, i_total=5, i_done=0, i_next=2))
        self.assertEqual((True, False, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_at_start_with_some_data_serialized(self):
        """
        At the first block, with some data serialized already, the mode
        returned has only the 'middle' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=3, cblock=1, i_total=5, i_done=1, i_next=2))
        self.assertEqual((False, True, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_in_the_middle(self):
        """
        At a block in the middle, the mode returned has only the
        'middle' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=3, cblock=2, i_total=5, i_done=1, i_next=2))
        self.assertEqual((False, True, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_at_the_end(self):
        """
        At the last block, about to serialize the last batch of data, the
        mode returned has only the 'end' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=2, cblock=2, i_total=5, i_done=1, i_next=4))
        self.assertEqual((False, False, True),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_at_the_end_and_not_the_last_batch_of_data(self):
        """
        At the last block, about to serialize a batch of data but more
        remains, the mode returned has only the 'middle' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=2, cblock=2, i_total=6, i_done=1, i_next=4))
        self.assertEqual((False, True, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_with_single_block_at_start_and_multi_batch_start(self):
        """
        A single block with no data serialized yet. Data is serialized in
        multiple batches and the next batch is not the last one.
        The mode returned has only the 'start' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=1, cblock=1, i_total=5, i_done=0, i_next=2))
        self.assertEqual((True, False, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_with_single_block_at_start_and_single_batch(self):
        """
        A single block with no data serialized yet. The data is serialized
        in a single batch.
        The mode returned has the 'start' and the 'end' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=1, cblock=1, i_total=5, i_done=0, i_next=5))
        self.assertEqual((True, False, True),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_with_single_block_at_start_and_multi_batch_middle(self):
        """
        A single block with some data serialized already. Data is serialized in
        multiple batches and the next batch is *not* the last one.
        The mode returned has only the 'middle' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=1, cblock=1, i_total=5, i_done=2, i_next=2))
        self.assertEqual((False, True, False),
                         hazard_output.SerializerContext().get_mode())

    def test_get_mode_with_single_block_at_start_and_multi_batch_end(self):
        """
        A single block with some data serialized already. Data is serialized in
        multiple batches and the next batch *is* the last one.
        The mode returned has only the 'end' flag set.
        """
        hazard_output.SerializerContext().update(
            self.XSC(blocks=1, cblock=1, i_total=5, i_done=3, i_next=2))
        self.assertEqual((False, False, True),
                         hazard_output.SerializerContext().get_mode())


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

    def test__create_writers_with_multi_stage_and_curve(self):
        """
        Multi-stage XML serialization, both serializers are created, the XML
        serializer is cached.
        """
        self._init_curve()
        job_id = self.jobs.next()
        nrml_path = self.files.next()
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        xml_serializer = self.xmls.next() - 1
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])
        # Next time we call the method under test it will invoke only
        # the constructor for the db serializer and the cached xml serializer
        # is returned.
        # This only works if the function under test is called with the same
        # 'job_id' and 'nrml_path'.
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])

    def test__create_writers_with_multi_stage_and_map(self):
        """
        Multi-stage XML serialization, both serializers are created, the XML
        serializer is cached.
        """
        self._init_map()
        job_id = self.jobs.next()
        nrml_path = self.files.next()
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        xml_serializer = self.xmls.next() - 1
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])
        # Next time we call the method under test it will invoke only
        # the constructor for the db serializer and the cached xml serializer
        # is returned.
        # This only works if the function under test is called with the same
        # 'job_id' and 'nrml_path'.
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])

    def test__create_writers_with_multi_stage_and_curve_but_other_job(self):
        """
        Both serializers are created, the xml serializer is *not* cached
        because the jobs differ.
        """
        self._init_curve()
        job_id = self.jobs.next()
        nrml_path = self.files.next()
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        xml_serializer = self.xmls.next() - 1
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])
        # We are passing different job identifiers to the method under test.
        # It will thus call both constructors.  The serializers returned are
        # different.
        result = hazard_output._create_writer(self.jobs.next(), ["db", "xml"],
                                              nrml_path, self.x, self.d, True)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(2, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1,  self.xmls.next() - 1],
                         [rw() for rw in result.writers])

    def test__create_writers_with_multi_stage_and_map_but_different_path(self):
        """
        Both serializers are created, the xml serializer is *not* cached
        because the paths differ.
        """
        self._init_map()
        job_id = self.jobs.next()
        nrml_path = self.files.next()
        result = hazard_output._create_writer(job_id, ["db", "xml"], nrml_path,
                                              self.x, self.d, True)
        self.assertEqual(1, self.d.call_count)
        self.assertEqual(1, self.x.call_count)
        xml_serializer = self.xmls.next() - 1
        self.assertEqual([self.dbs.next() - 1, xml_serializer],
                         [rw() for rw in result.writers])
        # We are passing different paths to the method under test. It will
        # thus call both constructors. The serializers returned are different.
        result = hazard_output._create_writer(
            job_id, ["db", "xml"], self.files.next(), self.x, self.d, True)
        self.assertEqual(2, self.d.call_count)
        self.assertEqual(2, self.x.call_count)
        self.assertEqual([self.dbs.next() - 1,  self.xmls.next() - 1],
                         [rw() for rw in result.writers])
