# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import io
import os
import sys
import shutil
import unittest
import tempfile
import numpy as np
import pandas
from openquake.baselib import general, InvalidFile
from openquake.commonlib import readinput
from openquake.risklib import reinsurance

aac = np.testing.assert_allclose


def _df(string, sep=',', index_col=None):
    # build a DataFrame from a string
    return pandas.read_csv(io.StringIO(string), sep=sep, index_col=index_col,
                           keep_default_na=False)


def assert_ok(got, exp):
    if len(got.columns) != len(exp.columns):
        raise ValueError('Different columns %s != %s' %
                         (got.columns, exp.columns))
    assert list(got.columns) == list(exp.columns)
    for col in got.columns:
        try:
            aac(got[col], exp[col], err_msg=col)
        except ValueError:
            sys.exit(f'Wrong column {col} in {got}')


def by_policy_event(agglosses_df, policy_df, treaty_df):
    #returns (risk_by_policy_df, risk_by_event_df)
    dfs = []
    for _, policy in policy_df.iterrows():
        df = reinsurance.by_policy(agglosses_df, dict(policy), treaty_df)
        dfs.append(df)
    rbp = pandas.concat(dfs)
    rbe = reinsurance.by_event(rbp, treaty_df)
    return rbp, rbe


policy_idx = {'?': 0, 'VA_region_1': 1, 'VA_region_2': 2, 'rur_Ant_1': 3}

# NB: agg_id starts from 0, policy_id from 1
risk_by_event = _df('''\
event_id,agg_id,loss
25,     2,      9159.046
27,     1,      3141.0974
28,     1,      3136.3154
26,     1,      2859.9182
29,     1,      2603.0217
23,     1,      1730.9891
41,     0,      1178.0742
41,     1,      1178.0742
40,     0,      1170.1654
40,     1,      1170.1654
21,     1,      1157.2078
33,     0,      1117.877
13,     0,      764.2781
13,     1,      764.2781
5,      1,      761.1264
5,      0,      761.1264
''')

CSV_NP = '''\
Policy,Limit,Deductible,WXLR_metro,WXLR_rural,CatXL_reg
VA_region_1,8000,100,0,0,1
VA_region_2,4000,200,1,1,1
rur_Ant_1,  9000,500,1,1,0
'''

XML_NP = '''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
      xmlns:gml="http://www.opengis.net/gml">
  <reinsuranceModel>
    <description>reinsurance model</description>
    <fieldMap>
      <field oq="policy" input="Policy" />
      <field oq="deductible" input="Deductible" />
      <field oq="liability" input="Limit" />
      <field input="WXLR_metro" type="wxlr" deductible="500" limit="3500" />
      <field input="WXLR_rural" type="wxlr" deductible="200" limit="5000" />
      <field input="CatXL_reg" type="catxl" deductible="50" limit="2500" />
    </fieldMap>
    <policies>{}</policies>
  </reinsuranceModel>
</nrml>
'''

XML_PR = '''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
      xmlns:gml="http://www.opengis.net/gml">
  <reinsuranceModel>
    <description>reinsurance model</description>
    <fieldMap>
      <field oq="prop1" input="qshared" />
      <field oq="prop2" input="surplus" />
    </fieldMap>
    <policies>{}</policies>
  </reinsuranceModel>
</nrml>
'''


class ProportionalTestCase(unittest.TestCase):
    def test_single_portfolio(self):
        # two proportional treaties with with no overspill
        treaty_df = _df('''\
id,type,deductible,limit,code
prop1,prop,      0,     5000,A
prop2,prop,      0,     8000,B
''')
        bypolicy = _df('''\
event_id,policy_id,retention,claim,prop1,prop2,policy_grp
1,       1,        2400, 12000,6000.0,3600.0,AB
1,       2,        1500, 5000, 2000.0,1500.0,AB
1,       3,         600, 3000, 1500.0, 900.0,AB
1,       4,        1800, 6000, 2400.0,1800.0,AB''')
        byevent = reinsurance.by_event(bypolicy, treaty_df)
        assert_ok(byevent, _df('''\
event_id,retention,claim,prop1,prop2,over_A
       1,13200.0,26000,5000.0,7800.0,6900'''))

    def test_two_portfolios(self):
        # the first treaty applies to the first two policies,
        # the second to the last two policies
        treaty_df = _df('''\
id,type,deductible,limit,code
prop1,prop,      0,    5000,A
prop2,prop,      0,    8000,B
''')
        pol_df = _df('''\
policy,liability,deductible,prop1,prop2,policy_grp
1,     99000,        0,     .5,   0    ,A.
2,     99000,        0,     .4,   0    ,A.
3,     99000,        0,     0,   .6    ,.B
4,     99000,        0,     0,   .6    ,.B
''')
        risk_by_event = _df('''\
event_id,agg_id,loss
1,     0,      12000
1,     1,      5000
1,     2,      3000
1,     3,      6000
''')
        expected = _df('''\
event_id,retention,claim,prop1,prop2,over_A
       1,15600.0  ,26000,5000.0,5400.0,3000.0
''')
        bypolicy, byevent = by_policy_event(
            risk_by_event, pol_df, treaty_df)
        assert_ok(byevent, expected)


class ReinsuranceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(XML_NP.format(csvfname))
        cls.policy_df, treaty_df, fmap = reinsurance.parse(
            xmlfname, policy_idx)
        assert len(cls.policy_df) == 3
        assert len(treaty_df) == 3
        assert fmap == {'deductible': 'Deductible',
                        'liability': 'Limit',
                        'policy': 'Policy'}
        cls.treaty_df = treaty_df

    def test_policy1(self):
        # VA_region_1, CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,retention,claim,WXLR_metro,WXLR_rural
41,1,1078.0742,1078.0742,0.0,0.0
40,1,1070.1654,1070.1654,0.0,0.0
33,1,1017.8770,1017.8770,0.0,0.0
13,1, 664.2781, 664.2781,0.0,0.0
 5,1, 661.1264, 661.1264,0.0,0.0''')
        pol = dict(self.policy_df.loc[0])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        del out['policy_grp']
        assert_ok(out, expected)

    def test_policy2(self):
        # VA_region_2
        # WXLR_metro(500, 3500) + WXLR_rural(200, 5000) + CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,retention,claim,WXLR_metro,WXLR_rural
0,27,2 ,200,2941.0974,2441.0974,300.0
1,28,2 ,200,2936.3154,2436.3154,300.0
2,26,2 ,200,2659.9182,2159.9182,300.0
3,29,2 ,200,2403.0217,1903.0217,300.0
4,23,2 ,200,1530.9891,1030.9891,300.0
5,41,2 ,200, 978.0742, 478.0742,300.0
6,40,2 ,200, 970.1654, 470.1654,300.0
7,21,2 ,200, 957.2078, 457.2078,300.0
8,13,2 ,200, 564.2781,  64.2781,300.0
9, 5,2 ,200, 561.1264,  61.1264,300.0''')
        pol = dict(self.policy_df.loc[1])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        del out['policy_grp']
        assert_ok(out, expected)

    def test_policy3(self):
        # rur_Ant_1, WXLR_metro(500, 3500) + WXLR_rural(200, 5000)
        expected = _df('''\
event_id,policy_id,retention,claim,WXLR_metro,WXLR_rural
25,      3,        700,8500, 3000,4800''')
        pol = dict(self.policy_df.loc[2])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        del out['policy_grp']
        assert_ok(out, expected)

    def test_by_cat_no_apply(self):
        expected = _df('''\
event_id,retention,claim,WXLR_metro,WXLR_rural,CatXL_reg
25,      700.0,   8500.0,  3000.0,  4800.0,   0.0''', index_col='event_id')
        bypolicy, byevent = by_policy_event(
            risk_by_event, self.policy_df, self.treaty_df)
        # the catxl does not apply on event 25
        byevent = byevent[byevent.event_id == 25].set_index('event_id')
        assert_ok(byevent, expected)

    def test_max_cession(self):
        treaty_df = _df('''\
id,type,deductible,limit,code
prop1,prop,      0,    5000,A
nonprop1,wxlr, 200,    4000,B
nonprop2,catxl,500,   10000,C
''')
        pol_df = _df('''\
policy,liability,deductible,prop1,nonprop1,nonprop2
1,     99000,        0,     .5,   1,   1
2,     99000,        0,     .4,   1,   1
3,     99000,        0,     .6,   1,   1
''')
        risk_by_event = _df('''\
event_id,agg_id,loss
1,     0,      12000
1,     1,      5000
1,     2,      3000
''')
        expected = _df('''\
event_id,claim,retention,prop1,nonprop1,overspill1,nonprop2
       1,20000,    500.0,5000.0, 7600.0,    4800.0,6900.0''')
        bypolicy, byevent = by_policy_event(
            risk_by_event, pol_df, treaty_df)

    def test_many_levels(self):
        treaty_df = _df('''\
id,type,deductible,limit,code
prop1,prop,   0,  90000,A
prop2,prop,   0,  80000,B
wxl1,wxlr,  100,    500,C
wxl2,wxlr,  150,    400,D
cat1,catxl, 200,   4000,E
cat2,catxl, 500,  10000,F
cat3,catxl, 200,   4000,G
cat4,catxl, 500,  10000,H
cat5,catxl,1000,  50000,I
''')
        pol_df = _df('''\
policy,liability,deductible,prop1,prop2,wxl1,wxl2,cat1,cat2,cat3,cat4,cat5
1,     99000,        0,     .5,     .1,  0,   1,   1,   0,   0,   1,   1
2,     99000,        0,     .4,     .2,  0,   1,   1,   0,   0,   1,   1
3,     99000,        0,     .6,      0,  1,   1,   0,   1,   0,   1,   1
4,     99000,        0,     .6,      0,  1,   1,   0,   1,   0,   1,   1
5,     99000,        0,     .0,      .2, 1,   1,   0,   0,   1,   0,   1
6,     99000,        0,     .0,      .3, 1,   1,   0,   0,   1,   0,   1
''')
        # catcomb = '10011', '01011', '00101' = 19, 11, 5
        risk_by_event = _df('''\
event_id,agg_id,loss
1,     0,      12000
1,     1,      5000
1,     2,      3000
1,     3,      12000
1,     4,      5000
1,     5,      3000
''')
        expected = _df('''\
event_id,retention,claim,prop1,prop2,wxl1,wxl2,cat1,cat2,cat3,cat4,cat5,over_E,over_G
       1,   1000.0,40000.,17000.,4100,1600,1500,3800.,4200.,3800.,2500,500,2300,800''')
        bypolicy, byevent = by_policy_event(
            risk_by_event, pol_df, treaty_df)
        assert_ok(byevent, expected)


