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

import numpy
import os
import unittest

from nose.plugins.attrib import attr
from openquake import engine2
from openquake.db import models
from qa_tests import _utils as qa_util
from tests.utils import helpers


class ClassicalHazardCase1TestCase(unittest.TestCase):

    @attr('qa')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = qa_util.run_hazard(cfg)

        expected_curve_poes = [0.4570, 0.0587, 0.0069]

        # One curve only:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=4)
