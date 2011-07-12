# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from db.alchemy.db_utils import get_uiapi_writer_session
from openquake.output.hazard import *
from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin
from openquake.shapes import Site
from openquake.utils import round_float

from db_tests import helpers

# See data in output_hazard_unittest.py
HAZARD_CURVE_DATA = [
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


class HazardCurveDBReadTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Test the code to read the hazard curve from DB.
    """
    def setUp(self):
        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        hcw = HazardCurveDBWriter(session, output_path, self.job.id)
        hcw.serialize(HAZARD_CURVE_DATA)

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_read_curve(self):
        """Verify _get_kvs_curve."""
        mixin = ClassicalPSHABasedMixin()
        mixin.params = {
            "OPENQUAKE_JOB_ID": str(self.job.id),
        }

        curve1 = mixin._get_db_curve(Site(-122.2, 37.5))
        self.assertEquals(list(curve1.abscissae),
                          [0.005, 0.007, 0.0098, 0.0137])
        self.assertEquals(list(curve1.ordinates), [0.354, 0.114, 0.023, 0.002])

        curve2 = mixin._get_db_curve(Site(-122.1, 37.5))
        self.assertEquals(list(curve2.abscissae),
                          [0.005, 0.007, 0.0098, 0.0137])
        self.assertEquals(list(curve2.ordinates), [0.454, 0.214, 0.123, 0.102])