#############################################################################
#                            VALIDATION TESTS                               #
#############################################################################

VULN_STCO = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <vulnerabilityModel
    assetCategory="buildings"
    id="Nepal"
    lossCategory="structural"
    >
        <vulnerabilityFunction
        dist="LN"
        id="RC"
        >
            <imls
            imt="SA(0.2)"
            >
                2.0000000E-01 5.0000000E-01 9.0000000E-01 1.1000000E+00 1.3000000E+00
            </imls>
            <meanLRs>
                3.5000000E-02 7.0000000E-02 1.4000000E-01 2.8000000E-01 5.6000000E-01
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04
            </covLRs>
        </vulnerabilityFunction>
        <vulnerabilityFunction
        dist="LN"
        id="W"
        >
            <imls
            imt="SA(0.5)"
            >
                3.0000000E-02 7.0000000E-02 1.5000000E-01 2.2000000E-01 9.5000000E-01
            </imls>
            <meanLRs>
                6.3000000E-02 1.2500000E-01 2.5000000E-01 5.0000000E-01 1.0000000E+00
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 0.0000000E+00
            </covLRs>
        </vulnerabilityFunction>
        <vulnerabilityFunction
        dist="LN"
        id="RM"
        >
            <imls
            imt="PGA"
            >
                2.0000000E-02 3.0000000E-01 5.0000000E-01 9.0000000E-01 1.2000000E+00
            </imls>
            <meanLRs>
                5.0000000E-02 1.0000000E-01 2.0000000E-01 4.0000000E-01 8.0000000E-01
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04
            </covLRs>
        </vulnerabilityFunction>
    </vulnerabilityModel>
</nrml>
'''

VULN_NONSTCO = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <vulnerabilityModel
    assetCategory="buildings"
    id="Nepal"
    lossCategory="nonstructural"
    >
        <vulnerabilityFunction
        dist="LN"
        id="W"
        >
            <imls
            imt="SA(0.8)"
            >
                .03 7.0000000E-02 1.5000000E-01 2.2000000E-01 9.5000000E-01
            </imls>
            <meanLRs>
                3.0000000E-02 5.0000000E-02 1.0000000E-01 1.5000000E-01 2.0000000E-01
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04
            </covLRs>
        </vulnerabilityFunction>
        <vulnerabilityFunction
        dist="LN"
        id="RM"
        >
            <imls
            imt="SA(1.0)"
            >
                1.0000000E-01 2.0000000E-01 4.0000000E-01 7.0000000E-01 1.0000000E+00
            </imls>
            <meanLRs>
                1.0000000E-01 2.0000000E-01 3.5000000E-01 6.0000000E-01 9.0000000E-01
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04
            </covLRs>
        </vulnerabilityFunction>
        <vulnerabilityFunction
        dist="LN"
        id="RC"
        >
            <imls
            imt="PGA"
            >
                2.0000000E-02 3.0000000E-01 5.0000000E-01 9.0000000E-01 1.2000000E+00
            </imls>
            <meanLRs>
                4.0000000E-02 7.0000000E-02 1.4000000E-01 2.0000000E-01 2.5000000E-01
            </meanLRs>
            <covLRs>
                1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04 1.0000000E-04
            </covLRs>
        </vulnerabilityFunction>
    </vulnerabilityModel>
</nrml>
'''

