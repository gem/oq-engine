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
import unittest
import pandas
from openquake.baselib import general
from openquake.risklib import reinsurance

def _df(string, sep=',', index_col=None):
    # build a DataFrame from a string
    return pandas.read_csv(io.StringIO(string), sep=sep, index_col=index_col,
                           keep_default_na=False)

def assert_ok(got, exp):
    cmp = got.compare(exp)
    if len(cmp):
        print(cmp)
        raise ValueError('got unexpected result')


# NB: agg_id starts from 0, policy_id from 1
risk_by_event = _df('''\
event_id	agg_id	loss
25	2	4159.046
27	1	3141.0974
28	1	3136.3154
26	1	2859.9182
29	1	2603.0217
23	1	1730.9891
41	0	1178.0742
41	1	1178.0742
40	0	1170.1654
40	1	1170.1654
21	1	1157.2078
33	0	1117.877
13	0	764.2781
13	1	764.2781
5	1	761.1264
5	0	761.1264
''', sep='\t')

CSV = '''\
Policy,Limit,Deductible,WXLR_metro,CatXL_rural,CatXL_reg
VA_region_1,8000,100,0,0,1
VA_region_2,4000,200,1,1,1
rur_Ant_1,  5000,500,1,1,0
'''

XML = '''\
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
      <field oq="nonprop2" input="CatXL_rural" type="catxl"
             max_retention="200" limit="5000" />
      <field oq="nonprop3" input="CatXL_reg" type="catxl"
             max_retention="50" limit="2500" />
    </fieldMap>
    <policies>{}</policies>
  </reinsuranceModel>
</nrml>
'''

class ReinsuranceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        csvfname = general.gettemp(CSV)
        cls.policy_df, treaty_df, maxc, fmap = reinsurance.parse(
            general.gettemp(XML.format(csvfname)))
        cls.policy_df['policy'] = range(1, 4)  # starts from 1
        assert not maxc  # there are no proportional treaties
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
event_id,policy_id,claim,retention,nonprop1,nonprop2,nonprop3
41,1,1078.0742,50.0,0.0,0.0,1028.0742
40,1,1070.1654,50.0,0.0,0.0,1020.1654
33,1,1017.8770,50.0,0.0,0.0,967.8770
13,1, 664.2781,50.0,0.0,0.0,614.2781
 5,1, 661.1264,50.0,0.0,0.0,611.1264''')
        pol = dict(self.policy_df.loc[0])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_policy2(self):
        # VA_region_2
        # WXLR_metro(500, 3500) + CatXL_Rural(200, 5000) + CatXL_reg(50, 2500)
        expected = _df('''\
event_id,policy_id,claim,retention,nonprop1,nonprop2,nonprop3
27,2,2941.0974,50.0,2441.0974,300.0,150.0
28,2,2936.3154,50.0,2436.3154,300.0,150.0
26,2,2659.9182,50.0,2159.9182,300.0,150.0
29,2,2403.0217,50.0,1903.0217,300.0,150.0
23,2,1530.9891,50.0,1030.9891,300.0,150.0
41,2, 978.0742,50.0, 478.0742,300.0,150.0
40,2, 970.1654,50.0, 470.1654,300.0,150.0
21,2, 957.2078,50.0, 457.2078,300.0,150.0
13,2, 564.2781,50.0,  64.2781,300.0,150.0
 5,2, 561.1264,50.0,  61.1264,300.0,150.0''')
        pol = dict(self.policy_df.loc[1])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)

    def test_policy3(self):
        # rur_Ant_1, WXLR_metro(500, 3500) + CatXL_Rural(200, 5000)
        expected = _df('''\
event_id,policy_id,claim,retention,nonprop1,nonprop2,nonprop3
25,3,3659.046,200.0,3159.046,300.0,0.0''')        
        pol = dict(self.policy_df.loc[2])
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        assert_ok(out, expected)
