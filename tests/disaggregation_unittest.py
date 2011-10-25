# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import os
import tempfile
import unittest

from nose.plugins.attrib import attr

from openquake import java
from openquake import shapes
from openquake.hazard import disaggregation as disagg
from openquake.hazard.general import store_source_model, store_gmpe_map
from openquake.input.logictree import LogicTreeProcessor

from tests.utils import helpers

DISAGG_DEMO_CONFIG_FILE = helpers.demo_file('disaggregation/config.gem')


class DisaggregationFuncsTestCase(unittest.TestCase):
    """Test for disaggregation calculator helper functions."""

    def test_list_to_jdouble_array(self):
        """Test construction of a Double[] (Java array) from a list of floats.
        """
        test_input = [0.01, 0.02, 0.03, 0.04]

        # Make the (Java) Double[] array (the input is copied as a simple way
        # to avoid false positives).
        jdouble_a = disagg.list_to_jdouble_array(list(test_input))

        # It should be a jpype Double[] type:
        self.assertEqual('java.lang.Double[]', jdouble_a.__class__.__name__)

        # Now check that the len and values are correct:
        self.assertEqual(len(test_input), len(jdouble_a))
        self.assertEqual(test_input, [x.doubleValue() for x in jdouble_a])


class DisaggregationTaskTestCase(unittest.TestCase):
    """ """

    @attr('slow')
    def test_compute_disagg_matrix(self):
        """Test the core function of the main disaggregation task."""

        # for the given test input data, we expect the calculator to return
        # this gmv:
        expected_gmv = 0.22617014437661012

        the_job = helpers.job_from_file(DISAGG_DEMO_CONFIG_FILE)

        # We need to store the source model and gmpe model in the KVS for this
        # test.
        lt_proc = LogicTreeProcessor(
            the_job.params['BASE_PATH'],
            the_job.params['SOURCE_MODEL_LOGIC_TREE_FILE_PATH'],
            the_job.params['GMPE_LOGIC_TREE_FILE_PATH'])

        src_model_seed = int(the_job.params.get('SOURCE_MODEL_LT_RANDOM_SEED'))
        gmpe_seed = int(the_job.params.get('GMPE_LT_RANDOM_SEED'))

        store_source_model(the_job.job_id, src_model_seed, the_job.params,
                           lt_proc)
        store_gmpe_map(the_job.job_id, gmpe_seed, lt_proc)

        site = shapes.Site(0.0, 0.0)
        realization = 1
        poe = 0.1
        result_dir = tempfile.tempdir

        gmv, matrix_path = disagg.compute_disagg_matrix(
            the_job.job_id, site, realization, poe, result_dir)

        # Now test the following:
        # 1) The matrix file exists
        # 2) The matrix file has a size > 0
        # 3) Check that the returned GMV is what we expect
        self.assertTrue(os.path.exists(matrix_path))
        self.assertTrue(os.path.getsize(matrix_path) > 0)
        self.assertEqual(expected_gmv, gmv)