EXPOXML = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <exposureModel
    category="buildings"
    id="ep"
    >
        <description>
            Exposure Model for buildings located in Pavia
        </description>
        <conversions>
            <area type="per_asset" unit="square meters"/>
            <costTypes>
                <costType name="structural" type="per_area" unit="EUR"/>
                <costType name="nonstructural" type="aggregated" unit="EUR"/>
            </costTypes>
        </conversions>
        <occupancyPeriods/>
        <tagNames>policy</tagNames>
        <assets>
            exposure.csv
        </assets>
    </exposureModel>
</nrml>
'''
EXPOCSV = '''\
id,number,taxonomy,lon,lat,nonstructural,structural,area,policy
a4,10,RM,87.7477,27.9015,2500,500,100,B
a2,1000,W,85.7477,27.9015,500,0.1,10,B
a0,3,RM,81.2985,29.1098,1500,100,10,A
a1,500,RC,83.0823,27.9006,1000,0.4,10,A
a3,10,RM,85.7477,27.9015,2500,500,1,B
'''

JOB = '''\
[general]
description = reinsurance case_1c (1 nonprop layer)
calculation_mode = event_based_risk
master_seed = 42

[exposure]
exposure_file = exposure_model.xml

[site_params]
reference_vs30_type = measured
reference_vs30_value = 760.0
reference_depth_to_2pt5km_per_sec = 5.0
reference_depth_to_1pt0km_per_sec = 100.0

[erf]
width_of_mfd_bin = 0.1
rupture_mesh_spacing = 2.0
area_source_discretization = 10

[logic_trees]
source_model_logic_tree_file = source_model_logic_tree.xml
gsim_logic_tree_file = gsim_logic_tree.xml

[hazard_calculation]
intensity_measure_types = PGA
truncation_level = 3
maximum_distance = 200.0
investigation_time = 1
number_of_logic_tree_samples = 0
ses_per_logic_tree_path = 200

[vulnerability]
structural_vulnerability_file = structural_vulnerability_model.xml
nonstructural_vulnerability_file = nonstructural_vulnerability_model.xml
contents_vulnerability_file = contents_vulnerability_model.xml
# business_interruption_vulnerability_file = downtime_vulnerability_model.xml
# occupants_vulnerability_file = occupants_vulnerability_model.xml

[risk_calculation]
aggregate_by = %(aggregate_by)s
reinsurance_file = {'structural+contents': 'reinsurance1.xml'}
total_losses = structural+contents
avg_losses = true
risk_investigation_time = 1

[export]
export_dir = ./
'''

EXPOSURE_MODEL_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <exposureModel id="ex1" category="buildings" taxonomySource="GEM taxonomy">
    <description>exposure model</description>

    <conversions>
      <costTypes>
        <costType name="structural" type="aggregated" unit="USD"/>
        <costType name="nonstructural" type="aggregated" unit="USD"/>
        <costType name="contents" type="aggregated" unit="USD"/>
      </costTypes>
    </conversions>

    <tagNames>tag_1 policy</tagNames>

    <occupancyPeriods>night </occupancyPeriods>

    <assets>
      exposure_model.csv
    </assets>

  </exposureModel>
</nrml>
'''

EXPOSURE_MODEL_CSV = '''\
id,lon,lat,taxonomy,number,structural,contents,nonstructural,business_interruption,night,tag_1,policy
a1,-122,38.113,tax1,1,10000,5000,15000,2000,6,zone_1,p1_a1
a2,-122.114,38.113,tax1,1,10000,5000,15000,2000,6,zone_1,p1_a2
a3,-122.57,38.113,tax1,1,10000,5000,15000,2000,6,zone_1,p1_a3
a4,-122,38,tax1,1,10000,5000,15000,2000,6,zone_2,p2
a5,-122,37.91,tax1,1,10000,5000,15000,2000,6,zone_2,p2
a6,-122,38.225,tax1,1,10000,5000,15000,2000,6,zone_2,p2
a7,-121.886,38.113,tax1,1,10000,5000,15000,2000,6,zone_2,p2
'''

