# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import os
import unittest

from django.contrib.gis.geos import GEOSGeometry

from openquake.db import models
from openquake.output.risk import (
    LossCurveDBWriter, LossMapDBWriter, LossCurveDBReader, LossMapDBReader)
from openquake.shapes import Site, Curve

from tests.utils import helpers

# The data below was captured (and subsequently modified for testing purposes)
# by running
#
#   bin/openquake --config-file=demos/classical_psha_simple/config.gem
#
# and putting a breakpoint in openquake/output/risk.py:CurveXMLWriter.write()
RISK_LOSS_CURVE_DATA = [
    (Site(-118.077721, 33.852034),
     [Curve([(3.18e-06, 1.0), (8.81e-06, 1.0), (1.44e-05, 1.0),
             (2.00e-05, 1.0)]), None]),

    (Site(-118.077721, 33.852034),
     [Curve([(7.18e-06, 1.0), (1.91e-05, 1.0), (3.12e-05, 1.0),
             (4.32e-05, 1.0)]), None]),

    (Site(-118.077721, 33.852034),
     [Curve([(5.48e-06, 1.0), (1.45e-05, 1.0), (2.36e-05, 1.0),
             (3.27e-05, 1.0)]), None]),

    (Site(-118.077721, 33.852034),
     [Curve([(9.77e-06, 1.0), (2.64e-05, 1.0), (4.31e-05, 1.0),
             (5.98e-05, 1.0)]), None]),
]


class LossCurveDBBaseTestCase(unittest.TestCase, helpers.DbTestCase):
    """Common code for loss curve db reader/writer test"""
    def setUp(self):
        path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, "LCB-exposure.yaml")
        inputs = [("exposure", path)]
        self.job = self.setup_classic_job(inputs=inputs)

        [input] = models.inputs4job(self.job.id, input_type="exposure",
                                    path=path)
        owner = models.OqUser.objects.get(user_name="openquake")
        emdl = models.ExposureModel(
            owner=owner, input=input, description="LCB test exposure model",
            category="LCB cars", stco_unit="peanuts", stco_type="aggregated")
        emdl.save()

        asset_data = [
            (Site(-118.077721, 33.852034),
             {u'stco': 5.07, u'asset_ref': u'a5625',
              u'taxonomy': u'HAZUS_RM1L_LC'}),

            (Site(-118.077721, 33.852034),
             {u'stco': 5.63, u'asset_ref': u'a5629',
              u'taxonomy': u'HAZUS_URML_LC'}),

            (Site(-118.077721, 33.852034),
             {u'stco': 11.26, u'asset_ref': u'a5630',
              u'taxonomy': u'HAZUS_URML_LS'}),

            (Site(-118.077721, 33.852034),
             {u'stco': 5.5, u'asset_ref': u'a5636',
              u'taxonomy': u'HAZUS_C3L_MC'}),
        ]
        for idx, (site, adata) in enumerate(asset_data):
            location = GEOSGeometry(site.point.to_wkt())
            asset = models.ExposureData(exposure_model=emdl, site=location,
                                        **adata)
            asset.save()
            RISK_LOSS_CURVE_DATA[idx][1][1] = asset

        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = LossCurveDBWriter(output_path, self.job.id)
        self.reader = LossCurveDBReader()

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def normalize(self, values):
        result = []
        for site, [curve, asset] in values:
            try:
                asset_ref = asset.asset_ref
            except:
                asset_ref = asset["assetID"]
            result.append((site, (curve, {'asset_ref': asset_ref})))

        return sorted(result, key=lambda v: v[1][1]['asset_ref'])


class LossCurveDBWriterTestCase(LossCurveDBBaseTestCase):
    """
    Unit tests for the LossCurveDBWriter class, which serializes
    loss curves to the database.
    """
    def test_serialize(self):
        """All the records are inserted correctly."""
        output = self.writer.output

        # Call the function under test.
        self.writer.serialize(RISK_LOSS_CURVE_DATA)

        # output record
        self.assertEqual(1, len(self.job.output_set.all()))

        output = self.job.output_set.get()
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(self.display_name, output.display_name)
        self.assertEqual("loss_curve", output.output_type)

        # loss curve record
        self.assertEqual(1, len(output.losscurve_set.all()))

        loss_curve = output.losscurve_set.get()

        self.assertEqual(loss_curve.unit, "peanuts")
        self.assertEqual(loss_curve.end_branch_label, None)
        self.assertEqual(loss_curve.category, "LCB cars")

        # loss curve data records
        self.assertEqual(4, len(loss_curve.losscurvedata_set.all()))

        inserted_data = []

        for lcd in loss_curve.losscurvedata_set.all():
            loc = lcd.location

            data = (Site(loc.x, loc.y),
                    (Curve(zip(lcd.losses, lcd.poes)),
                    {u'assetID': lcd.asset_ref}))

            inserted_data.append(data)

        self.assertEquals(self.normalize(RISK_LOSS_CURVE_DATA),
                          self.normalize(inserted_data))


