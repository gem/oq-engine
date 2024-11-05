# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
import toml
import numpy
import pandas
from numpy.testing import assert_almost_equal
from openquake.baselib.general import gettemp
from openquake.hazardlib import InvalidFile, nrml
from openquake.risklib import riskmodels
from openquake.qa_tests_data.scenario_damage import case_4b

FF_DIR = os.path.dirname(case_4b.__file__)


class ParseCompositeRiskModelTestCase(unittest.TestCase):

    def test_different_levels_ok(self):
        # the same IMT can appear with different levels in different
        # vulnerability functions
        vuln_content = gettemp(u"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="occupants">
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
                                  lossCategory="occupants">
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
        vfs = nrml.to_python(vuln_content)
        assert_almost_equal(vfs['PGA', 'RC/A'].imls,
                            numpy.array([0.005, 0.007, 0.0098, 0.0137]))
        assert_almost_equal(vfs['PGA', 'RC/B'].imls,
                            numpy.array([0.004, 0.008, 0.037]))

    def test_one_taxonomy_many_imts(self):
        # Should raise a ValueError if a vulnerabilityFunctionID is used for
        # multiple IMTs.
        # In this test input, we've defined two functions in separate sets
        # with the same ID and different IMTs.
        vuln_content = gettemp(u"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="occupants">
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
                                  lossCategory="occupants">
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
            nrml.to_python(vuln_content)
        self.assertIn('Duplicated vulnerabilityFunctionID: A',
                      str(ar.exception))

    def test_lr_eq_0_cov_gt_0(self):
        # If a vulnerability function loss ratio is 0 and its corresponding CoV
        # is > 0, a ValueError should be raised
        vuln_content = gettemp(u"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="occupants">
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
            nrml.to_python(vuln_content)
        self.assertIn('It is not valid to define a mean loss ratio = 0 '
                      'with a corresponding coefficient of variation > 0',
                      str(ar.exception))

    def test_missing_minIML(self):
        vuln_content = gettemp(u"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
     <fragilityModel format="continuous">
        <description>Fragility for test</description>
        <limitStates>LS1 LS2</limitStates>
        <ffs type="lognormal">
            <taxonomy>RC</taxonomy>
            <IML IMT="PGA" maxIML="9.9" imlUnit="g"/>
            <ffc ls="LS1">
                <params mean="0.2" stddev="0.05" />
            </ffc>
            <ffc ls="LS2">
                <params mean="0.35" stddev="0.10" />
            </ffc>
        </ffs>
    </fragilityModel>
</nrml>""")
        with self.assertRaises(KeyError) as ar:
            nrml.to_python(vuln_content)
        self.assertIn("node IML: 'minIML', line 9", str(ar.exception))

    def test_missing_maxIML(self):
        vuln_content = gettemp(u"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
     <fragilityModel format="continuous">
        <description>Fragility for test</description>
        <limitStates>LS1 LS2</limitStates>
        <ffs type="lognormal">
            <taxonomy>RC</taxonomy>
            <IML IMT="PGA" minIML="9.9" imlUnit="g"/>
            <ffc ls="LS1">
                <params mean="0.2" stddev="0.05" />
            </ffc>
            <ffc ls="LS2">
                <params mean="0.35" stddev="0.10" />
            </ffc>
        </ffs>
    </fragilityModel>
</nrml>""")
        with self.assertRaises(KeyError) as ar:
            nrml.to_python(vuln_content)
        self.assertIn("node IML: 'maxIML', line 9", str(ar.exception))


class RiskComputerTestCase(unittest.TestCase):
    def test1(self):
        dic = {'asset_df': {'area': [1.0],
                            'id': [b'a2'],
                            'lat': [38.17],
                            'lon': [15.56],
                            'site_id': [0],
                            'taxonomy': [1],
                            'value-number': [2000.0],
                            'value-structural': [2000.0]},
               'calculation_mode': 'event_based_risk',
               'loss_types': ['structural'],
               'minimum_asset_loss': {'structural': 0},
               'risk_functions': {
                   'RC#structural':
                   {"openquake.risklib.scientific.VulnerabilityFunction":
                    {"id": "RC",
                     "peril": 'earthquake',
                     "loss_type": "structural",
                     "imt": "PGA",
                     "imls": [0.1, 0.2, 0.3, 0.5, 0.7],
                     "mean_loss_ratios": [0.0035, 0.07, 0.14, 0.28, 0.56],
                     "covs": [0.0, 0.0, 0.0, 0.0, 0.0],
                     "distribution_name": "LN"}}},
               'wdic': {'RC#structural': 1}}
        gmfs = {'eid': [0, 1],
                'sid': [0, 0],
                'gmv_0': [.23, .31]}
        rc = riskmodels.get_riskcomputer(dic, alias={'PGA': 'gmv_0'})
        print(toml.dumps(dic))
        for k, v in rc.todict().items():
            self.assertEqual(dic[k], v)
        out = rc.output(pandas.DataFrame(gmfs))
        print(out)

    def test2(self):
        alias = {'PGA': 'gmv_0',
                 'SA(0.2)': 'gmv_1',
                 'SA(0.5)': 'gmv_2',
                 'SA(0.8)': 'gmv_3',
                 'SA(1.0)': 'gmv_4'}
        dic = {'asset_df': {'area': [10.0, 1.0],
                            'id': [b'a0', b'a3'],
                            'lat': [29.1098, 27.9015],
                            'lon': [81.2985, 85.7477],
                            'policy': [2, 1],
                            'site_id': [0, 2],
                            'taxonomy': [1, 1],
                            'value-nonstructural': [1500.0, 2500.0],
                            'value-number': [3.0, 10.0],
                            'value-structural': [3000.0, 5000.0]},
               'calculation_mode': 'event_based_risk',
               'loss_types': ['nonstructural', 'structural'],
               'risk_functions': {
                   'RM#nonstructural': {
                       'openquake.risklib.scientific.VulnerabilityFunction': {
                           'covs': [0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
                           'distribution_name': 'LN',
                           'id': 'RM',
                           'imls': [0.1, 0.2, 0.4, 0.7, 1.0],
                           'imt': 'SA(1.0)',
                           'mean_loss_ratios': [0.1, 0.2, 0.35, 0.6, 0.9]}},
                   'RM#structural': {
                       'openquake.risklib.scientific.VulnerabilityFunction': {
                           'covs': [0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
                           'distribution_name': 'LN',
                           'id': 'RM',
                           'imls': [0.02, 0.3, 0.5, 0.9, 1.2],
                           'imt': 'PGA',
                           'mean_loss_ratios': [0.05, 0.1, 0.2, 0.4, 0.8]}}},
               'wdic': {'RM#nonstructural': 1, 'RM#structural': 1}}

        gmfs = {'eid': [0, 2],
                'sid': [0, 0],
                'gmv_0': [.23, .31],
                'gmv_1': [.23, .41],
                'gmv_2': [.23, .51],
                'gmv_3': [.23, .32],
                'gmv_4': [.23, .21]}
        rc = riskmodels.get_riskcomputer(dic, alias)
        print(toml.dumps(dic))
        out = rc.output(pandas.DataFrame(gmfs))
        print(out)

    def test3(self):
        # TODO: a case with nontrivial wdic, for instance
        # 'wdic': {'Wood/Com#contents': 1.0,
        #          'Wood1#structural': 0.6,
        #          'Wood2#structural': 0.4}
        # NB: for the same loss type the weights must sum up to 1
        pass

    def test4(self):
        # TODO: a case with secondary losses, for instance
        # seclosses = [partial(total_losses, kind=oq.total_losses)]
        # seclosses = [partial(insurance_losses, policy_df=self.policy_df)]
        pass
