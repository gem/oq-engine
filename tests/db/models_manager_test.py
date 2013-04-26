# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

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
Test Django custom model managers
"""

import random
import unittest

from django.contrib.gis.geos.point import Point
from django.contrib.gis.geos.polygon import Polygon

from openquake.engine.db import models
from openquake.engine.calculators.risk import base

from tests.utils import helpers
from tests.utils.helpers import demo_file


class TestCaseWithAJob(unittest.TestCase):
    """
    Abstract test case class to just setup a job
    """
    def setUp(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username="test_user")
        for i in range(0, random.randint(1, 10)):
            models.LtRealization(
                hazard_calculation=self.job.hazard_calculation,
                ordinal=i, seed=None, weight=1 / (i + 1), sm_lt_path=[i],
                gsim_lt_path=[i], total_items=0, completed_items=0).save()


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
            demo_file('classical_psha_based_risk/job.ini'),
            demo_file('simple_fault_demo_hazard/job.ini'))
        calculator = base.RiskCalculator(self.job)
        calculator.pre_execute()
        self.model = self.job.risk_calculation.exposure_model

        common_fake_args = dict(
            exposure_model=self.model,
            stco=1,
            number_of_units=10,
            reco=1,
            taxonomy="test")

        asset = models.ExposureData(site=Point(0.5, 0.5),
                                    asset_ref="test1",
                                    **common_fake_args)
        asset.save()

        asset = models.ExposureData(site=Point(179.1, 0),
                                    asset_ref="test2",
                                    **common_fake_args)
        asset.save()

    def test_simple_inclusion(self):
        region_constraint = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))

        results = models.ExposureData.objects.contained_in(
            self.model.id, "test", region_constraint, 0, 10)

        self.assertEqual(1, len(list(results)))
        self.assertEqual("test1", results[0].asset_ref)

    def test_inclusion_of_a_pole(self):
        region_constraint = Polygon(
            ((-1, 0), (-1, 1), (1, 1), (1, 0), (-1, 0)))

        results = models.ExposureData.objects.contained_in(
            self.model.id, "test", region_constraint, 0, 10)

        self.assertEqual(1, len(results))
        self.assertEqual("test1", results[0].asset_ref)

        region_constraint = Polygon(
            ((179, 10), (-179, 10), (-179, -10), (179, -10), (179, 10)))

        results = models.ExposureData.objects.contained_in(
            self.model.id, "test", region_constraint, 0, 10)

        self.assertEqual(1, len(list(results)))
        self.assertEqual("test2", results[0].asset_ref)