class LossCurveDBReaderTestCase(LossCurveDBBaseTestCase):
    """
    Unit tests for the LossCurveDBReader class, which deserializes
    loss curves from the database.
    """
    def test_deserialize(self):
        """
        Loss curve is read back correctly
        """
        self.writer.serialize(RISK_LOSS_CURVE_DATA)

        # Call the function under test.
        data = self.reader.deserialize(self.writer.output.id)

        self.assertEquals(self.normalize(RISK_LOSS_CURVE_DATA),
                          self.normalize(data))


SITE_A = Site(-117.0, 38.0)

SITE_B = Site(-118.0, 39.0)

LOSS_MAP_METADATA = {
    'nrmlID': 'test_nrml_id',
    'riskResultID': 'test_rr_id',
    'lossMapID': 'test_lm_id',
    'endBranchLabel': 'test_ebl',
    'lossCategory': 'economic_loss',
    'unit': 'EUR'}

SCENARIO_LOSS_MAP_METADATA = LOSS_MAP_METADATA.copy()
SCENARIO_LOSS_MAP_METADATA.update({'scenario': True})

SITE_A_SCENARIO_LOSS_ONE = {'mean_loss': 0, 'stddev_loss': 100}
SITE_A_SCENARIO_LOSS_TWO = {'mean_loss': 5, 'stddev_loss': 2000.0}

SITE_B_SCENARIO_LOSS_ONE = {'mean_loss': 120000.0, 'stddev_loss': 2000.0}

SAMPLE_SCENARIO_LOSS_MAP_DATA = [
    SCENARIO_LOSS_MAP_METADATA,
    (SITE_A, [[SITE_A_SCENARIO_LOSS_ONE, {'assetID': 'asset1'}],
              [SITE_A_SCENARIO_LOSS_TWO, {'assetID': 'asset2'}]]),
    (SITE_B, [[SITE_B_SCENARIO_LOSS_ONE, {'assetID': 'asset3'}]])]

NONSCENARIO_LOSS_MAP_METADATA = LOSS_MAP_METADATA.copy()
NONSCENARIO_LOSS_MAP_METADATA.update({
    'poE': 0.6,
    'scenario': False,
    'timeSpan': 1,
    })


SITE_A_NONSCENARIO_LOSS_ONE = {'value': 12}
SITE_A_NONSCENARIO_LOSS_TWO = {'value': 66}

SITE_B_NONSCENARIO_LOSS_ONE = {'value': 1000.0}

SAMPLE_NONSCENARIO_LOSS_MAP_DATA = [
    NONSCENARIO_LOSS_MAP_METADATA,
    (SITE_A, [[SITE_A_NONSCENARIO_LOSS_ONE, None],
              [SITE_A_NONSCENARIO_LOSS_TWO, None]]),
    (SITE_B, [[SITE_B_NONSCENARIO_LOSS_ONE, None]])]


