# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2014, GEM Foundation.
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
Test Django custom model managers
"""

import mock
import random
import unittest
from collections import namedtuple

from django.contrib.gis.geos.point import Point

from openquake.engine.db import models
from openquake.engine.calculators.risk import base

from openquake.engine.tests.utils import helpers
from openquake.engine.tests.utils.helpers import get_data_path


class TestCaseWithAJob(unittest.TestCase):
    """
    Abstract test case class to just setup a job
    """
    def setUp(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_job(cfg, username="test_user")
        for i in range(0, random.randint(1, 10)):
            lt_model = models.LtSourceModel.objects.create(
                hazard_calculation=self.job, ordinal=i, sm_lt_path=[i])
            models.LtRealization(
                lt_model=lt_model, ordinal=i,
                weight=1 / (i + 1), gsim_lt_path=[i]).save()


class OutputManagerTestCase(TestCaseWithAJob):
    """
    Test the OutputManager
    """

    def setUp(self):
        super(OutputManagerTestCase, self).setUp()
        self.manager = models.Output.objects

    def test_create_output(self):
        output = self.manager.create_output(
            self.job, "fake output", "hazard_curve")
        self.assertEqual(1, self.manager.filter(pk=output.id).count())

        output = self.manager.create_output(
            self.job, "another fake output", "hazard_map")
        self.assertEqual(1, self.manager.filter(pk=output.id).count())


class ExposureContainedInTestCase(unittest.TestCase):
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))
        calculator = base.RiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)
        calculator.pre_execute()
        self.rc = self.job.risk_calculation

        common_fake_args = dict(
            exposure_model=self.rc.exposure_model, taxonomy="test")

        asset = models.ExposureData(site=Point(0.5, 0.5),
                                    asset_ref="test1",
                                    **common_fake_args)
        asset.save()

        asset = models.ExposureData(site=Point(179.1, 0),
                                    asset_ref="test2",
                                    **common_fake_args)
        asset.save()


class AssetManagerTestCase(unittest.TestCase):
    base = 'openquake.engine.db.models.AssetManager.'

    def setUp(self):
        self.manager = models.ExposureData.objects

    def test_get_asset_chunk_query_args(self):
        rc = mock.Mock()
        rc.exposure_model.id = 0
        rc.region_constraint.wkt = "REGION CONSTRAINT"

        p1 = mock.patch(self.base + '_get_people_query_helper')
        m1 = p1.start()
        m1.return_value = ("occupants_fields", "occupants_cond",
                           "occupancy_join", ("occ_arg1", "occ_arg2"))
        p2 = mock.patch(self.base + '_get_cost_types_query_helper')
        m2 = p2.start()
        m2.return_value = ("cost_type_fields", "cost_type_joins")

        asset_ids = [13, 14]
        expected_query = """\
        SELECT riski.exposure_data.*,
               occupants_fields AS people,
               cost_type_fields
        FROM riski.exposure_data
        occupancy_join
        ON riski.exposure_data.id = riski.occupancy.exposure_data_id
        cost_type_joins
        WHERE exposure_model_id = %s
        AND riski.exposure_data.id IN %s
        AND occupants_cond
        GROUP BY riski.exposure_data.id
        ORDER BY riski.exposure_data.id"""
        try:
            query, args = self.manager._get_asset_chunk_query_args(
                rc, asset_ids)
            self.assertEqual(expected_query, query.rstrip())
            self.assertEqual(args, (0, asset_ids, 'occ_arg1', 'occ_arg2'))
        finally:
            p1.stop()
            p2.stop()

    def test_get_people_query_helper_population_no_event(self):
        field, cond, join, args = self.manager._get_people_query_helper(
            "population", None)
        self.assertEqual("number_of_units", field)
        self.assertEqual("1 = 1", cond)
        self.assertEqual("", join)
        self.assertEqual(args, ())

    def test_get_people_query_helper_population_time_event(self):
        field, cond, join, args = self.manager._get_people_query_helper(
            "population", "day")
        self.assertEqual("number_of_units", field)
        self.assertEqual("1 = 1", cond)
        self.assertEqual("", join)
        self.assertEqual(args, ())

    def test_get_people_query_helper_buildings_no_event(self):
        field, cond, join, args = self.manager._get_people_query_helper(
            "buildings", None)
        self.assertEqual("AVG(riski.occupancy.occupants)", field)
        self.assertEqual("1 = 1", cond)
        self.assertEqual("LEFT JOIN riski.occupancy", join)
        self.assertEqual(args, ())

    def test_get_people_query_helper_buildings_time_event(self):
        field, cond, join, args = self.manager._get_people_query_helper(
            "buildings", "day")
        self.assertEqual("AVG(riski.occupancy.occupants)", field)
        self.assertEqual("riski.occupancy.period = %s", cond)
        self.assertEqual("LEFT JOIN riski.occupancy", join)
        self.assertEqual(args, ("day",))

    def test_get_cost_types_query_helper_no_cost_types(self):
        fields, joins = self.manager._get_cost_types_query_helper([])

        self.assertEqual("", fields)
        self.assertEqual("", joins)

    def test_get_cost_types_query_helper_one_cost_type(self):
        cost = namedtuple("cost", "name id")
        fields, joins = self.manager._get_cost_types_query_helper(
            [cost("structural", 1)])

        self.assertEqual(
            "max(structural.converted_cost) AS structural, "
            "max(structural.converted_retrofitted_cost) AS retrofitted_structural, "
            "max(structural.deductible_absolute) AS deductible_structural, "
            "max(structural.insurance_limit_absolute) AS insurance_limit_structural",
            fields)
        self.assertEqual("""
            LEFT JOIN riski.cost AS structural
            ON structural.cost_type_id = '1' AND
            structural.exposure_data_id = riski.exposure_data.id""",
            joins)

    def test_get_cost_types_query_helper_several_cost_types(self):
        cost = namedtuple("cost", "name id")
        fields, joins = self.manager._get_cost_types_query_helper(
            [cost("structural", 1), cost("nonstructural", 2)])

        self.assertEqual(
            "max(structural.converted_cost) AS structural, "
            "max(structural.converted_retrofitted_cost) AS retrofitted_structural, "
            "max(structural.deductible_absolute) AS deductible_structural, "
            "max(structural.insurance_limit_absolute) AS insurance_limit_structural, "
            "max(nonstructural.converted_cost) AS nonstructural, "
            "max(nonstructural.converted_retrofitted_cost) AS retrofitted_nonstructural, "
            "max(nonstructural.deductible_absolute) AS deductible_nonstructural, "
            "max(nonstructural.insurance_limit_absolute) AS insurance_limit_nonstructural",
            fields)
        self.assertEqual("""
            LEFT JOIN riski.cost AS structural
            ON structural.cost_type_id = '1' AND
            structural.exposure_data_id = riski.exposure_data.id
            LEFT JOIN riski.cost AS nonstructural
            ON nonstructural.cost_type_id = '2' AND
            nonstructural.exposure_data_id = riski.exposure_data.id""",
            joins)
