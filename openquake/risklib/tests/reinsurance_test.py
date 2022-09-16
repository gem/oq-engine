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
from openquake.risklib.reinsurance import reinsurance

def _df(string, sep=',', index_col=None):  # DataFrame from string
    return pandas.read_csv(io.StringIO(string), sep=sep, index_col=index_col,
                           keep_default_na=False)

risk_by_event = _df('''\
event_id	agg_id	loss
25	2	4159.046
27	2	3141.0974
28	2	3136.3154
26	2	2859.9182
29	2	2603.0217
23	2	1730.9891
41	1	1178.0742
41	2	1178.0742
40	1	1170.1654
40	2	1170.1654
21	2	1157.2078
33	1	1117.877
33	2	1117.877
20	2	1066.6654
16	2	1016.66644
22	2	1000.24884
13	1	764.2781
13	2	764.2781
5	2	761.1264
5	1	761.1264
''', sep='\t')

treaty = _df('''\
treaty,treaty_type,treaty_unit,qs_retention,qs_cession,treaty_limit
qs_1,quota_share,policy,0.1,0.9,2000
''', index_col='treaty')


class ReinsuranceTestCase(unittest.TestCase):
    def test_1(self):
        pol = dict(policy=1, insurance_limit=1.0, deductible=0.1, treaty='')
        out = reinsurance(risk_by_event, pol, treaty)
        print('\n', out)

    def test_2(self):
        pol = dict(policy=2, insurance_limit=0.9, deductible=0.05,
                   treaty='qs_1')
        out = reinsurance(risk_by_event, pol, treaty)
        print('\n', out)
