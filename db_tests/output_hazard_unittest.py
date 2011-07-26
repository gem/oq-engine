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


import os
import unittest

from db.alchemy.db_utils import get_uiapi_writer_session
from openquake.output.hazard import *
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


# same as the data above; the sites with statistics data were added by hand;
# the IMLValues and PoEValues are trimmed to the last 4 values and 3 decimals
HAZARD_CURVE_DATA = [
    (Site(-122.2, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'endBranchLabel': '1_1'}),
    (Site(-122.1, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'endBranchLabel': '1_2'}),
    (Site(-122.0, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'endBranchLabel': '1_1'}),
    (Site(-122.0, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'quantileValue': 0.6,
      'statistics': 'quantile'}),
    (Site(-122.1, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'quantileValue': 0.6,
      'statistics': 'quantile'}),
    (Site(-121.9, 37.5),
     {'investigationTimeSpan': '50.0',
      'IMLValues': [0.778, 1.09, 1.52, 2.13],
      'PoEValues': [0.354, 0.114, 0.023, 0.002],
      'IMT': 'PGA',
      'endBranchLabel': '2'})]


GMF_DATA = {
    Site(-117, 40): {'groundMotion': 0.0},
    Site(-116, 40): {'groundMotion': 0.1},
    Site(-116, 41): {'groundMotion': 0.2},
    Site(-117, 41): {'groundMotion': 0.3},
}


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
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        display_name = os.path.basename(output_path)
        hmw = HazardMapDBWriter(session, output_path, self.job.id)

        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set))

        # Call the function under test.
        hmw.insert_output("hazard_map")

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # Make sure the inserted output record has the right data.
        [output] = self.job.output_set
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(display_name, output.display_name)
        self.assertEqual("hazard_map", output.output_type)
        self.assertTrue(self.job is output.oq_job)

    def test_serialize(self):
        """serialize() inserts the output and the hazard_map_data records."""
        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
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
        [hazard_map] = output.hazardmap_set

        self.assertEquals(0.01, hazard_map.poe)
        self.assertEquals('mean', hazard_map.statistic_type)
        self.assertEquals(None, hazard_map.quantile)

        self.assertEqual(len(HAZARD_MAP_DATA),
                         len(hazard_map.hazardmapdata_set))
        self.assertEqual(0, len(output.lossmap_set))

    def test_serialize_sets_min_max_values(self):
        """
        serialize() sets the minimum and maximum values on the output record.
        """
        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        hmw = HazardMapDBWriter(session, output_path, self.job.id)

        # Call the function under test.
        hmw.serialize(HAZARD_MAP_DATA)

        minimum = min(data[1].get("IML") for data in HAZARD_MAP_DATA)
        maximum = max(data[1].get("IML") for data in HAZARD_MAP_DATA)
        # After calling the function under test we see the expected map data.
        [output] = self.job.output_set
        self.assertEqual(round_float(minimum), round_float(output.min_value))
        self.assertEqual(round_float(maximum), round_float(output.max_value))


class HazardCurveDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Unit tests for the HazardCurveDBWriter class, which serializes
    hazard curvess to the database.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_serialize(self):
        """serialize() inserts the output and the hazard_map_data records."""
        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        hcw = HazardCurveDBWriter(session, output_path, self.job.id)

        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set))

        # Call the function under test.
        hcw.serialize(HAZARD_CURVE_DATA)

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # After calling the function under test we see the expected map data.
        [output] = self.job.output_set
        self.assertEqual(4, len(output.hazardcurvedata_set))
        self.assertEqual(0, len(output.lossmap_set))

        # read data from the DB and check that it's equal to the original data
        inserted_data = []

        for hcd in output.hazardcurvedata_set:
            for hcdn in hcd.hazardcurvenodedata_set:
                location = hcdn.location.coords(session)
                node = (Site(location[0], location[1]),
                        {'PoEValues': hcdn.poes})
                if hcd.end_branch_label:
                    node[1]['endBranchLabel'] = hcd.end_branch_label
                else:
                    node[1]['statistics'] = hcd.statistic_type
                    if hcd.quantile is not None:
                        node[1]['quantileValue'] = hcd.quantile

                inserted_data.append(node)

        def normalize(values):
            def sort_key(v):
                return v[0].longitude, v[0].latitude, v[1]

            def norm(dic):
                dic = dict(dic)

                # remove keys not stored in the database
                for k in ['IMLValues', 'investigationTimeSpan', 'IMT']:
                    dic.pop(k, None)

                return dic

            return sorted([(s, norm(v)) for s, v in values], key=sort_key)

        self.assertEquals(normalize(HAZARD_CURVE_DATA),
                          normalize(inserted_data))


class GMFDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Unit tests for the GMFDBWriter class, which serializes
    hazard curvess to the database.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_serialize(self):
        """serialize() inserts the output and the gmf_data records."""
        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        gmfw = GMFDBWriter(session, output_path, self.job.id)

        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set))

        # Call the function under test.
        gmfw.serialize(GMF_DATA)

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # After calling the function under test we see the expected map data.
        [output] = self.job.output_set
        self.assertEqual(0, len(output.hazardcurvedata_set))
        self.assertEqual(0, len(output.lossmap_set))
        self.assertEqual(4, len(output.gmfdata_set))

        # read data from the DB and check that it's equal to the original data
        inserted_data = []

        for gmfd in output.gmfdata_set:
            location = gmfd.location.coords(session)
            inserted_data.append((Site(location[0], location[1]),
                                  {'groundMotion': gmfd.ground_motion}))

        def normalize(values):
            def sort_key(v):
                return v[0].longitude, v[0].latitude, v[1]

            return sorted(values, key=sort_key)

        self.assertEquals(normalize(GMF_DATA.items()),
                          normalize(inserted_data))
