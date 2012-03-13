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

from openquake.db.models import LossCurveData
from openquake.db.models import OqJob

from tests.utils import helpers


class ClassicalRiskQATestCase(unittest.TestCase):
    """Single site QA tests for the Classical Risk calculator."""

    @attr('qa')
    def test_classical_psha_based_risk(self):
        """Run the full hazard+risk job, serialize all results to the db,
        and verify them against expected values."""
        output_dir = helpers.demo_file(
            'classical_psha_based_risk/computed_output')

        expected_lc_poes = [
            0.03944,
            0.03943,
            0.03857,
            0.03548,
            0.03123,
            0.02708,
            0.02346,
            0.02039,
            0.01780,
            0.01565,
            0.01386,
            0.01118,
            0.00926,
            0.00776,
            0.00654,
            0.00555,
            0.00417,
            0.00338,
            0.00283,
            0.00231,
            0.00182,
            0.00114,
            0.00089,
            0.00082,
            0.00069,
            0.00039,
            0.00024,
            0.00013,
            0.00006,
            0.00002,
            0.00001,
        ]

        cls_risk_cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')
        ret_code = helpers.run_job(cls_risk_cfg, ['--output-type=xml'])
        self.assertEquals(0, ret_code)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        loss_curve = LossCurveData.objects.get(
            loss_curve__output__oq_job=job.id)

        self.assertTrue(numpy.allclose(expected_lc_poes, loss_curve.poes,
                                       atol=0.0009))

        # Now check that we output the expected XML files:
        expected_files = [
            'hazardcurve-0.xml',
            'hazardcurve-mean.xml',
            'losscurves-block-#%s-block#0.xml' % job.id,
            'losscurves-loss-block-#%s-block#0.xml' % job.id,
            'losses_at-0.01.xml',
            'losses_at-0.02.xml',
            'losses_at-0.05.xml'
        ]

        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(output_dir, f)))