GSIM_LOGIC_TREE = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.5">

<logicTree logicTreeID='lt1'>
  <logicTreeBranchingLevel branchingLevelID="bl1">
    <logicTreeBranchSet uncertaintyType="gmpeModel"
                        branchSetID="bs1"
                        applyToTectonicRegionType="Active Shallow Crust">

      <logicTreeBranch branchID="b1">
        <uncertaintyModel>BooreAtkinson2008</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>

  </logicTreeBranchSet>
  </logicTreeBranchingLevel>
</logicTree>

</nrml>
'''

SOURCE_MODEL_LOGIC_TREE = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.5">

<logicTree logicTreeID="lt1">
  <logicTreeBranchingLevel branchingLevelID="bl1">
    <logicTreeBranchSet uncertaintyType="sourceModel"
						branchSetID="bs1">
      <logicTreeBranch branchID="b1">
		<uncertaintyModel>source_model.xml</uncertaintyModel>
		<uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
	</logicTreeBranchSet>
  </logicTreeBranchingLevel>
</logicTree>

</nrml>
'''

STRUCTURAL_VULNERABILITY = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">

<vulnerabilityModel id="vm1" assetCategory="buildings" lossCategory="structural">

  <description>ln vf | tax3 | nzcov</description>

  <vulnerabilityFunction id="tax1" dist="LN">
    <imls imt="PGA">0.05 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00</imls>
    <meanLRs>0.01 0.04 0.10 0.20 0.33 0.50 0.67 0.80 0.90 0.96 0.99</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.38 0.40 0.38 0.32 0.24 0.12 0.03</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax2" dist="LN">
    <imls imt="PGA">0.05 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00</imls>
    <meanLRs>0.01 0.02 0.05 0.11 0.18 0.26 0.36 0.41 0.46 0.49 0.51</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.38 0.40 0.38 0.32 0.24 0.12 0.03</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax3" dist="LN">
    <imls imt="PGA">0.05 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00</imls>
    <meanLRs>0.01 0.04 0.09 0.18 0.28 0.47 0.58 0.71 0.79 0.85 0.91</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.38 0.40 0.38 0.32 0.24 0.12 0.03</covLRs>
  </vulnerabilityFunction>

</vulnerabilityModel>

</nrml>
'''

NONSTRUCTURAL_VULNERABILITY = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">

<vulnerabilityModel id="vm1" assetCategory="buildings" lossCategory="nonstructural">

  <description>ln vf | tax3 | imt3 | nonstructural</description>

  <vulnerabilityFunction id="tax1" dist="LN">
    <imls imt="PGA">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.01 0.05 0.12 0.24 0.40 0.60 0.80 0.96 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.32 0.24 0.12 0.03 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax2" dist="LN">
    <imls imt="SA(0.1)">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.01 0.05 0.12 0.24 0.40 0.60 0.80 0.96 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.32 0.24 0.12 0.03 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax3" dist="LN">
    <imls imt="SA(0.3)">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.01 0.05 0.12 0.24 0.40 0.60 0.80 0.96 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.32 0.32 0.24 0.12 0.03 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

</vulnerabilityModel>

</nrml>
'''

CONTENTS_VULNERABILITY = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">

<vulnerabilityModel id="vm1" assetCategory="buildings" lossCategory="contents">

  <description>ln vf | tax3 | imt3 | contents</description>

  <vulnerabilityFunction id="tax1" dist="LN">
    <imls imt="PGA">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.02 0.10 0.33 0.66 0.90 0.98 1.00 1.00 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.24 0.12 0.03 0.00 0.00 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax2" dist="LN">
    <imls imt="SA(0.1)">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.02 0.10 0.33 0.66 0.90 0.98 1.00 1.00 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.24 0.12 0.03 0.00 0.00 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

  <vulnerabilityFunction id="tax3" dist="LN">
    <imls imt="SA(0.4)">0.005 0.15 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 2.0</imls>
    <meanLRs>0.02 0.10 0.33 0.66 0.90 0.98 1.00 1.00 1.00 1.00 1.00</meanLRs>
    <covLRs>0.03 0.12 0.24 0.24 0.12 0.03 0.00 0.00 0.00 0.00 0.00</covLRs>
  </vulnerabilityFunction>

</vulnerabilityModel>

