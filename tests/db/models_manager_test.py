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

from openquake.db import models
from openquake.calculators.risk import general as general_risk

from tests.utils import helpers


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
                gsim_lt_path=[i], total_sources=0, completed_sources=0).save()


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


class HazardCurveManagerTestCase(TestCaseWithAJob):
    """
    Test the manager for HazardCurve
    """
    def setUp(self):
        super(HazardCurveManagerTestCase, self).setUp()
        self.manager = models.HazardCurve.objects
        self.output = models.Output.objects.create_output(
            self.job, "fake output", "hazard_curve")

    def test_create_aggregate_curve(self):
        curve = self.manager.create_aggregate_curve(self.output, "PGA", "mean")
        self.assertEqual(1, self.manager.filter(pk=curve.id).count())

        curve = self.manager.create_aggregate_curve(self.output,
                                            imt="SA(0.025)",
                                            statistics="mean")
        self.assertEqual(1, self.manager.filter(pk=curve.id).count())

        self.assertRaises(ValueError,
                          self.manager.create_aggregate_curve,
                          self.output, "SA(10)", "mean", quantile=0.5)


class HazardCurveDataManagerTestCase(TestCaseWithAJob):
    """
    Test the manager of HazardCurveData objects
    """
    def setUp(self):
        super(HazardCurveDataManagerTestCase, self).setUp()
        self.manager = models.HazardCurveData.objects

        # Setup some data
        # Requires a working version of Django models
        output = models.Output.objects.create_output(
            self.job, "fake output", "hazard_curve")

        curves_per_location = (
            self.job.hazard_calculation.individual_curves_per_location())

        self.a_location = (
            helpers.random_location_generator(max_x=50, max_y=50))
        self.a_bigger_location = helpers.random_location_generator(
                min_x=50,
                min_y=50)

        for curve_nr in range(0, curves_per_location):
            realization = models.LtRealization.objects.all()[curve_nr]
            curve = models.HazardCurve.objects.create(
                output=output,
                lt_realization=realization,
                investigation_time=10,
                imt="PGA", imls=[1, 2, 3])

            models.HazardCurveData.objects.create(
                hazard_curve=curve,
                location=self.a_location.wkt,
                poes=[random.random()])

            models.HazardCurveData.objects.create(
                hazard_curve=curve,
                location=self.a_bigger_location.wkt,
                poes=[random.random()])

    def test_individual_curves(self):
        self.assertEqual(0,
                         len(self.manager.individual_curves(
                             self.job, "fake imt")))

        self.assertEqual(
            self.job.hazard_calculation.individual_curves_per_location() * 2,
            len(self.manager.individual_curves(self.job, "PGA")))

    def test_individual_curves_nr(self):
        # use a fake imt
        self.assertEqual(0,
                         self.manager.individual_curves_nr(
                             self.job, "fake imt"))

        self.assertEqual(
            self.job.hazard_calculation.individual_curves_per_location() * 2,
            self.manager.individual_curves_nr(self.job, "PGA"))

    def test_individual_curves_ordered(self):
        curves = self.manager.individual_curves_ordered(self.job, "PGA")

        previous_curve = curves[0]

        for curve in curves[1:]:
            self.assertTrue(previous_curve.location <= curve.location.wkb)
            previous_curve = curve

    def test_individual_curves_chunks(self):
        location_block_size = 2

        chunks = self.manager.individual_curves_chunks(
            self.job, "PGA", location_block_size=location_block_size)

        self.assertEqual(1, len(chunks))

        locations = chunks[0].locations
        self.assertEqual(len(locations), location_block_size)

        self.assertEqual(str(locations[0]), self.a_location.wkb)

    def test_individual_curves_chunk(self):
        curves = self.manager.individual_curves_chunk(
            self.job, "PGA", 0, 1)
        self.assertEqual(1, len(curves))

        curve = curves[0]
        self.assertEqual(
            sorted(['poes', 'wkb', 'hazard_curve__lt_realization__weight']),
            sorted(curve.keys()))


class ExposureContainedInTestCase(unittest.TestCase):
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'classical_psha_based_risk/job.ini',
            'simple_fault_demo_hazard/job.ini')
        calculator = general_risk.BaseRiskCalculator(self.job)
        calculator.pre_execute()
        self.model = self.job.risk_calculation.model('exposure')

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
            self.model.id,
            region_constraint)
        results = [result for result in results if result.taxonomy == "test"]

        self.assertEqual(1, len(list(results)))
        self.assertEqual("test1", results[0].asset_ref)

    def test_inclusion_of_a_pole(self):
        region_constraint = Polygon(
            ((-1, 0), (-1, 1), (1, 1), (1, 0), (-1, 0)))

        results = models.ExposureData.objects.contained_in(
            self.model.id,
            region_constraint)
        results = [result for result in results if result.taxonomy == "test"]
        self.assertEqual(1, len(results))
        self.assertEqual("test1", results[0].asset_ref)

        region_constraint = Polygon(
            ((179, 10), (-179, 10), (-179, -10), (179, -10), (179, 10)))

        results = models.ExposureData.objects.contained_in(
            self.model.id,
            region_constraint)
        results = [result for result in results if result.taxonomy == "test"]
        self.assertEqual(1, len(list(results)))
        self.assertEqual("test2", results[0].asset_ref)
