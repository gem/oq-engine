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

import os
from nose.plugins.attrib import attr
from qa_tests._utils import BaseQATestCase, compare_hazard_curve_with_csv

CURRENTDIR = os.path.dirname(__file__)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226061
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase15TestCase(BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        cfg = os.path.join(CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)

        lt_paths = [
            [['SM1'], ['BA2008', 'C2003']],
            [['SM1'], ['BA2008', 'T2002']],
            [['SM1'], ['CB2008', 'C2003']],
            [['SM1'], ['CB2008', 'T2002']],
            [['SM2', 'a3pt2b0pt8'], ['BA2008']],
            [['SM2', 'a3pt2b0pt8'], ['CB2008']],
            [['SM2', 'a3b1'], ['BA2008']],
            [['SM2', 'a3b1'], ['CB2008']],
        ]

        csvdir = os.path.join(CURRENTDIR, 'expected_results')
        j = '_'.join
        for sm_path, gsim_path in lt_paths:

            fname = 'PGA/hazard_curve-smltp_%s-gsimltp_%s.csv' % (
                j(sm_path), j(gsim_path))
            compare_hazard_curve_with_csv(
                job, sm_path, gsim_path, 'PGA', None, None,
                os.path.join(csvdir, fname), ' ', rtol=1e-7)

            fname = 'SA-0.1/hazard_curve-smltp_%s-gsimltp_%s.csv' % (
                j(sm_path), j(gsim_path))
            compare_hazard_curve_with_csv(
                job, sm_path, gsim_path, 'SA', 0.1, 5.0,
                os.path.join(csvdir, fname), ' ', rtol=1e-7)
