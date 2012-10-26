# -*- coding: utf-8 -*-

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
Unit tests for hazard computations with the hazard engine.
Includes:

- hazard curves (with mean and quantile)
- hazard maps (only mean and quantile)
"""

import numpy
import os
import unittest

from openquake import engine
from openquake import kvs
from openquake import logs
from openquake import xml
from openquake.calculators.hazard import general as hazard_general
from openquake.engine import JobContext
from openquake.export import psha
from openquake.job import params as job_params
from openquake.kvs import tokens
from openquake.nrml.utils import nrml_schema_file

from tests.utils import helpers

LOG = logs.LOG

TEST_JOB_FILE = helpers.testdata_path('simplecase/config.gem')

NRML_SCHEMA_PATH = nrml_schema_file()

SIMPLE_FAULT_SRC_MODEL_LT = helpers.demo_file(
    'simple_fault_demo_hazard/source_model_logic_tree.xml')
SIMPLE_FAULT_GMPE_LT = helpers.demo_file(
    'simple_fault_demo_hazard/gmpe_logic_tree.xml')
SIMPLE_FAULT_BASE_PATH = os.path.abspath(
    helpers.demo_file('simple_fault_demo_hazard'))


def get_pattern(regexp):
    """Get all the values whose keys satisfy the given regexp.

    Return an empty list if there are no keys satisfying the given regxep.
    """

    values = []

    keys = kvs.get_client().keys(regexp)

    if keys:
        values = kvs.get_client().mget(keys)

    return values


class HazardEngineTestCase(unittest.TestCase):
    """The Hazard Engine is a JPype-based wrapper around OpenSHA-lite.
    Most data returned from the engine is via the KVS."""

    def setUp(self):
        self.generated_files = []
        self.kvs_client = kvs.get_client()

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError:
                pass


class IMLTestCase(unittest.TestCase):
    """
    Tests that every Intensity Measure Type
    declared in ``openquake.db.models.OqJobProfile.IMT_CHOICES``
    has a correct corresponding function
    in ``openquake.hazard.general.IML_SCALING`` mapping
    and is allowed to be the configuration parameter value
    for ``INTENSITY_MEASURE_TYPE``.
    """
    def test_scaling_definitions(self):
        from openquake.db.models import OqJobProfile
        from openquake.job.params import ENUM_MAP
        from openquake.calculators.hazard.general import IML_SCALING
        enum_map_reversed = dict((val, key) for (key, val) in ENUM_MAP.items())
        imt_config_names = [enum_map_reversed[imt]
                            for (imt, imt_verbose) in OqJobProfile.IMT_CHOICES
                            if imt in enum_map_reversed]
        self.assertEqual(set(IML_SCALING) - set(imt_config_names), set())
        self.assertEqual(set(imt_config_names), set(IML_SCALING))
        for imt in imt_config_names:
            self.assertTrue(callable(IML_SCALING[imt]))
            self.assertTrue(hasattr(self, 'test_imt_%s' % imt),
                            'please test imt %s' % imt)

    def _test_imt(self, imt, function):
        sample_imt = [1.2, 3.4, 5.6]
        double_array = hazard_general.get_iml_list(sample_imt, imt)
        actual_result = [val.value for val in double_array]
        expected_result = map(function, sample_imt)
        self.assertEqual(actual_result, expected_result)

    def test_imt_PGA(self):
        self._test_imt('PGA', numpy.log)

    def test_imt_SA(self):
        self._test_imt('SA', numpy.log)

    def test_imt_PGV(self):
        self._test_imt('PGV', numpy.log)

    def test_imt_PGD(self):
        self._test_imt('PGD', numpy.log)

    def test_imt_IA(self):
        self._test_imt('IA', numpy.log)

    def test_imt_RSD(self):
        self._test_imt('RSD', numpy.log)

    def test_imt_MMI(self):
        self._test_imt('MMI', lambda val: val)
