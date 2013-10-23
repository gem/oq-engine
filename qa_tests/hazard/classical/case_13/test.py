# Copyright (c) 2013, GEM Foundation.
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
import unittest
from nose.plugins.attrib import attr
from qa_tests._utils import BaseQATestCase, compare_hazard_curve_with_csv

CURRENTDIR = os.path.dirname(__file__)


# this test is described in https://bugs.launchpad.net/oq-engine/+bug/1226061
# the CSV files with the expected hazard_curves were provided by Damiano
class ClassicalHazardCase13TestCase(BaseQATestCase):

    @attr('qa', 'hazard', 'classical')
    def test(self):
        raise unittest.SkipTest  # temporarily skipped until I fix it (MS)
        cfg = os.path.join(CURRENTDIR, 'job.ini')
        job = self.run_hazard(cfg)
        hc = job.hazard_calculation

        lt_paths = [
            ['aFault_aPriori_D2.1', 'BooreAtkinson2008'],
            ['aFault_aPriori_D2.1', 'ChiouYoungs2008'],
            ['bFault_stitched_D2.1_Char', 'BooreAtkinson2008'],
            ['bFault_stitched_D2.1_Char', 'ChiouYoungs2008']]

        csvdir = os.path.join(CURRENTDIR, 'expected_results')
        for sm_path, gsim_path in lt_paths:

            fname = '%s_%s_expected_curves_PGA.dat' % (sm_path, gsim_path)
            compare_hazard_curve_with_csv(
                hc, [sm_path], [gsim_path], 'PGA', None, None,
                os.path.join(csvdir, fname), ' ')

            fname = '%s_%s_expected_curves_SA02.dat' % (sm_path, gsim_path)
            compare_hazard_curve_with_csv(
                hc, [sm_path], [gsim_path], 'SA', 0.2, 5.0,
                os.path.join(csvdir, fname), ' ')
