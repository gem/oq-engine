# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904

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
from openquake.db import models as openquake
from tests.utils import helpers


class TestCaseWithAJob(unittest.TestCase):
    """
    Abstract test case class to just setup a job
    """
    def setUp(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username="test_user")


class OutputManagerTestCase(TestCaseWithAJob):
    """
    Test the OutputManager
    """

    def setUp(self):
        super(OutputManagerTestCase, self).setUp()
        self.manager = openquake.Output.objects

    def test_create_output(self):
        output = self.manager.create_output(self.job,
                                            "fake output")
        self.assertEqual(1, self.manager.filter(pk=output.id).count())

        output = self.manager.create_output(self.job,
                                            "another fake output",
                                            "hazard_map")
        self.assertEqual(1, self.manager.filter(pk=output.id).count())


class HazardCurveManagerTestCase(TestCaseWithAJob):
    """
    Test the manager for HazardCurve
    """
    def setUp(self):
        super(HazardCurveManagerTestCase, self).setUp()
        self.manager = openquake.HazardCurve.objects
        self.output = openquake.Output.objects.create_output(self.job,
                                                             "fake output")

    def test_create_aggregate_curve(self):
        curve = self.manager.create_aggregate_curve(self.output, "PGA")
        self.assertEqual(1, self.manager.filter(pk=curve.id).count())

        curve = self.manager.create_aggregate_curve(self.output,
                                            imt="SA(0.025)",
                                            statistics="mean")
        self.assertEqual(1, self.manager.filter(pk=curve.id).count())

        self.assertRaises(AttributeError,
                          self.manager.create_aggregate_curve,
                          self.output, "SA(")

        self.assertRaises(ValueError,
                          self.manager.create_aggregate_curve,
                          self.output, "SA(10)", quantile=0.5)


class AggregateResultWriterTestCase(TestCaseWithAJob):
    """
    Test the manager to create aggregate result writer
    """
    def setUp(self):
        super(AggregateResultWriterTestCase, self).setUp()
        self.manager = openquake.AggregateResultWriter(self.job, "PGA")

    def test_create_mean_curve(self):
        a_location = (random.random(), random.random())
        poes = [random.random()]

        curvedata, curve, output = self.manager.create_mean_curve(
            location=a_location,
            poes=poes
            )
        self.assertEqual(1,
                         openquake.Output.objects.filter(pk=output.id).count())
        self.assertEqual(
            1,
            openquake.HazardCurve.objects.filter(pk=curve.id).count())
        self.assertEqual(
            1,
            openquake.HazardCurveData.objects.filter(pk=curvedata.id).count())

    def test_create_quantile_curve(self):
        a_location = (random.random(), random.random())
        poes = [random.random()]

        curvedata, curve, output = self.manager.create_quantile_curve(
            location=a_location,
            quantile=random.random(),
            poes=poes
            )
        self.assertEqual(1,
                         openquake.Output.objects.filter(pk=output.id).count())
        self.assertEqual(
            1,
            openquake.HazardCurve.objects.filter(pk=curve.id).count())
        self.assertEqual(
            1,
            openquake.HazardCurveData.objects.filter(pk=curvedata.id).count())


class HazardCurveDataManagerTestCase(TestCaseWithAJob):
    """
    Test the manager of HazardCurveData objects
    """
    def setUp(self):
        super(HazardCurveDataManagerTestCase, self).setUp()
        self.manager = openquake.HazardCurveData.objects
        self.manager.current_job = self.job

        # Setup some data
        # Requires a working version of Django models
        output = openquake.Output.objects.create_output(self.job,
                                                        "fake output")
        realization = openquake.LtRealization.objects.all()[0]
        curve = openquake.HazardCurve.objects.create(
            output=output,
            lt_realization=realization,
            investigation_time=10,
            imt="PGA", imls=[1, 2, 3])

        self.a_location = (random.random(), random.random())
        openquake.HazardCurveData.objects.create(
            hazard_curve=curve,
            location="POINT(%s %s)" % self.a_location,
            poes=[random.random()])

        self.a_bigger_location = (1 + random.random(), random.random())
        openquake.HazardCurveData.objects.create(
            hazard_curve=curve,
            location="POINT(%s %s)" % self.a_bigger_location,
            poes=[random.random()])

    def test_individual_curves(self):
        """
        Test getting individual curves
        """
        # use a fake imt
        self.assertEqual(0,
                         len(self.manager.individual_curves("fake imt")))

        self.assertEqual(2,
                         len(self.manager.individual_curves("PGA")))

        self.assertEqual(2,
                         len(self.manager.individual_curves()))

    def test_individual_curves_nr(self):
        """
        Test counting the individual curves
        """
        # use a fake imt
        self.assertEqual(0,
                         self.manager.individual_curves_nr("fake imt"))

        self.assertEqual(2,
                         self.manager.individual_curves_nr())

    def test_individual_curves_ordered(self):
        """
        Test getting individual curves ordered by location
        """
        curves = self.manager.individual_curves_ordered()

        self.assertEqual(2, len(curves))
        self.assertTrue(curves[0].location < curves[1].location)

    def individual_curves_chunks(self):
        """
        Test getting individual curves in chunks
        """
        block_size = 1
        chunks = self.manager.individual_curves_chunks(block_size=block_size)

        chunk_getter = chunks.next()
        chunk = chunk_getter('location')
        self.assertEqual(len(chunk), block_size)
        self.assertAlmostEqual(chunk[0], self.a_location)
