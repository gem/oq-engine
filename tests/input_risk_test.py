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

from openquake.db import models
from openquake.input.fragility import FragilityDBWriter
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
          'endBranchLabel': '1'}),
        (Site(-122.1, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.454, 0.214, 0.123, 0.102],
          'IMT': 'PGA',
          'endBranchLabel': '1'}),
    ]


def MEAN_CURVE_DATA():
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
    ]


def QUANTILE_CURVE_DATA():
    return [
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
        expected_lss = ["slight", "moderate", "extensive", "complete"]
        self.assertEqual(expected_lss, model.lss)
        self.assertIs(self.input, model.input)
        self.assertIs(None, model.no_damage_limit)

        ffcs = model.ffc_set.all().order_by("taxonomy", "lsi")
        ffds = model.ffd_set.all()
        self.assertEqual(8, ffcs.count())
        self.assertEqual(0, ffds.count())

        self.assertEqual(expected_lss * 2, [ff.ls for ff in ffcs])

        self.assertIs(None, ffcs[0].ftype)
        self.assertEqual("RC/DMRF-D/HR", ffcs[0].taxonomy)
        self.assertEqual("slight", ffcs[0].ls)
        self.assertEqual(11.18, ffcs[0].mean)
        self.assertEqual(8.28, ffcs[0].stddev)

        self.assertIs(None, ffcs[3].ftype)
        self.assertEqual("RC/DMRF-D/HR", ffcs[3].taxonomy)
        self.assertEqual("complete", ffcs[3].ls)
        self.assertEqual(108.8, ffcs[3].mean)
        self.assertEqual(123.6, ffcs[3].stddev)

        self.assertEqual("lognormal", ffcs[5].ftype)
        self.assertEqual("RC/DMRF-D/LR", ffcs[5].taxonomy)
        self.assertEqual("moderate", ffcs[5].ls)
        self.assertEqual(27.98, ffcs[5].mean)
        self.assertEqual(20.677, ffcs[5].stddev)

        self.assertEqual("lognormal", ffcs[6].ftype)
        self.assertEqual("RC/DMRF-D/LR", ffcs[6].taxonomy)
        self.assertEqual("extensive", ffcs[6].ls)
        self.assertEqual(48.05, ffcs[6].mean)
        self.assertEqual(42.49, ffcs[6].stddev)


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
        expected_lss = ["minor", "moderate", "severe", "collapse"]
        self.assertEqual(expected_lss, model.lss)
        self.assertIs(self.input, model.input)
        self.assertEqual(0.2, model.no_damage_limit)

        ffcs = model.ffc_set.all()
        ffds = model.ffd_set.all().order_by("taxonomy", "lsi")
        self.assertEqual(0, ffcs.count())
        self.assertEqual(8, ffds.count())

        self.assertEqual(expected_lss * 2, [ff.ls for ff in ffds])

        self.assertEqual("RC/DMRF-D/HR", ffds[0].taxonomy)
        self.assertEqual("minor", ffds[0].ls)
        self.assertEqual([0.0, 0.09, 0.56, 0.92, 0.99], ffds[0].poes)

        self.assertEqual("RC/DMRF-D/HR", ffds[3].taxonomy)
        self.assertEqual("collapse", ffds[3].ls)
        self.assertEqual([0.0, 0.0, 0.0, 0.04, 0.64], ffds[3].poes)

        self.assertEqual("RC/DMRF-D/LR", ffds[5].taxonomy)
        self.assertEqual("moderate", ffds[5].ls)
        self.assertEqual([0.0, 0.0, 0.04, 0.78, 0.96], ffds[5].poes)

        self.assertEqual("RC/DMRF-D/LR", ffds[6].taxonomy)
        self.assertEqual("severe", ffds[6].ls)
        self.assertEqual([0.0, 0.0, 0.0, 0.29, 0.88], ffds[6].poes)
