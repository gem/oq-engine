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
import sys
import unittest
import numpy
import pandas
from openquake.baselib import general
from openquake.risklib import reinsurance

aac = numpy.testing.assert_allclose

def _df(string, sep=',', index_col=None):
    # build a DataFrame from a string
    return pandas.read_csv(io.StringIO(string), sep=sep, index_col=index_col,
                           keep_default_na=False)

def assert_ok(got, exp):
    assert (got.columns == exp.columns).all()
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
      <field oq="nonprop1" input="WXLR_metro" type="wxlr"
             max_retention="500" limit="3500" />
      <field oq="nonprop2" input="WXLR_rural" type="wxlr"
             max_retention="200" limit="5000" />
      <field oq="nonprop3" input="CatXL_reg" type="catxl"
             max_retention="50" limit="2500" />
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


class InvalidFractionsTestCase(unittest.TestCase):
    def test_negative_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.1,-.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3: invalid fraction surplus=-0.2', str(ctx.exception))

    def test_toolarge_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.1,1.2''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3: invalid fraction surplus=1.2', str(ctx.exception))

    def test_excess_fraction(self):
        csvfname = general.gettemp('''\
policy,liability,deductible,qshared,surplus
VA_region_1,10000,100,.1,.2
VA_region_2,10000,100,.3,.8''')
        xmlfname = general.gettemp(XML_PR.format(csvfname))
        with self.assertRaises(ValueError) as ctx:
            reinsurance.parse(xmlfname, policy_idx)
        self.assertIn(':3 the sum of the fractions must be under 1, got 1.1',
                      str(ctx.exception))


class ProportionalTestCase(unittest.TestCase):
    def test_single_portfolio(self):
        treaty_df = _df('''\
id,type,max_retention,limit
prop1,prop,      0,    5000
prop2,prop,      0,    8000
''').set_index('id')
        bypolicy = _df('''\
event_id,policy_id,claim,retention,prop1,prop2
1,       1,        12000,  2400.0,6000.0,3600.0
1,       2,         5000,  1500.0,2000.0,1500.0
1,       3,         3000,   600.0,1500.0, 900.0
1,       4,         6000,  1800.0,2400.0,1800.0''')
        byevent = reinsurance._by_event(bypolicy, treaty_df)
        assert_ok(byevent, _df('''\
event_id,claim,retention,prop1,prop2,overspill1
       1,26000,13200.0,5000.0,7800.0,6900.0'''))

    def test_two_portfolios(self):
        # the first treaty applies to the first two policies,
        # the second to the last two policies
        treaty_df = _df('''\
id,type,max_retention,limit
prop1,prop,      0,    5000
prop2,prop,      0,    8000
''').set_index('id')
        pol_df = _df('''\
policy,liability,deductible,prop1,prop2
1,     99000,        0,     .5,   0
2,     99000,        0,     .4,   0
3,     99000,        0,     0,   .6
4,     99000,        0,     0,   .6
''')
        risk_by_event = _df('''\
event_id,agg_id,loss
1,     0,      12000
1,     1,      5000
1,     2,      3000
1,     3,      6000
''')
        expected = _df('''\
event_id,claim,retention,prop1,prop2,overspill1
       1,26000,15600.0,5000.0,5400.0,3000.0
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
        print(fmap)
        assert len(cls.policy_df) == 3
        assert len(treaty_df) == 3
        assert len(fmap) == 6
        cls.treaty_df = treaty_df.set_index('id')
        
    def test_policy1(self):
        # VA_region_1, CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,claim,retention,nonprop1,nonprop2
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
event_id,policy_id,claim,retention,nonprop1,nonprop2
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
event_id,policy_id,claim,retention,nonprop1,nonprop2
25,      3,        8500,700.0, 3000,4800''')
        pol = dict(self.policy_df.loc[2])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_by_cat_no_apply(self):
        expected = _df('''\
event_id,claim,retention,nonprop1,nonprop2,nonprop3
25,      8500.0,   700.0,   3000.0,  4800.0,   0.0''', index_col='event_id')
        bypolicy, byevent = reinsurance.by_policy_event(
            risk_by_event, self.policy_df, self.treaty_df)
        # the catxl does not apply on event 25
        byevent = byevent[byevent.event_id == 25].set_index('event_id')
        assert_ok(byevent, expected)

    def test_max_cession(self):
        treaty_df = _df('''\
id,type,max_retention,limit
prop1,prop,      0,    5000
nonprop1,wxlr, 200,    4000
nonprop2,catxl,500,   10000
''').set_index('id')
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
id,type,max_retention,limit
prop1,prop,   0,  90000
cat1,catxl, 200,   4000
cat2,catxl, 500,  10000
cat3,catxl, 200,   4000
cat4,catxl, 500,  10000
cat5,catxl,1000,  50000
''').set_index('id')
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
event_id,claim,retention,prop1,nonprop1,nonprop2,nonprop3,nonprop4,nonprop5
       1,40000,   1000.0,17000.0,3800.0,  5500.0,  3800.0,  5200.0,  3700.0''')
        bypolicy, byevent = reinsurance.by_policy_event(
            risk_by_event, pol_df, treaty_df)
        #assert_ok(byevent, expected)



def clever_agg(ukeys, claims, treaty_df, cession):
    """
    :param ukeys: a list of unique keys
    :param claims: a list of arrays of the same size
    :param treaty_df: a treaty DataFrame
    :param cession: a dictionary treaty.code -> cession array

    Recursively compute cessions and retentions for each treaty.
    Populate the cession dictionary and returns the final retention.
    """
    newkeys, newclaims = [], []
    for key, claim in zip(ukeys, claims):
        code = key[0]
        newkey = key[1:]
        if code != '.':
            tr = treaty_df.loc[code]
            reinsurance.apply_nonprop(
                cession[code], claim, tr.max_retention, tr.limit)
        newkeys.append(newkey)
        newclaims.append(claim)
    if len(newkeys) > 1:
        keys, sums = general.fast_agg2(newkeys, numpy.array(newclaims))
        return clever_agg(keys, sums, treaty_df, cession)
    return newclaims[0]


def test_clever_agg():
    treaty_df = _df('''\
id,type,max_retention,limit,code
cat1,catxl, 200,   4000,A
cat2,catxl, 500,  10000,B
cat3,catxl, 200,   4000,C
cat4,catxl, 500,  10000,D
cat5,catxl,1000,  50000,E
''').set_index('code')
    df = _df('''\
event_id,claim,key
0,6000,A..DE
0,3000,A..DE
0,1200,.B.DE
0,4800,.B.DE
0,5000,..C.E
0,3000,..C.E
1,6000,A..DE
1,3000,A..DE
1,1200,.B.DE
1,4800,.B.DE
1,5000,..C.E
1,3000,..C.E
''')
    eids, idxs = numpy.unique(df.event_id.to_numpy(), return_inverse=True)
    df['event_id'] = idxs
    E = len(eids)
    cession = {code: numpy.zeros(E) for code in treaty_df.index}
    keys, claims = [], []
    for key, grp in df.groupby('key'):
        claim = numpy.zeros(E)
        gb = grp[['event_id', 'claim']].groupby('event_id').sum()
        claim[gb.index] = gb.claim.to_numpy()
        keys.append(key)
        claims.append(claim)
    retention = clever_agg(keys, claims, treaty_df, cession)
    aac(cession['A'], [3800, 3800])
    aac(cession['B'], [5500, 5500])
    aac(cession['C'], [3800, 3800])
    aac(cession['D'], [5200, 5200])
    aac(cession['E'], [3700, 3700])
    aac(retention, [1000, 1000])