class LossMapDBBaseTestCase(unittest.TestCase, helpers.DbTestCase):
    """Common code for loss map DB reader/writer test"""
    def setUp(self):
        path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, "LMB-exposure.yaml")
        inputs = [("exposure", path)]
        self.job = self.setup_classic_job(inputs=inputs)

        [input] = models.inputs4job(self.job.id, input_type="exposure",
                                    path=path)
        owner = models.OqUser.objects.get(user_name="openquake")
        emdl = models.ExposureModel(
            owner=owner, input=input, description="LMB test exposure model",
            category="LMB yachts", stco_unit="oranges", stco_type="aggregated")
        emdl.save()

        asset_data = [
            ("asset_a_1", SITE_A,
             {u'stco': 5.07, u'asset_ref': u'a1711',
              u'taxonomy': u'HAZUS_RM1L_LC'}),

            ("asset_a_2", SITE_A,
             {u'stco': 5.63, u'asset_ref': u'a1712',
              u'taxonomy': u'HAZUS_URML_LC'}),

            ("asset_b_1", SITE_B,
             {u'stco': 5.5, u'asset_ref': u'a1713',
              u'taxonomy': u'HAZUS_C3L_MC'}),
        ]
        for idx, (name, site, adata) in enumerate(asset_data):
            location = GEOSGeometry(site.point.to_wkt())
            asset = models.ExposureData(exposure_model=emdl, site=location,
                                        **adata)
            asset.save()
            setattr(self, name, asset)

        SAMPLE_NONSCENARIO_LOSS_MAP_DATA[1][1][0][1] = self.asset_a_1
        SAMPLE_NONSCENARIO_LOSS_MAP_DATA[1][1][1][1] = self.asset_a_2
        SAMPLE_NONSCENARIO_LOSS_MAP_DATA[2][1][0][1] = self.asset_b_1

        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = LossMapDBWriter(output_path, self.job.id)
        self.reader = LossMapDBReader()

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)


class LossMapDBWriterTestCase(LossMapDBBaseTestCase):
    """
    Unit tests for the LossMapDBWriter class, which serializes
    loss maps to the database.
    """
    def test_serialize_scenario(self):
        """
        All the records for scenario loss maps are inserted correctly.
        """

        output = self.writer.output

        # Call the function under test.
        data = SAMPLE_SCENARIO_LOSS_MAP_DATA
        self.writer.serialize(data)

        # Output record
        self.assertEqual(1, len(self.job.output_set.all()))
        output = self.job.output_set.get()
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(self.display_name, output.display_name)
        self.assertEqual("loss_map", output.output_type)

        # LossMap record
        self.assertEqual(1, len(output.lossmap_set.all()))
        metadata = output.lossmap_set.get()
        self.assertEqual(SCENARIO_LOSS_MAP_METADATA['scenario'],
                         metadata.scenario)
        self.assertEqual(SCENARIO_LOSS_MAP_METADATA['endBranchLabel'],
                         metadata.end_branch_label)
        self.assertEqual(SCENARIO_LOSS_MAP_METADATA['lossCategory'],
                         metadata.category)
        self.assertEqual(SCENARIO_LOSS_MAP_METADATA['unit'],
                         metadata.unit)
        self.assertEqual(None, metadata.poe)

        # LossMapData records
        self.assertEqual(3, len(metadata.lossmapdata_set.all()))
        [data_a, data_b, data_c] = sorted(metadata.lossmapdata_set.all(),
                                          key=lambda d: d.id)

        self.assertEqual(SITE_A, Site(*data_a.location.coords))

        self.assertEqual(
            SAMPLE_SCENARIO_LOSS_MAP_DATA[1][1][0][1]['assetID'],
            data_a.asset_ref)
        # self.assertEqual(self.asset_a_1.asset_ref, data_a.asset_ref)
        self.assertEqual(SITE_A_SCENARIO_LOSS_ONE['mean_loss'],
                        data_a.value)
        self.assertEqual(SITE_A_SCENARIO_LOSS_ONE['stddev_loss'],
                         data_a.std_dev)

        self.assertEqual(SITE_A, Site(*data_b.location.coords))
        self.assertEqual(
            SAMPLE_SCENARIO_LOSS_MAP_DATA[1][1][1][1]['assetID'],
            data_b.asset_ref)
        self.assertEqual(SITE_A_SCENARIO_LOSS_TWO['mean_loss'],
                         data_b.value)
        self.assertEqual(SITE_A_SCENARIO_LOSS_TWO['stddev_loss'],
                         data_b.std_dev)

        self.assertEqual(SITE_B, Site(*data_c.location.coords))
        self.assertEqual(
            SAMPLE_SCENARIO_LOSS_MAP_DATA[2][1][0][1]['assetID'],
            data_c.asset_ref)
        self.assertEqual(SITE_B_SCENARIO_LOSS_ONE['mean_loss'],
                         data_c.value)
        self.assertEqual(SITE_B_SCENARIO_LOSS_ONE['stddev_loss'],
                         data_c.std_dev)

    def test_serialize_nonscenario(self):
        """
        All the records for non-scenario loss maps are inserted correctly.
        """

        output = self.writer.output

        # Call the function under test.
        data = SAMPLE_NONSCENARIO_LOSS_MAP_DATA

        self.writer.serialize(data)

        # Output record
        self.assertEqual(1, len(self.job.output_set.all()))
        output = self.job.output_set.get()
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(self.display_name, output.display_name)
        self.assertEqual("loss_map", output.output_type)

        # LossMap record
        self.assertEqual(1, len(output.lossmap_set.all()))

        metadata = output.lossmap_set.get()
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['scenario'],
                         metadata.scenario)
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['endBranchLabel'],
                         metadata.end_branch_label)
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['lossCategory'],
                         metadata.category)
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['unit'],
                         metadata.unit)
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['timeSpan'],
                         metadata.timespan)
        self.assertEqual(NONSCENARIO_LOSS_MAP_METADATA['poE'],
                         metadata.poe)

        # LossMapData records
        self.assertEqual(3, len(metadata.lossmapdata_set.all()))
        [data_a, data_b, data_c] = sorted(metadata.lossmapdata_set.all(),
                                          key=lambda d: d.id)

        self.assertEqual(SITE_A, Site(*data_a.location.coords))
        self.assertEqual(self.asset_a_1.asset_ref, data_a.asset_ref)
        self.assertEqual(SITE_A_NONSCENARIO_LOSS_ONE['value'],
                         data_a.value)

        self.assertEqual(SITE_A, Site(*data_b.location.coords))
        self.assertEqual(self.asset_a_2.asset_ref, data_b.asset_ref)
        self.assertEqual(SITE_A_NONSCENARIO_LOSS_TWO['value'],
                         data_b.value)

        self.assertEqual(SITE_B, Site(*data_c.location.coords))
        self.assertEqual(self.asset_b_1.asset_ref, data_c.asset_ref)
        self.assertEqual(SITE_B_NONSCENARIO_LOSS_ONE['value'],
                         data_c.value)


