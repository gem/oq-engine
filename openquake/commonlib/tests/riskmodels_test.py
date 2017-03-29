# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import pickle
import unittest
import mock
import numpy
from numpy.testing import assert_almost_equal
from openquake.baselib.general import writetmp
from openquake.hazardlib import InvalidFile, nrml
from openquake.commonlib import nrml_examples, riskmodels
from openquake.qa_tests_data.scenario_damage import case_4b

EXAMPLES_DIR = os.path.dirname(nrml_examples.__file__)
FF_DIR = os.path.dirname(case_4b.__file__)


class ParseCompositeRiskModelTestCase(unittest.TestCase):

    def test_different_levels_ok(self):
        # the same IMT can appear with different levels in different
        # vulnerability functions
        vuln_content = writetmp(u"""\
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
        vfs = nrml.parse(vuln_content)
        assert_almost_equal(vfs['PGA', 'RC/A'].imls,
                            numpy.array([0.005, 0.007, 0.0098, 0.0137]))
        assert_almost_equal(vfs['PGA', 'RC/B'].imls,
                            numpy.array([0.004, 0.008, 0.037]))

    def test_one_taxonomy_many_imts(self):
        # Should raise a ValueError if a vulnerabilityFunctionID is used for
        # multiple IMTs.
        # In this test input, we've defined two functions in separate sets
        # with the same ID and different IMTs.
        vuln_content = writetmp(u"""\
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
            nrml.parse(vuln_content)
        self.assertIn('Duplicated vulnerabilityFunctionID: A',
                      str(ar.exception))

    def test_lr_eq_0_cov_gt_0(self):
        # If a vulnerability function loss ratio is 0 and its corresponding CoV
        # is > 0, a ValueError should be raised
        vuln_content = writetmp(u"""\
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
            nrml.parse(vuln_content)
        self.assertIn('It is not valid to define a loss ratio = 0.0 with a '
                      'corresponding coeff. of variation > 0.0',
                      str(ar.exception))

    def test_missing_minIML(self):
        vuln_content = writetmp(u"""\
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
            nrml.parse(vuln_content)
        self.assertIn("node IML: 'minIML', line 9", str(ar.exception))

    def test_missing_maxIML(self):
        vuln_content = writetmp(u"""\
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
            nrml.parse(vuln_content)
        self.assertIn("node IML: 'maxIML', line 9", str(ar.exception))


class ParseConsequenceModelTestCase(unittest.TestCase):
    wrong_csq_model_1 = writetmp(u"""<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
<consequenceModel id="example" assetCategory="buildings">

  <description>ln cf | tax3 | zcov</description>
  <limitStates>ds1 ds2 ds3 ds4</limitStates>

  <consequenceFunction id="tax1" dist="LN">
    <params ls="ds1" mean="0.10" stddev="0.00"/>
    <params ls="ds2" mean="0.30" stddev="0.00"/>
    <params ls="ds3" mean="0.60" stddev="0.00"/>
    <params ls="ds4" mean="0.90" stddev="0.00"/>
  </consequenceFunction>

</consequenceModel>
</nrml>
""")
    wrong_csq_model_2 = writetmp(u"""<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
<consequenceModel id="example" assetCategory="buildings"
lossCategory="contents">

  <description>ln cf | tax3 | zcov</description>
  <limitStates>ds1 ds2 ds3 ds4</limitStates>

  <consequenceFunction id="tax1" dist="LN">
    <params ls="ds1" mean="0.10" stddev="0.00"/>
    <params ls="ds2" mean="0.30" stddev="0.00"/>
    <params ls="ds3" mean="0.60" stddev="0.00"/>
  </consequenceFunction>

</consequenceModel>
</nrml>
""")
    wrong_csq_model_3 = writetmp(u"""<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
<consequenceModel id="example" assetCategory="buildings"
lossCategory="contents">

  <description>ln cf | tax3 | zcov</description>
  <limitStates>ds1 ds2 ds3 ds4</limitStates>

  <consequenceFunction id="tax1" dist="LN">
    <params ls="ds1" mean="0.10" stddev="0.00"/>
    <params ls="ds2" mean="0.30" stddev="0.00"/>
    <params ls="ds4" mean="0.90" stddev="0.00"/>
    <params ls="ds3" mean="0.60" stddev="0.00"/>
  </consequenceFunction>

</consequenceModel>
</nrml>
""")

    def test_ok(self):
        fname = os.path.join(EXAMPLES_DIR, 'consequence-model.xml')
        cmodel = nrml.parse(fname)
        self.assertEqual(
            repr(cmodel),
            "<ConsequenceModel structural ds1, ds2, ds3, ds4 tax1>")

        # test pickleability
        pickle.loads(pickle.dumps(cmodel))

    def test_wrong_loss_type_association(self):
        scm = os.path.join(FF_DIR, 'structural_consequence_model.xml')
        ccm = os.path.join(FF_DIR, 'contents_consequence_model.xml')
        # exchanging the associations on purpose
        oq = mock.Mock()
        oq.inputs = dict(structural_consequence=ccm, contents_consequence=scm)
        with self.assertRaises(ValueError) as ctx:
            riskmodels.get_risk_models(oq, 'consequence')
        self.assertIn('structural_consequence_model.xml": lossCategory is of '
                      'type "structural", expected "contents"',
                      str(ctx.exception))

    def test_wrong_riskmodel_association(self):
        cfm = os.path.join(FF_DIR, 'contents_fragility_model.xml')
        # passing a fragility model instead of a consequence model
        oq = mock.Mock()
        oq.inputs = dict(contents_consequence=cfm)
        with self.assertRaises(ValueError) as ctx:
            riskmodels.get_risk_models(oq, 'consequence')
        self.assertIn('is of kind FragilityModel, '
                      'expected ConsequenceModel', str(ctx.exception))

    def test_wrong_files(self):
        # missing lossCategory
        with self.assertRaises(KeyError) as ctx:
            nrml.parse(self.wrong_csq_model_1)
        self.assertIn("node consequenceModel: 'lossCategory', line 3",
                      str(ctx.exception))

        # missing loss state
        with self.assertRaises(ValueError) as ctx:
            nrml.parse(self.wrong_csq_model_2)
        self.assertIn("node consequenceFunction: Expected 4 limit"
                      " states, got 3, line 9", str(ctx.exception))

        # inverted loss states
        with self.assertRaises(ValueError) as ctx:
            nrml.parse(self.wrong_csq_model_3)
        self.assertIn("node params: Expected 'ds3', got 'ds4', line 12",
                      str(ctx.exception))
