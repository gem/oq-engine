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


# NB: agg_id starts from 0, policy_id from 1
risk_by_event = _df('''\
event_id	agg_id	loss
25	1	4159.046
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
33	1	1117.877
20	1	1066.6654
16	1	1016.66644
22	1	1000.24884
13	0	764.2781
13	1	764.2781
5	1	761.1264
5	0	761.1264
''', sep='\t')

CSV = '''\
Policy,Limit,Deductible,WXLR_metro,CatXL_rural,CatXL_reg
VA_region_1,7850000,0,0,0,1
VA_region_2,54000000,1080000,0,0,1
VA_region_3,23300000,466000,0,0,1
VA_region_4,16400000,328000,0,0,1
VA_region_5,30000000,600000,0,0,1
VA_region_6,7900000,0,0,0,1
VA_region_7,52000000,1040000,0,0,1
VA_region_8,25000000,500000,0,0,1
VA_region_9,10000000,200000,0,0,1
rur_Ant_1,1575000,31500,0,1,0
rur_Ant_10,14250000,285000,0,1,0
rur_Ant_100,8750000,175000,0,1,0
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
             max_retention="50" limit="5000" />
    </fieldMap>
    <policies>{}</policies>
  </reinsuranceModel>
</nrml>
'''

class ReinsuranceTestCase(unittest.TestCase):
    # "WXLR_metro" max_retention="500" limit="3500"
    # "CatXL_rural" max_retention="200" limit="5000"
    # "CatXL_reg" max_retention="50" limit="5000"
    @classmethod
    def setUpClass(cls):
        csvfname = general.gettemp(CSV)
        policy_df, treaty_df, maxc, fmap = reinsurance.parse(
            general.gettemp(XML.format(csvfname)))
        assert not maxc  # there are no proportional treaties
        print(policy_df)
        print(treaty_df)
        print(fmap)
        assert len(policy_df) == 12
        assert len(treaty_df) == 3
        assert len(fmap) == 6
        cls.treaty_df = treaty_df.set_index('id')
        
    def test_policy1(self):
        # VA_region_1, CatXL_reg, max_retention=50, limit=5000
        expected = _df('''\
event_id,policy_id,claim,retention,nonprop1,nonprop2,nonprop3
41,1,1060.26678,50.0,560.26678,300.0,150.0
40,1,1053.14886,50.0,553.14886,300.0,150.0
33,1,1006.08930,50.0,506.08930,300.0,150.0
13,1, 687.85029,50.0,187.85029,300.0,150.0
 5,1, 685.01376,50.0,185.01376,300.0,150.0
''')
        pol = dict(policy=1, liability=1.0, liability_abs=False,
                   deductible=0.1, deductible_abs=False,
                   nonprop1=True, nonprop2=True, nonprop3=True)
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        print('\n', out)
        assert len(out.compare(expected)) == 0

    def test_policy2(self):
        # VA_region_2, CatXL_reg, max_retention=50, limit=5000
        expected = _df('''\
event_id,policy_id,claim,retention,nonprop1,nonprop2,nonprop3
25,2,3535.189100,50.0,3035.189100,300.0,150.0
27,2,2669.932790,50.0,2169.932790,300.0,150.0
28,2,2665.868090,50.0,2165.868090,300.0,150.0
26,2,2430.930470,50.0,1930.930470,300.0,150.0
29,2,2212.568445,50.0,1712.568445,300.0,150.0
23,2,1471.340735,50.0, 971.340735,300.0,150.0
41,2,1001.363070,50.0, 501.363070,300.0,150.0
40,2, 994.640590,50.0, 494.640590,300.0,150.0
21,2, 983.626630,50.0, 483.626630,300.0,150.0
33,2, 950.195450,50.0, 450.195450,300.0,150.0
20,2, 906.665590,50.0, 406.665590,300.0,150.0
16,2, 864.166474,50.0, 364.166474,300.0,150.0
22,2, 850.211514,50.0, 350.211514,300.0,150.0
13,2, 649.636385,50.0, 149.636385,300.0,150.0
 5,2, 646.957440,50.0, 146.957440,300.0,150.0
''')
        pol = dict(policy=2, liability=0.9, liability_abs=False,
                   deductible=0.05, deductible_abs=False,
                   nonprop1=True, nonprop2=True, nonprop3=True)
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        print('\n', out)
        assert len(out.compare(expected)) == 0