class LossMapDBReaderTestCase(LossMapDBBaseTestCase):
    """
    Unit tests for the LossMapDBReader class, which deserializes
    loss maps from the database.
    """
    def test_deserialize_scenario(self):
        """
        Scenario loss map is read back correctly
        """
        self.writer.serialize(SAMPLE_SCENARIO_LOSS_MAP_DATA)

        # Call the function under test.
        data = self.reader.deserialize(self.writer.output.id)
        data.pop(0)
        data = sorted(data, key=lambda e: (e[0].longitude, e[0].latitude))

        # compare metadata, ignoring fields that we know aren't saved
        result_metadata = dict(SCENARIO_LOSS_MAP_METADATA)
        result_metadata.pop('nrmlID')
        result_metadata.pop('riskResultID')

        # before overwriting, check the value is not set
        self.assertTrue('poe' not in result_metadata)
        result_metadata['poe'] = None

        self.assertEquals(result_metadata, result_metadata)

        # compare sites ad losses
        self.assertEquals(
            self.normalize(SAMPLE_SCENARIO_LOSS_MAP_DATA[1:]),
            self.normalize(data))

    def test_deserialize_nonscenario(self):
        """
        Scenario loss map is read back correctly
        """
        self.writer.serialize(SAMPLE_NONSCENARIO_LOSS_MAP_DATA)

        # Call the function under test.
        data = self.reader.deserialize(self.writer.output.id)
        data.pop(0)
        data = sorted(data, key=lambda e: (e[0].longitude, e[0].latitude))

        # compare metadata, ignoring fields that we know aren't saved
        result_metadata = dict(NONSCENARIO_LOSS_MAP_METADATA)
        result_metadata.pop('nrmlID')
        result_metadata.pop('riskResultID')

        self.assertEquals(result_metadata, result_metadata)

        # compare sites ad losses
        self.assertEquals(
            self.normalize(SAMPLE_NONSCENARIO_LOSS_MAP_DATA[1:]),
            self.normalize(data))

    def normalize(self, data):
        def dict_or_obj(e):
            try:
                return e[1].asset_ref
            except:
                return e[1]["assetID"]

        data = sorted(data, key=lambda e: (e[0].longitude, e[0].latitude))
        result = []

        for site, losses in data:
            nlosses = []
            for loss, asset in sorted(losses, key=dict_or_obj):
                if isinstance(asset, models.ExposureData):
                    nlosses.append([loss, {"assetID": asset.asset_ref}])
                else:
                    nlosses.append([loss, asset])

            result.append((site, nlosses))

        return result
