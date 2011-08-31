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

from openquake.output.hazard import *
from openquake.shapes import Site
from openquake.utils import round_float

from tests.utils import helpers


# The data below was captured (and subsequently modified for testing purposes)
# by running
#
#   bin/openquake --config_file=smoketests/classical_psha_simple/config.gem
#
# and putting a breakpoint in openquake/writer.py, line 86
def HAZARD_MAP_MEAN_DATA():
    return [
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


def HAZARD_MAP_QUANTILE_DATA():
    return [
        (Site(-121.7, 37.6),
         {'IML': 1.9266716959669603,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'quantile',
          'quantileValue': 0.2,
          'vs30': 760.0}),
        (Site(-121.8, 38.0),
         {'IML': 1.9352164637194078,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'quantile',
          'quantileValue': 0.2,
          'vs30': 760.0}),
        (Site(-122.1, 37.8),
         {'IML': 1.9459475420737888,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'quantile',
          'quantileValue': 0.2,
          'vs30': 760.0}),
        (Site(-121.9, 37.7),
         {'IML': 1.9566716959669603,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'quantile',
          'quantileValue': 0.2,
          'vs30': 760.0})]


# same as the data above; the sites with statistics data were added by hand;
# the IMLValues and PoEValues are trimmed to the last 4 values and 3 decimals
def HAZARD_CURVE_DATA():
    return [
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


def GMF_DATA():
    return {
        Site(-117, 40): {'groundMotion': 0.0},
        Site(-116, 40): {'groundMotion': 0.1},
        Site(-116, 41): {'groundMotion': 0.2},
        Site(-117, 41): {'groundMotion': 0.3},
    }


class HazardMapDBBaseTestCase(unittest.TestCase, helpers.DbTestMixin):
    """Common code for hazard map db reader/writer test"""

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def setUp(self):
        self.job = self.setup_classic_job()
        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = HazardMapDBWriter(output_path, self.job.id)
        self.reader = HazardMapDBReader()


class HazardMapDBWriterTestCase(HazardMapDBBaseTestCase):
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
        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set.all()))

        # Call the function under test.
        self.writer.insert_output("hazard_map")

        self.job = models.OqJob.objects.get(id=self.job.id)
        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set.all()))

        # Make sure the inserted output record has the right data.
        output = self.job.output_set.get()
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(self.display_name, output.display_name)
        self.assertEqual("hazard_map", output.output_type)

    def test_serialize_mean(self):
        """serialize() inserts the output and the hazard_map_data records."""
        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set.all()))

        # Call the function under test.
        self.writer.serialize(HAZARD_MAP_MEAN_DATA())

        self.job = models.OqJob.objects.get(id=self.job.id)
        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set.all()))

        # After calling the function under test we see the expected map data.
        output = self.job.output_set.get()
        hazard_map = output.hazardmap_set.get()

        self.assertEquals(0.01, hazard_map.poe)
        self.assertEquals('mean', hazard_map.statistic_type)
        self.assertEquals(None, hazard_map.quantile)

        self.assertEqual(len(HAZARD_MAP_MEAN_DATA()),
                         len(hazard_map.hazardmapdata_set.all()))
        self.assertEqual(0, len(output.lossmap_set.all()))

    def test_serialize_quantile(self):
        """serialize() inserts the output and the hazard_map_data records."""
        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set.all()))

        # Call the function under test.
        self.writer.serialize(HAZARD_MAP_QUANTILE_DATA())

        self.job = models.OqJob.objects.get(id=self.job.id)
        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set.all()))

        # After calling the function under test we see the expected map data.
        output = self.job.output_set.get()
        hazard_map = output.hazardmap_set.get()

        self.assertEquals(0.01, hazard_map.poe)
        self.assertEquals('quantile', hazard_map.statistic_type)
        self.assertEquals(0.2, hazard_map.quantile)

        self.assertEqual(len(HAZARD_MAP_QUANTILE_DATA()),
                         len(hazard_map.hazardmapdata_set.all()))
        self.assertEqual(0, len(output.lossmap_set.all()))

    def test_serialize_sets_min_max_values(self):
        """
        serialize() sets the minimum and maximum values on the output record.
        """
        # Call the function under test.
        self.writer.serialize(HAZARD_MAP_MEAN_DATA())

        minimum = min(data[1].get("IML") for data in HAZARD_MAP_MEAN_DATA())
        maximum = max(data[1].get("IML") for data in HAZARD_MAP_MEAN_DATA())
        # After calling the function under test we see the expected map data.
        output = self.job.output_set.get()
        self.assertEqual(round_float(minimum), round_float(output.min_value))
        self.assertEqual(round_float(maximum), round_float(output.max_value))


class HazardMapDBReaderTestCase(HazardMapDBBaseTestCase):
    """
    Unit tests for the HazardMapDBReader class, which deserializes
    hazard maps from the database.
    """
    def test_deserialize_mean(self):
        """Hazard map is read back correctly"""
        self.writer.serialize(HAZARD_MAP_MEAN_DATA())

        data = self.reader.deserialize(self.writer.output.id)

        self.assertEquals(self.sort(self.normalize(HAZARD_MAP_MEAN_DATA())),
                          self.sort(self.normalize(data)))

    def test_deserialize_quantile(self):
        """Hazard map is read back correctly"""
        self.writer.serialize(HAZARD_MAP_QUANTILE_DATA())

        data = self.reader.deserialize(self.writer.output.id)

        self.assertEquals(
                self.sort(self.normalize(HAZARD_MAP_QUANTILE_DATA())),
                self.sort(self.normalize(data)))

    def sort(self, values):
        def sort_key(v):
            return v[0].longitude, v[0].latitude, v[1].get('statistics')

        return sorted(values, key=sort_key)

    def normalize(self, values):
        result = []

        for site, attrs in values:
            new = attrs.copy()
            new['IML'] = round_float(attrs['IML'])
            new['investigationTimeSpan'] = float(new['investigationTimeSpan'])

            result.append((site, new))

        return result