</nrml>
'''

REINSURANCE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
      xmlns:gml="http://www.opengis.net/gml">
  <reinsuranceModel>
    <description>reinsurance model</description>

    <fieldMap>
      <field input="treaty_1" type="prop" max_cession_event="800" />
      <field input="treaty_2" type="prop" max_cession_event="400" />
      <field input="xlr1" type="wxlr" deductible="200" limit="1000" />
    </fieldMap>

  <policies>policy1.csv</policies>

  </reinsuranceModel>
</nrml>
'''

POLICY = '''\
policy,liability,deductible,retention,treaty_1,treaty_2,xlr1,XLR
p1_a1,2000,400,0.7,0.1,0.2,1,0
p1_a2,1000,200,0.6,0.3,0.1,1,0
p1_a3,1000,100,0.8,0,0.2,1,0
p2,2000,500,0.5,0.4,0.1,0,1
'''


class WrongInputTestCase(unittest.TestCase):
    """
    Tests for errors in the input files
    """
    @classmethod
    def setUpClass(cls):
        # Creating directory with fake input files
        cls.tmpdir = tempfile.mkdtemp()
        cls.jobfname = os.path.join(cls.tmpdir, 'job.ini')
        cls.xmlfname = os.path.join(cls.tmpdir, 'reinsurance.xml')
        cls.csvfname = os.path.join(cls.tmpdir, 'policy.csv')
        cls.vuln_stcofname = os.path.join(
            cls.tmpdir, 'vulnerability_model_stco.xml')
        cls.vuln_nonstcofname = os.path.join(
            cls.tmpdir, 'vulnerability_model_nonstco.xml')
        cls.expoxmlfname = os.path.join(cls.tmpdir, 'exposure.xml')
        cls.expocsvfname = os.path.join(cls.tmpdir, 'exposure.csv')
        cls.expo1xmlfname = os.path.join(cls.tmpdir, 'exposure_model.xml')
        cls.expo1csvfname = os.path.join(cls.tmpdir, 'exposure_model.csv')
        cls.gsimltfname = os.path.join(
            cls.tmpdir, 'gsim_logic_tree.xml')
        cls.srcmdlltfname = os.path.join(
            cls.tmpdir, 'source_model_logic_tree.xml')
        cls.strvulnfname = os.path.join(
            cls.tmpdir, 'structural_vulnerability_model.xml')
        cls.nonstrvulnfname = os.path.join(
            cls.tmpdir, 'nonstructural_vulnerability_model.xml')
        cls.contvulnfname = os.path.join(
            cls.tmpdir, 'contents_vulnerability_model.xml')
        cls.reinsxmlfname = os.path.join(
            cls.tmpdir, 'reinsurance1.xml')
        cls.policyfname = os.path.join(
            cls.tmpdir, 'policy1.csv')
        with open(cls.xmlfname, 'w') as xml:
            xml.write(XML_NP.format('policy.csv'))
        with open(cls.vuln_stcofname, 'w') as xml:
            xml.write(VULN_STCO)
        with open(cls.vuln_nonstcofname, 'w') as xml:
            xml.write(VULN_NONSTCO)
        with open(cls.expoxmlfname, 'w') as xml:
            xml.write(EXPOXML)
        with open(cls.expocsvfname, 'w') as xml:
            xml.write(EXPOCSV)
        with open(cls.expo1xmlfname, 'w') as xml:
            xml.write(EXPOSURE_MODEL_XML)
        with open(cls.expo1csvfname, 'w') as xml:
            xml.write(EXPOSURE_MODEL_CSV)
        with open(cls.gsimltfname, 'w') as xml:
            xml.write(GSIM_LOGIC_TREE)
        with open(cls.srcmdlltfname, 'w') as xml:
            xml.write(SOURCE_MODEL_LOGIC_TREE)
        with open(cls.strvulnfname, 'w') as xml:
            xml.write(STRUCTURAL_VULNERABILITY)
        with open(cls.nonstrvulnfname, 'w') as xml:
            xml.write(NONSTRUCTURAL_VULNERABILITY)
        with open(cls.contvulnfname, 'w') as xml:
            xml.write(CONTENTS_VULNERABILITY)
        with open(cls.reinsxmlfname, 'w') as xml:
            xml.write(REINSURANCE)
        with open(cls.policyfname, 'w') as csv:
            csv.write(POLICY)
        readinput.Global.reset()  # for independence from other tests

    # Checks in the policy file

    def test_policy_in_exposure_missing_in_policy_csv(self):
        POLICYCSV = '''\
Policy,Limit,Deductible,WXLR_metro,WXLR_rural,CatXL_reg
VA_region_1,8000,100,0,0,1
rur_Ant_1,  9000,500,1,1,0
'''
        with open(self.csvfname, 'w') as csv:
            csv.write(POLICYCSV)
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(self.xmlfname, policy_idx)
        self.assertIn('policy "VA_region_2" is missing', str(ctx.exception))

    def test_policy_duplicated(self):
        with open(self.csvfname, 'w') as csv:
            csv.write(CSV_NP.replace('VA_region_1', 'VA_region_2'))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(self.xmlfname, policy_idx)
        self.assertIn('(row 3): a duplicate policy was found: "VA_region_2"',
                      str(ctx.exception))

    def test_negative_liability(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,-10000,100,.1,.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('(row 3): a negative liability was found',
                      str(ctx.exception))

    def test_negative_deductible(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,-100,.1,.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('(row 3): a negative deductible was found',
                      str(ctx.exception))

    def test_empty_liability(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,,100,.1,.2
VA_region_2,10000,100,.1,.2
rur_Ant_1,,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('(rows [2, 4]): empty liability values were found',
                      str(ctx.exception))

    def test_empty_deductible(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,,.1,.2
VA_region_2,10000,100,.1,.2
rur_Ant_1,10000,,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('(rows [2, 4]): empty deductible values were found',
                      str(ctx.exception))

    def test_nonprop_treaty_non_boolean(self):
        CSV = '''\
Policy,Limit,Deductible,WXLR_metro,WXLR_rural,CatXL_reg
VA_region_1,8000,100,0,0,1
VA_region_2,4000,200,1,1,1.5
rur_Ant_1,  9000,500,1,1,0
'''
        with open(self.csvfname, 'w') as csv:
            csv.write(CSV)
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(self.xmlfname, policy_idx)
        self.assertIn('(row 3): values for CatXL_reg must be either 0 or 1',
                      str(ctx.exception))

    def test_treaty_types_in_a_wrong_order_in_policies_csv(self):
        csvfname = general.gettemp(CSV_NP.replace(
            'Policy,Limit,Deductible,WXLR_metro,WXLR_rural,CatXL_reg',
            'Policy,Limit,Deductible,WXLR_metro,CatXL_reg,WXLR_rural'))
        xmlfname = general.gettemp(XML_NP.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            'treaty type columns must be in the order'
            ' (\'prop\', \'wxlr\', \'catxl\'). Treaty "WXLR_rural" of'
            ' type "wxlr" was found after treaty "CatXL_reg" of'
            ' type "catxl"', str(ctx.exception))

    # Checks in the reinsurance file

    def test_treaty_in_reinsurancexml_missing_in_policycsv(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,xxsurplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.1,.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('(line 8): surplus is missing in', str(ctx.exception))

    def test_type_within_prop_wxlr_or_catxl(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace('catxl', 'wrongtype'))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            "(line 12): valid treaty types are ('prop', 'wxlr', 'catxl')."
            " 'wrongtype' was found instead", str(ctx.exception))

    def test_treaty_types_in_a_wrong_order_in_reinsurance_xml(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp('''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
      xmlns:gml="http://www.opengis.net/gml">
  <reinsuranceModel>
    <description>reinsurance model</description>
    <fieldMap>
      <field oq="policy" input="Policy" />
      <field oq="deductible" input="Deductible" />
      <field oq="liability" input="Limit" />
      <field input="WXLR_metro" type="wxlr" deductible="500" limit="3500" />
      <field input="CatXL_reg" type="catxl" deductible="50" limit="2500" />
      <field input="WXLR_rural" type="wxlr" deductible="200" limit="5000" />
    </fieldMap>
    <policies>{}</policies>
  </reinsuranceModel>
</nrml>
'''.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            '(line 12): treaty types must be specified in the order'
            ' (\'prop\', \'wxlr\', \'catxl\'). Treaty "WXLR_rural"'
            ' of type "wxlr" was found after treaty "CatXL_reg" of'
            ' type "catxl"', str(ctx.exception))

    def test_deductible_is_negative(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'deductible="200"', 'deductible="-200"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert deductible->positivefloat: "
                      "float -200.0 < 0, line 11, line 11", str(ctx.exception))

    def test_deductible_is_empty(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'deductible="200"', 'deductible=""'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert deductible->positivefloat: "
                      "Got an empty string, line 11, line 11",
                      str(ctx.exception))

    def test_deductible_is_not_float(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'deductible="200"', 'deductible="XXX"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert deductible->positivefloat: "
                      "could not convert string to float: 'XXX', "
                      "line 11, line 11", str(ctx.exception))

    def test_limit_is_negative(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'limit="5000"', 'limit="-5000"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert limit->positivefloat: "
                      "float -5000.0 < 0, line 11, line 11",
                      str(ctx.exception))

    def test_limit_is_empty(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'limit="5000"', 'limit=""'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert limit->positivefloat: "
                      "Got an empty string, line 11, line 11",
                      str(ctx.exception))

    def test_limit_is_not_float(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'limit="5000"', 'limit="XXX"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert limit->positivefloat: "
                      "could not convert string to float: 'XXX', "
                      "line 11, line 11", str(ctx.exception))

    def test_max_cession_event_is_negative(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'deductible="200"', 'max_cession_event="-200"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert max_cession_event->positivefloat: "
                      "float -200.0 < 0, line 11, line 11", str(ctx.exception))

    def test_max_cession_event_is_not_float(self):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(
            XML_NP.format(csvfname).replace(
                'deductible="200"', 'max_cession_event="XXX"'))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn("Could not convert max_cession_event->positivefloat: "
                      "could not convert string to float: 'XXX', "
                      "line 11, line 11", str(ctx.exception))

    def test_missing_aggregate_by_policy(self):
        with open(self.jobfname, 'w') as job:
            job.write((JOB % dict(aggregate_by='policy')).replace(
                'aggregate_by = policy\n', ''))
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_oqparam(self.jobfname)
        self.assertIn(
            "The field `aggregate_by = policy` in the %s file is required for"
            " reinsurance calculations." % self.jobfname, str(ctx.exception))

    def test_correct_aggregate_by_policy_semicolon_taxonomy(self):
        with open(self.jobfname, 'w') as job:
            job.write(JOB % dict(aggregate_by='policy; taxonomy'))
        oq = readinput.get_oqparam(self.jobfname)
        pol_df, treaty_df, fmap = readinput.get_reinsurance(oq)
        self.assertEqual(len(pol_df), 4)
        self.assertEqual(len(treaty_df), 3)
        self.assertEqual(len(fmap), 0)

    def test_wrong_aggregate_by_taxonomy_semicolon_policy(self):
        with open(self.jobfname, 'w') as job:
            job.write(JOB % dict(aggregate_by='taxonomy; policy'))
        oq = readinput.get_oqparam(self.jobfname)
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_reinsurance(oq)
        self.assertIn("aggregate_by=[['taxonomy'], ['policy']]",
                      str(ctx.exception))

    def test_wrong_aggregate_by_policy_comma_taxonomy(self):
        with open(self.jobfname, 'w') as job:
            job.write(JOB % dict(aggregate_by='policy, taxonomy'))
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_oqparam(self.jobfname)
        self.assertIn(
            "The field `aggregate_by = policy` in the %s file is required for"
            " reinsurance calculations. Got `aggregate_by = [['policy',"
            " 'taxonomy']]` instead." % self.jobfname, str(ctx.exception))

    def test_missing_total_losses(self):
        with open(self.jobfname, 'w') as job:
            job.write((JOB % dict(aggregate_by='policy')).replace(
                'total_losses = structural+contents\n', ''))
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_oqparam(self.jobfname)
        self.assertIn(
            'you forgot to set total_losses=structural+contents',
            str(ctx.exception))

    def test_multiple_reinsurance_files(self):
        with open(self.jobfname, 'w') as job:
            job.write((JOB % dict(aggregate_by='policy')).replace(
                "reinsurance_file = "
                "{'structural+contents': 'reinsurance1.xml'}",
                "reinsurance_file = "
                "{'structural': 'reinsurance1.xml', "
                "'contents': 'reinsurance1.xml'}"))
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_oqparam(self.jobfname)
        self.assertIn(
            "too many loss types in reinsurance ['structural', 'contents']",
            str(ctx.exception))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)


# TODO: integrate in the class above
class InvalidFractionsTestCase(unittest.TestCase):
    def test_negative_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.1,-.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            '(row 3): proportional fraction for treaty "surplus", -0.2, is'
            ' not >= 0 and <= 1', str(ctx.exception))

    def test_toolarge_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.7,.6
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            '(row 3): the sum of proportional fractions is 1.3.'
            ' It must be >= 0 and <= 1', str(ctx.exception))

    def test_excess_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.3,.8
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(
            '(row 3): the sum of proportional fractions is 1.1.'
            ' It must be >= 0 and <= 1', str(ctx.exception))
