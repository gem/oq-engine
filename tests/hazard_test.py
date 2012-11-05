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

from openquake import kvs
from openquake import logs
from openquake.calculators.hazard import general as hazard_general
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
