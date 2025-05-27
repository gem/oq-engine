# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

"""
A nontrivial test case with 8 realizations:

<FullLogicTree
b1, SA_RA_CATAL1_00.xml, trt=[0, 1]: 4 realization(s)
b2, SA_RA_CATAL2_00.xml, trt=[2, 3]: 4 realization(s)>
<RlzsAssoc
0,AkkarBommer2010: ['<2,b1,b2_b3,w=0.126>', '<3,b1,b2_b4,w=0.054>']
0,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<1,b1,b1_b4,w=0.126>']
1,AkkarBommer2010: ['<1,b1,b1_b4,w=0.126>', '<3,b1,b2_b4,w=0.054>']
1,AtkinsonBoore2006: ['<0,b1,b1_b3,w=0.294>', '<2,b1,b2_b3,w=0.126>']
2,AkkarBommer2010: ['<6,b2,b2_b3,w=0.084>', '<7,b2,b2_b4,w=0.036>']
2,AtkinsonBoore2006: ['<4,b2,b1_b3,w=0.196>', '<5,b2,b1_b4,w=0.084>']
3,AkkarBommer2010: ['<5,b2,b1_b4,w=0.084>', '<7,b2,b2_b4,w=0.036>']
3,AtkinsonBoore2006: ['<4,b2,b1_b3,w=0.196>', '<6,b2,b2_b3,w=0.084>']>
"""
