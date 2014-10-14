# Copyright (c) 2014, GEM Foundation.
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

from nose.plugins.attrib import attr
from qa_tests import _utils as qa_utils
from qa_tests.hazard.event_based.spatial_correlation import _utils as sc_utils


class EBHazardSpatialCorrelCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

        job = self.run_hazard(cfg)
        hc = job.get_oqparam()

        site_1 = 'POINT(0.0 0.0)'
        site_2 = 'POINT(0.008993 0.0)'

        gmvs_site_1 = sc_utils.get_gmvs_for_location(site_1, job)
        gmvs_site_2 = sc_utils.get_gmvs_for_location(site_2, job)

        joint_prob_0_5 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 0.5, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )
        joint_prob_1_0 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 1.0, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )

        numpy.testing.assert_almost_equal(joint_prob_0_5, 0.99, decimal=1)
        numpy.testing.assert_almost_equal(joint_prob_1_0, 0.64, decimal=1)
