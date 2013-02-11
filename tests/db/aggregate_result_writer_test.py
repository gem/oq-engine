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
Test bulk insert of aggregate results (mean curves, quantile curves,
hazard maps, etc.)
"""

from __future__ import absolute_import

import random
import unittest
from openquake.engine.db import models as oq_models
from openquake.engine.db.aggregate_result_writer import (
    MeanCurveWriter, QuantileCurveWriter)

from ..utils import helpers


class AggregateResultWriterFactoryTestCase(unittest.TestCase):
    """
    Test the manager to create aggregate result writer
    """

    def setUp(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username="test_user")

    def test_create_mean_output(self):
        writer = MeanCurveWriter(self.job, imt="PGA")
        curve, output = writer.create_aggregate_result()
        self.assertEqual(1,
                         oq_models.Output.objects.filter(pk=output.id).count())
        self.assertEqual(
            1,
            oq_models.HazardCurve.objects.filter(pk=curve.id).count())
        self.assertEqual("hazard_curve", output.output_type)
        self.assertFalse(curve.lt_realization)
        self.assertEqual("mean", curve.statistics)
        self.assertEqual("PGA", curve.imt)
        self.assertFalse(curve.sa_damping)
        self.assertFalse(curve.sa_period)
        self.assertFalse(curve.quantile)

        curve, output = writer.create_aggregate_result()
        self.assertEqual(1,
                         oq_models.Output.objects.filter(pk=output.id).count())
        self.assertEqual(
            1,
            oq_models.HazardCurve.objects.filter(pk=curve.id).count())
        self.assertEqual(curve.output, output)

    def test_create_quantile_output(self):
        period = 0.025

        writer = QuantileCurveWriter(
            self.job, quantile=0.5, imt="SA(%s)" % period)
        curve, output = writer.create_aggregate_result()
        self.assertEqual(1,
                         oq_models.Output.objects.filter(pk=output.id).count())
        self.assertEqual(
            1,
            oq_models.HazardCurve.objects.filter(pk=curve.id).count())
        self.assertEqual("hazard_curve", output.output_type)
        self.assertFalse(curve.lt_realization)
        self.assertEqual("quantile", curve.statistics)
        self.assertEqual("SA", curve.imt)
        self.assertEqual(oq_models.DEFAULT_SA_DAMPING, curve.sa_damping)
        self.assertEqual(period, curve.sa_period)
        self.assertEqual(curve.output, output)


class AggregateResultWriterTestCase(unittest.TestCase):
    """
    Test the manager to create aggregate result
    """
    def setUp(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username="test_user")

        self.mean_curve_writer = MeanCurveWriter(self.job, imt="PGA")
        self.mean_curve, self.mean_output = (
            self.mean_curve_writer.create_aggregate_result())
        self.quantile_curve_writer = QuantileCurveWriter(
            self.job, quantile=0.5, imt="PGA")
        self.quantile_curve, self.quantile_output = (
            self.quantile_curve_writer.create_aggregate_result())

    def test_create_mean_curves(self):
        a_location = helpers.random_location_generator()
        poes = [random.random()]

        with self.mean_curve_writer as writer:
            writer.add_data(
                location=a_location.wkb,
                poes=poes)
            writer.add_data(
                location=a_location.wkb,
                poes=poes)

        self.assertEqual(2,
                         self.mean_curve.hazardcurvedata_set.count())
        curvedata = self.mean_curve.hazardcurvedata_set.all()[0]
        self.assertEqual(
            1,
            oq_models.HazardCurveData.objects.filter(pk=curvedata.id).count())

    def test_create_quantile_curves(self):
        a_location = helpers.random_location_generator()
        poes = [random.random()]

        with self.quantile_curve_writer as writer:
            writer.add_data(
                location=a_location.wkb,
                poes=poes)
        self.assertEqual(1,
                         self.quantile_curve.hazardcurvedata_set.count())
        curvedata = self.quantile_curve.hazardcurvedata_set.all()[0]

        self.assertEqual(
            1,
            oq_models.HazardCurveData.objects.filter(pk=curvedata.id).count())
