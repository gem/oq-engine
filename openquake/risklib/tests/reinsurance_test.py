# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022, GEM Foundation
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
event_id,policy_id,claim,retention,prop1,prop2,policy_grp
1,       1,        12000,  2400.0,6000.0,3600.0,AB
1,       2,         5000,  1500.0,2000.0,1500.0,AB
1,       3,         3000,   600.0,1500.0, 900.0,AB
1,       4,         6000,  1800.0,2400.0,1800.0,AB''')
        byevent = reinsurance._by_event(bypolicy, treaty_df)
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
        bypolicy, byevent = reinsurance.by_policy_event(
            risk_by_event, pol_df, treaty_df)
        assert_ok(byevent, expected)


class ReinsuranceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        csvfname = general.gettemp(CSV_NP)
        xmlfname = general.gettemp(XML_NP.format(csvfname))
        cls.policy_df, treaty_df, fmap = reinsurance.parse(
            xmlfname, policy_idx)
        print(cls.policy_df)
        print(treaty_df)
        assert len(cls.policy_df) == 3
        assert len(treaty_df) == 3
        assert fmap == {'deductible': 'Deductible',
                        'liability': 'Limit',
                        'policy': 'Policy'}
        cls.treaty_df = treaty_df
        
    def test_policy1(self):
        # VA_region_1, CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,claim,retention,WXLR_metro,WXLR_rural
41,1,1078.0742,1078.0742,0.0,0.0
40,1,1070.1654,1070.1654,0.0,0.0
33,1,1017.8770,1017.8770,0.0,0.0
13,1, 664.2781, 664.2781,0.0,0.0
 5,1, 661.1264, 661.1264,0.0,0.0''')
        pol = dict(self.policy_df.loc[0])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_policy2(self):
        # VA_region_2
        # WXLR_metro(500, 3500) + WXLR_rural(200, 5000) + CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,claim,retention,WXLR_metro,WXLR_rural
0,27,2 ,2941.0974,200.0,2441.0974,300.0
1,28,2 ,2936.3154,200.0,2436.3154,300.0
2,26,2 ,2659.9182,200.0,2159.9182,300.0
3,29,2 ,2403.0217,200.0,1903.0217,300.0
4,23,2 ,1530.9891,200.0,1030.9891,300.0
5,41,2 , 978.0742,200.0, 478.0742,300.0
6,40,2 , 970.1654,200.0, 470.1654,300.0
7,21,2 , 957.2078,200.0, 457.2078,300.0
8,13,2 , 564.2781,200.0,  64.2781,300.0
9, 5,2 , 561.1264,200.0,  61.1264,300.0''')
        pol = dict(self.policy_df.loc[1])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_policy3(self):
        # rur_Ant_1, WXLR_metro(500, 3500) + WXLR_rural(200, 5000)
        expected = _df('''\
event_id,policy_id,claim,retention,WXLR_metro,WXLR_rural
25,      3,        8500,700.0, 3000,4800''')
        pol = dict(self.policy_df.loc[2])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_by_cat_no_apply(self):
        expected = _df('''\
event_id,retention,claim,WXLR_metro,WXLR_rural,CatXL_reg
25,      700.0,   8500.0,  3000.0,  4800.0,   0.0''', index_col='event_id')
        bypolicy, byevent = reinsurance.by_policy_event(
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
        bypolicy, byevent = reinsurance.by_policy_event(
            risk_by_event, pol_df, treaty_df)

    def test_many_levels(self):
        treaty_df = _df('''\
id,type,deductible,limit,code
prop1,prop,   0,  90000,A
cat1,catxl, 200,   4000,B
cat2,catxl, 500,  10000,C
cat3,catxl, 200,   4000,D
cat4,catxl, 500,  10000,E
cat5,catxl,1000,  50000,F
''')
        pol_df = _df('''\
policy,liability,deductible,prop1,cat1,cat2,cat3,cat4,cat5
1,     99000,        0,     .5,      1,   0,   0,   1,   1
2,     99000,        0,     .4,      1,   0,   0,   1,   1
3,     99000,        0,     .6,      0,   1,   0,   1,   1
4,     99000,        0,     .6,      0,   1,   0,   1,   1
5,     99000,        0,     .0,      0,   0,   1,   0,   1
6,     99000,        0,     .0,      0,   0,   1,   0,   1
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
event_id,retention,claim,prop1,cat1,cat2,cat3,cat4,cat5,over_B,over_D
       1,   1000.0,40000.,17000.,3800.,5500.,3800.,5200.,3700.,5200.,4200.''')
        bypolicy, byevent = reinsurance.by_policy_event(
            risk_by_event, pol_df, treaty_df)
        assert_ok(byevent, expected)


#############################################################################
#                            VALIDATION TESTS                               #
#############################################################################

JOB = '''\
[general]
random_seed = 23
master_seed = 42
description = Test
calculation_mode = event_based_risk
aggregate_by = %(aggregate_by)s
structural_vulnerability_file = vulnerability_model_stco.xml
nonstructural_vulnerability_file = vulnerability_model_nonstco.xml
reinsurance_file = {'structural+nonstructural': 'reinsurance.xml'}
total_losses = structural+nonstructural
exposure_file = exposure.xml
discard_assets = true
region = 81.1 26, 88 26, 88 30, 81.1 30
asset_hazard_distance = 20
sites = 87.7477 27.9015

[calculation]
investigation_time = 50.0
ses_per_logic_tree_path = 20
maximum_distance = 100.0
return_periods = [30, 60, 120, 240, 480, 960]
'''

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


class WrongInputTestCase(unittest.TestCase):
    """
    Tests for errors in the input files
    """
    @classmethod
    def setUpClass(cls):
        print('Creating directory with fake input files')
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
        self.assertIn('policy contains duplicates', str(ctx.exception))

    def test_negative_liability(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,-10000,100,.1,.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('liabilities must be => 0', str(ctx.exception))

    def test_negative_deductible(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,-100,.1,.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(InvalidFile) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn('deductibles must be => 0', str(ctx.exception))

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
        self.assertIn('field CatXL_reg must be 0 or 1', str(ctx.exception))

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
        self.assertIn('surplus is missing', str(ctx.exception))

    # TODO: finish
    def _test_wrong_aggregate_by_1(self):
        with open(self.jobfname, 'w') as job:
            job.write(JOB % dict(aggregate_by='taxonomy; policy'))
        oq = readinput.get_oqparam(self.jobfname)
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_reinsurance(oq)
        self.assertIn('aggregate_by=taxonomy; policy', str(ctx.exception))

    @classmethod
    def tearDownClass(cls):
        print('Deleting directory with fake input files')
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
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3: invalid fraction surplus=-0.2', str(ctx.exception))

    def test_toolarge_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.1,1.2
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3: invalid fraction surplus=1.2', str(ctx.exception))

    def test_excess_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.3,.8
rur_Ant_1,10000,100,.1,.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3 the sum of the fractions must be under 1, got 1.1',
                      str(ctx.exception))
