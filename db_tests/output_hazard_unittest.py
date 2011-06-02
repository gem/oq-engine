# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import unittest

from db.alchemy.db_utils import Session
from openquake.output.hazard import HazardMapDBWriter
from openquake.shapes import Site
from openquake.utils import round_float

from db_tests import helpers

# The data below was captured (and subsequently modified for testing purposes)
# by running
#
#   bin/openquake --config_file=smoketests/classical_psha_simple/config.gem
#
# and putting a breakpoint in openquake/writer.py, line 86
HAZARD_MAP_DATA = [
    (Site(-121.7, 37.6),
     {'IML': 1.9266716959669603,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-121.8, 38.0),
     {'IML': 1.9352164637194078,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-122.1, 37.8),
     {'IML': 1.9459475420737888,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-121.9, 37.7),
     {'IML': 1.9566716959669603,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0})]


class HazardMapDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Unit tests for the HazardMapDBWriter class, which serializes
    hazard maps to the database.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_insert_output(self):
        """An `uiapi.output` record is inserted correctly."""
        self.job = self.setup_classic_job()
        session = Session.get()
        output_path = self.generate_output_path(self.job)
        hmw = HazardMapDBWriter(session, output_path, self.job.id)

        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set))

        # Call the function under test.
        hmw.insert_output()

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # Make sure the inserted output record has the right data.
        [output] = self.job.output_set
        self.assertTrue(output.db_backed)
        self.assertEqual(output_path, output.path)
        self.assertEqual("hazard_map", output.output_type)
        self.assertIs(self.job, output.oq_job)

    def test_insert_map_datum(self):
        """An `uiapi.hazard_map_data` record is inserted correctly."""
        self.output = self.setup_output()
        session = Session.get()
        hmw = HazardMapDBWriter(
            session, self.output.path, self.output.oq_job.id)
        hmw.output = self.output

        # This output has no map data before calling the function under test.
        self.assertEqual(0, len(self.output.hazardmapdata_set))
        self.assertEqual(0, len(self.output.lossmapdata_set))

        # Call the function under test.
        data = HAZARD_MAP_DATA[-1]
        hmw.insert_map_datum(*data)

        # After calling the function under test we see the expected map data.
        self.assertEqual(1, len(self.output.hazardmapdata_set))
        self.assertEqual(0, len(self.output.lossmapdata_set))

        # Make sure the inserted map data is correct.
        [hmd] = self.output.hazardmapdata_set
        point = data[0].point
        self.assertEqual([point.x, point.y], hmd.location.coords(session))
        self.assertEqual(round_float(data[1].get("IML")),
                         round_float(hmd.value))

    def test_serialize(self):
        """serialize() inserts the output and the hazard_map_data records."""
        self.job = self.setup_classic_job()
        session = Session.get()
        output_path = self.generate_output_path(self.job)
        hmw = HazardMapDBWriter(session, output_path, self.job.id)

        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set))

        # Call the function under test.
        hmw.serialize(HAZARD_MAP_DATA)

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # After calling the function under test we see the expected map data.
        [output] = self.job.output_set
        self.assertEqual(len(HAZARD_MAP_DATA), len(output.hazardmapdata_set))
        self.assertEqual(0, len(output.lossmapdata_set))
