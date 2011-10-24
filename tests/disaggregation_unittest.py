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


import unittest

from openquake import java
from openquake.hazard import disaggregation as disagg

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

    @helpers.skipit
    def test_compute_disagg_matrix(self):
        """Test the core function of the main disaggregation task."""

        the_job = helpers.job_from_file(DISAGG_DEMO_CONFIG_FILE)
        da_calc = disagg.compute_disagg_matrix(
            the_job.job_id, None, None, None)
        print da_calc
        self.assertTrue(False)
