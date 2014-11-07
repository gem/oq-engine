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

import unittest
import StringIO
import numpy
from numpy.testing import assert_almost_equal
from openquake.commonlib.riskmodels import get_vulnerability_functions
from openquake.commonlib import InvalidFile


class ParseVulnerabilityModelTestCase(unittest.TestCase):

    def test_different_levels_ok(self):
        # the same IMT can appear with different levels in different
        # vulnerability functions
        vuln_content = StringIO.StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGA">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="RC/A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30
         </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGA">0.004 0.008 0.037</IML>
            <discreteVulnerability vulnerabilityFunctionID="RC/B"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30
         </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>
""")
        vfs = get_vulnerability_functions(vuln_content)
        assert_almost_equal(vfs['PGA', 'A'].imls,
                            numpy.array([0.005, 0.007, 0.0098, 0.0137]))
        assert_almost_equal(vfs['PGA', 'B'].imls,
                            numpy.array([0.004, 0.008, 0.037]))

    def test_one_taxonomy_many_imts(self):
        # Should raise a ValueError if a vulnerabilityFunctionID is used for
        # multiple IMTs.
        # In this test input, we've defined two functions in separate sets
        # with the same ID and different IMTs.
        vuln_content = StringIO.StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGA">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30
         </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="MMI">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30
                </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>
""")
        with self.assertRaises(InvalidFile) as ar:
            get_vulnerability_functions(vuln_content)
        self.assertIn('Duplicated vulnerabilityFunctionID: A',
                      ar.exception.message)

    def test_lr_eq_0_cov_gt_0(self):
        # If a vulnerability function loss ratio is 0 and its corresponding CoV
        # is > 0, a ValueError should be raised
        vuln_content = StringIO.StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGV">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.00 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30
                </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>
""")
        with self.assertRaises(ValueError) as ar:
            get_vulnerability_functions(vuln_content)
        self.assertIn('It is not valid to define a loss ratio = 0.0 with a '
                      'corresponding coeff. of variation > 0.0',
                      ar.exception.message)
