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


import unittest
import os

from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.event_based.core import (
    EventBasedRiskCalculator)
from openquake.db import models
from openquake.input.exposure import ExposureDBWriter
from openquake.input.fragility import FragilityDBWriter
from openquake.output.hazard import GmfDBWriter
from openquake.output.hazard import HazardCurveDBWriter
from openquake.parser.exposure import ExposureModelFile
from openquake.parser.fragility import FragilityModelParser
from openquake.shapes import Site

from tests.utils import helpers


CONTINUOUS_FMODEL = os.path.join(helpers.SCHEMA_DIR, "examples/fragm_c.xml")
DISCRETE_FMODEL = os.path.join(helpers.SCHEMA_DIR, "examples/fragm_d.xml")
TEST_FILE = 'exposure-portfolio.xml'


# See data in output_hazard_unittest.py
def HAZARD_CURVE_DATA():
    return [
        (Site(-122.2, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.354, 0.114, 0.023, 0.002],
          'IMT': 'PGA',
          'statistics': 'mean'}),
        (Site(-122.1, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.454, 0.214, 0.123, 0.102],
          'IMT': 'PGA',
          'statistics': 'mean'}),
        (Site(-122.2, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.354, 0.114, 0.023, 0.002],
          'IMT': 'PGA',
          'statistics': 'quantile',
          'quantileValue': 0.25}),
        (Site(-122.1, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.454, 0.214, 0.123, 0.102],
          'IMT': 'PGA',
          'statistics': 'quantile',
          'quantileValue': 0.25}),
        (Site(-122.2, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.354, 0.114, 0.023, 0.002],
          'IMT': 'PGA',
          'endBranchLabel': '1'}),
        (Site(-122.1, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.454, 0.214, 0.123, 0.102],
          'IMT': 'PGA',
          'endBranchLabel': '1'}),
    ]


def GMF_DATA():
    return [
        {
            Site(-117, 40): {'groundMotion': 0.1},
            Site(-116, 40): {'groundMotion': 0.2},
            Site(-116, 41): {'groundMotion': 0.3},
            Site(-117, 41): {'groundMotion': 0.4},
        },
        {
            Site(-117, 40): {'groundMotion': 0.5},
            Site(-116, 40): {'groundMotion': 0.6},
            Site(-116, 41): {'groundMotion': 0.7},
            Site(-117, 41): {'groundMotion': 0.8},
        },
        {
            Site(-117, 42): {'groundMotion': 1.0},
            Site(-116, 42): {'groundMotion': 1.1},
            Site(-116, 41): {'groundMotion': 1.2},
            Site(-117, 41): {'groundMotion': 1.3},
        },
    ]


class HazardCurveDBReadTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Test the code to read hazard curves from DB.
    """
    def setUp(self):
        self.job = self.setup_classic_job()
        output_path = self.generate_output_path(self.job)
        hcw = HazardCurveDBWriter(output_path, self.job.id)
        hcw.serialize(HAZARD_CURVE_DATA())

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_read_curve(self):
        """Verify _get_db_curve."""
        the_job = helpers.create_job({}, job_id=self.job.id)
        calculator = ClassicalRiskCalculator(the_job)

        curve1 = calculator._get_db_curve(Site(-122.2, 37.5))
        self.assertEqual(list(curve1.abscissae),
                          [0.005, 0.007, 0.0098, 0.0137])
        self.assertEqual(list(curve1.ordinates),
                          [0.354, 0.114, 0.023, 0.002])

        curve2 = calculator._get_db_curve(Site(-122.1, 37.5))
        self.assertEqual(list(curve2.abscissae),
                          [0.005, 0.007, 0.0098, 0.0137])
        self.assertEqual(list(curve2.ordinates),
                          [0.454, 0.214, 0.123, 0.102])


class GmfDBReadTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Test the code to read the ground motion fields from DB.
    """
    def setUp(self):
        self.job = self.setup_classic_job()
        for gmf in GMF_DATA():
            output_path = self.generate_output_path(self.job)
            hcw = GmfDBWriter(output_path, self.job.id)
            hcw.serialize(gmf)

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_site_keys(self):
        """Verify _sites_to_gmf_keys"""
        params = {
            'REGION_VERTEX': '40,-117, 42,-117, 42,-116, 40,-116',
            'REGION_GRID_SPACING': '1.0'}

        the_job = helpers.create_job(params, job_id=self.job.id)
        calculator = EventBasedRiskCalculator(the_job)

        keys = calculator._sites_to_gmf_keys([Site(-117, 40), Site(-116, 42)])

        self.assertEqual(["0!0", "2!1"], keys)

    def test_read_gmfs(self):
        """Verify _get_db_gmfs."""
        params = {
            'REGION_VERTEX': '40,-117, 42,-117, 42,-116, 40,-116',
            'REGION_GRID_SPACING': '1.0'}

        the_job = helpers.create_job(params, job_id=self.job.id)
        calculator = EventBasedRiskCalculator(the_job)

        self.assertEqual(3, len(calculator._gmf_db_list(self.job.id)))

        # only the keys in gmfs are used
        gmfs = calculator._get_db_gmfs([], self.job.id)
        self.assertEqual({}, gmfs)

        # only the keys in gmfs are used
        sites = [Site(lon, lat)
                        for lon in xrange(-117, -115)
                        for lat in xrange(40, 43)]
        gmfs = calculator._get_db_gmfs(sites, self.job.id)
        # avoid rounding errors
        for k, v in gmfs.items():
            gmfs[k] = [round(i, 1) for i in v]

        self.assertEqual({
                '0!0': [0.1, 0.5, 0.0],
                '0!1': [0.2, 0.6, 0.0],
                '1!0': [0.4, 0.8, 1.3],
                '1!1': [0.3, 0.7, 1.2],
                '2!0': [0.0, 0.0, 1.0],
                '2!1': [0.0, 0.0, 1.1],
                }, gmfs)


class ExposureDBWriterTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Test the code to serialize exposure model to DB.
    """
    job = None
    path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, TEST_FILE)

    @classmethod
    def setUpClass(cls):
        inputs = [("exposure", cls.path)]
        cls.job = cls.setup_classic_job(inputs=inputs)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        [input] = models.inputs4job(self.job.id, input_type="exposure")
        self.writer = ExposureDBWriter(input)

    def test_read_exposure(self):
        parser = ExposureModelFile(self.path)

        # call tested function
        self.writer.serialize(parser)

        # test results
        model = self.writer.model

        self.assertFalse(model is None)

        # Make sure the exposure model is associated with the proper
        # input and job.
        self.assertEqual(self.path, model.input.path)
        self.assertEqual("exposure", model.input.input_type)
        self.assertEqual(1, len(models.inputs4job(self.job.id)))

        # check model fields
        self.assertEqual("Collection of existing building in downtown Pavia",
                          model.description)
        self.assertEqual("buildings", model.category)

        self.assertEqual("per_asset", model.area_type)
        self.assertEqual("GBP", model.area_unit)

        self.assertEqual("per_area", model.coco_type)
        self.assertEqual("CHF", model.coco_unit)

        self.assertEqual("aggregated", model.reco_type)
        self.assertEqual("EUR", model.reco_unit)

        self.assertEqual("aggregated", model.stco_type)
        self.assertEqual("USD", model.stco_unit)

        self.assertEqual("Pavia taxonomy", model.taxonomy_source)

        # check asset instances
        assets = sorted(model.exposuredata_set.all(), key=lambda e: e.value)

        def _to_site(pg_point):
            return Site(pg_point.x, pg_point.y)

        self.assertEqual("asset_01", assets[0].asset_ref)
        self.assertEqual(120, assets[0].area)
        self.assertEqual(12.95, assets[0].coco)
        self.assertEqual(55, assets[0].deductible)
        self.assertEqual(999, assets[0].ins_limit)
        self.assertEqual(7, assets[0].number_of_units)
        self.assertEqual(109876, assets[0].reco)
        self.assertEqual(150000, assets[0].stco)
        self.assertEqual(150000, assets[0].value)
        self.assertEqual("RC/DMRF-D/LR", assets[0].taxonomy)
        self.assertEqual(Site(9.15000, 45.16667), _to_site(assets[0].site))
        self.assertEqual(0, assets[0].occupancy_set.count())

        self.assertEqual("asset_02", assets[1].asset_ref)
        self.assertEqual(119, assets[1].area)
        self.assertEqual(21.95, assets[1].coco)
        self.assertEqual(66, assets[1].deductible)
        self.assertEqual(1999, assets[1].ins_limit)
        self.assertEqual(6, assets[1].number_of_units)
        self.assertEqual(205432, assets[1].reco)
        self.assertEqual(250000, assets[1].stco)
        self.assertEqual(250000, assets[1].value)
        self.assertEqual("RC/DMRF-D/HR", assets[1].taxonomy)
        self.assertEqual(Site(9.15333, 45.12200), _to_site(assets[1].site))
        day, night = sorted(assets[1].occupancy_set.all(),
                            key=lambda o: o.description)
        self.assertEqual(12, day.occupants)
        self.assertEqual("day", day.description)
        self.assertEqual(50, night.occupants)
        self.assertEqual("night", night.description)

        self.assertEqual("asset_03", assets[2].asset_ref)
        self.assertEqual(118, assets[2].area)
        self.assertEqual(30.95, assets[2].coco)
        self.assertEqual(77, assets[2].deductible)
        self.assertEqual(2888, assets[2].ins_limit)
        self.assertEqual(5, assets[2].number_of_units)
        self.assertEqual(495432, assets[2].reco)
        self.assertEqual(500000, assets[2].stco)
        self.assertEqual(500000, assets[2].value)
        self.assertEqual("RC/DMRF-D/LR", assets[2].taxonomy)
        self.assertEqual(Site(9.14777, 45.17999), _to_site(assets[2].site))
        morning, afternoon = sorted(assets[2].occupancy_set.all(),
                                    key=lambda o: o.description)
        self.assertEqual(5, afternoon.occupants)
        self.assertEqual("late afternoon", afternoon.description)
        self.assertEqual(36, morning.occupants)
        self.assertEqual("early morning", morning.description)


class CFragilityDBWriterTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Test the code that writes continuous fragility model data to the database
    """
    job = None
    path = CONTINUOUS_FMODEL

    @classmethod
    def setUpClass(cls):
        inputs = [("fragility", cls.path)]
        cls.job = cls.setup_classic_job(inputs=inputs)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        [self.input] = models.inputs4job(self.job.id, input_type="fragility")
        self.parser = FragilityModelParser(self.path)
        self.writer = FragilityDBWriter(self.input, self.parser)

    def test_write_continuous_fragility_model_to_db(self):
        # call tested function
        self.writer.serialize()

        # test results
        model = self.writer.model
        self.assertFalse(model is None)

        self.assertIs(None, model.imls)
        self.assertIs(None, model.imt)
        self.assertEqual("continuous", model.format)
        self.assertEqual("Fragility model for Pavia (continuous)",
                         model.description)
        self.assertEqual(["slight", "moderate", "extensive", "complete"],
                         model.lss)
        self.assertIs(self.input, model.input)

        ffcs = model.ffc_set.all().order_by("taxonomy", "ls")
        ffds = model.ffd_set.all()
        self.assertEqual(8, ffcs.count())
        self.assertEqual(0, ffds.count())

        self.assertIs(None, ffcs[0].ftype)
        self.assertEqual("RC/DMRF-D/HR", ffcs[0].taxonomy)
        self.assertEqual("complete", ffcs[0].ls)
        self.assertEqual(108.8, ffcs[0].mean)
        self.assertEqual(123.6, ffcs[0].stddev)

        self.assertIs(None, ffcs[3].ftype)
        self.assertEqual("RC/DMRF-D/HR", ffcs[3].taxonomy)
        self.assertEqual("slight", ffcs[3].ls)
        self.assertEqual(11.18, ffcs[3].mean)
        self.assertEqual(8.28, ffcs[3].stddev)

        self.assertEqual("lognormal", ffcs[5].ftype)
        self.assertEqual("RC/DMRF-D/LR", ffcs[5].taxonomy)
        self.assertEqual("extensive", ffcs[5].ls)
        self.assertEqual(48.05, ffcs[5].mean)
        self.assertEqual(42.49, ffcs[5].stddev)

        self.assertEqual("lognormal", ffcs[6].ftype)
        self.assertEqual("RC/DMRF-D/LR", ffcs[6].taxonomy)
        self.assertEqual("moderate", ffcs[6].ls)
        self.assertEqual(27.98, ffcs[6].mean)
        self.assertEqual(20.677, ffcs[6].stddev)


class DFragilityDBWriterTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Test the code that writes discrete fragility model data to the database
    """
    job = None
    path = DISCRETE_FMODEL

    @classmethod
    def setUpClass(cls):
        inputs = [("fragility", cls.path)]
        cls.job = cls.setup_classic_job(inputs=inputs)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        [self.input] = models.inputs4job(self.job.id, input_type="fragility")
        self.parser = FragilityModelParser(self.path)
        self.writer = FragilityDBWriter(self.input, self.parser)

    def test_write_discrete_fragility_model_to_db(self):
        # call tested function
        self.writer.serialize()

        # test results
        model = self.writer.model
        self.assertFalse(model is None)

        self.assertEqual([7.0, 8.0, 9.0, 10.0, 11.0], model.imls)
        self.assertEqual("mmi", model.imt)
        self.assertEqual("discrete", model.format)
        self.assertEqual("Fragility model for Pavia (discrete)",
                         model.description)
        self.assertEqual(["minor", "moderate", "severe", "collapse"],
                         model.lss)
        self.assertIs(self.input, model.input)

        ffcs = model.ffc_set.all()
        ffds = model.ffd_set.all().order_by("taxonomy", "ls")
        self.assertEqual(0, ffcs.count())
        self.assertEqual(8, ffds.count())

        self.assertEqual("RC/DMRF-D/HR", ffds[0].taxonomy)
        self.assertEqual("collapse", ffds[0].ls)
        self.assertEqual([0.0, 0.0, 0.0, 0.04, 0.64], ffds[0].poes)

        self.assertEqual("RC/DMRF-D/HR", ffds[3].taxonomy)
        self.assertEqual("severe", ffds[3].ls)
        self.assertEqual([0.0, 0.0, 0.0, 0.3, 0.89], ffds[3].poes)

        self.assertEqual("RC/DMRF-D/LR", ffds[5].taxonomy)
        self.assertEqual("minor", ffds[5].ls)
        self.assertEqual([0.0, 0.09, 0.56, 0.91, 0.98], ffds[5].poes)

        self.assertEqual("RC/DMRF-D/LR", ffds[6].taxonomy)
        self.assertEqual("moderate", ffds[6].ls)
        self.assertEqual([0.0, 0.0, 0.04, 0.78, 0.96], ffds[6].poes)
