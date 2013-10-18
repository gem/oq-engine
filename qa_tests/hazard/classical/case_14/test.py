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
import os
from nose.plugins.attrib import attr
from qa_tests._utils import BaseQATestCase, compare_hazard_curve_with_csv

CURRENTDIR = os.path.dirname(__file__)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226102
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase14TestCase(BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cfg = os.path.join(CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)
        hc = job.hazard_calculation

        compare_hazard_curve_with_csv(
            hc, ['AbrahamsonSilva2008'], 'PGA', None, None,
            os.path.join(CURRENTDIR, 'AS2008_expected_curves.dat'), ' ')

        compare_hazard_curve_with_csv(
            hc, ['CampbellBozorgnia2008'], 'PGA', None, None,
            os.path.join(CURRENTDIR, 'CB2008_expected_curves.dat'), ' ')
