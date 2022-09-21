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
import pathlib
import unittest
import pandas
from openquake.risklib import reinsurance

CDIR = pathlib.Path(os.path.dirname(__file__))

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


class ReinsuranceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        policy_df, treaty_df, maxc, fmap = reinsurance.parse(
            CDIR / 'reinsurance.xml')
        print(policy_df)
        print(treaty_df)
        print(maxc)
        print(fmap)
        assert len(policy_df) == 12
        assert len(treaty_df) == 3
        assert len(maxc) == 5
        assert len(fmap) == 16
        cls.treaty_df = treaty_df
        
    def test_policy1(self):
        pol = dict(policy=1, liability=1.0, liability_abs=False,
                   deductible=0.1, deductible_abs=False, nonprop1='wxlr')
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        print('\n', out)

    def test_policy2(self):
        pol = dict(policy=2, liability=0.9, liability_abs=False,
                   deductible=0.05, deductible_abs=False, nonprop1='wxlr')
        out = reinsurance.by_policy(risk_by_event, pol, self.treaty_df)
        print('\n', out)