class HazardCurveDBBaseTestCase(unittest.TestCase, helpers.DbTestMixin):
    """Common code for hazard curve db reader/writer test"""
    IMLS = [0.778, 1.09, 1.52, 2.13]

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def setUp(self):
        self.job = self.setup_classic_job()
        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = HazardCurveDBWriter(output_path, self.job.id)
        self.reader = HazardCurveDBReader()

    def sort(self, values):
        def sort_key(v):
            return v[0].longitude, v[0].latitude, v[1].get('statistics')

        return sorted(values, key=sort_key)

    def normalize(self, values):
        def norm(dic):
            dic = dict(dic)

            # remove keys not stored in the database
            for k in ['IMLValues', 'investigationTimeSpan', 'IMT']:
                dic.pop(k, None)

            return dic

        return self.sort((s, norm(v)) for s, v in values)


class HazardCurveDBWriterTestCase(HazardCurveDBBaseTestCase):
    """
    Unit tests for the HazardCurveDBWriter class, which serializes
    hazard curvess to the database.
    """
    def test_serialize(self):
        """serialize() inserts the output and the hazard_map_data records."""
        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set.all()))

        # Call the function under test.
        self.writer.serialize(HAZARD_CURVE_DATA())

        # After calling the function under test we see the expected output.
        self.job = models.OqJob.objects.get(id=self.job.id)
        self.assertEqual(1, len(self.job.output_set.all()))

        # After calling the function under test we see the expected map data.
        output = self.job.output_set.get()
        self.assertEqual(4, len(output.hazardcurve_set.all()))
        self.assertEqual(0, len(output.lossmap_set.all()))

        # read data from the DB and check that it's equal to the original data
        inserted_data = []

        for hc in output.hazardcurve_set.all():
            for hcd in hc.hazardcurvedata_set.all():
                location = hcd.location
                node = (Site(location.x, location.y),
                        {'PoEValues': hcd.poes})
                if hc.end_branch_label:
                    node[1]['endBranchLabel'] = hc.end_branch_label
                else:
                    node[1]['statistics'] = hc.statistic_type
                    if hc.quantile is not None:
                        node[1]['quantileValue'] = hc.quantile

                inserted_data.append(node)

        self.assertEquals(self.normalize(HAZARD_CURVE_DATA()),
                          self.normalize(inserted_data))


class HazardCurveDBReaderTestCase(HazardCurveDBBaseTestCase):
    """
    Unit tests for the HazardMapDBReader class, which deserializes
    hazard maps from the database.
    """
    def test_deserialize(self):
        """Hazard map is read back correctly"""
        self.writer.serialize(HAZARD_CURVE_DATA())

        data = self.reader.deserialize(self.writer.output.id)

        def _normalize(data):
            result = []

            for pt, val in data:
                new = val.copy()
                new['investigationTimeSpan'] = \
                    float(new['investigationTimeSpan'])
                result.append((pt, new))

            return result

        self.assertEquals(self.sort(_normalize(HAZARD_CURVE_DATA())),
                          self.sort(_normalize(data)))


class GmfDBBaseTestCase(unittest.TestCase, helpers.DbTestMixin):
    """Common code for ground motion field db reader/writer test"""
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def setUp(self):
        self.job = self.setup_classic_job()
        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = GmfDBWriter(output_path, self.job.id)
        self.reader = GmfDBReader()

    def normalize(self, values):
        def sort_key(v):
            return v[0].longitude, v[0].latitude, v[1]

        return sorted(values, key=sort_key)


class GmfDBWriterTestCase(GmfDBBaseTestCase):
    """
    Unit tests for the GmfDBWriter class, which serializes
    ground motion fields to the database.
    """
    def test_serialize(self):
        """serialize() inserts the output and the gmf_data records."""
        # This job has no outputs before calling the function under test.
        self.assertEqual(0, len(self.job.output_set.all()))

        # Call the function under test.
        self.writer.serialize(GMF_DATA())

        # Reload job row.
        self.job = models.OqJob.objects.get(id=self.job.id)
        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set.all()))

        # After calling the function under test we see the expected map data.
        output = self.job.output_set.get()
        self.assertEqual(0, len(output.hazardcurve_set.all()))
        self.assertEqual(0, len(output.lossmap_set.all()))
        self.assertEqual(4, len(output.gmfdata_set.all()))

        # read data from the DB and check that it's equal to the original data
        inserted_data = []

        for gmfd in output.gmfdata_set.all():
            location = gmfd.location
            inserted_data.append((Site(location.x, location.y),
                                  {'groundMotion': gmfd.ground_motion}))

        self.assertEquals(self.normalize(GMF_DATA().items()),
                          self.normalize(inserted_data))


class GmfDBReaderTestCase(GmfDBBaseTestCase):
    """
    Unit tests for the GmfDBReader class, which deserializes
    ground motion fields from the database.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_deserialize(self):
        """Ground motion field is read back correctly"""
        self.writer.serialize(GMF_DATA())

        data = self.reader.deserialize(self.writer.output.id)

        self.assertEquals(self.normalize(GMF_DATA().items()),
                          self.normalize(data.items()))
