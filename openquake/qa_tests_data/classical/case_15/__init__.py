# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
This is an example with a nontrivial logic tree producing 8 independent
realizations. The file source_model_2.xml contains a single area source
of kind "Active Shallow Crust": that means that the full GMPE logic tree

{"Active Shallow Crust": ["BA2008", "CB2008"],
"Stable Continental Crust": ["C2003", "T2002"]}

produces 2 pairs of identical GMPE realizations for that model.
Such realizations are managed by a single effective realization with double
weight.

The associations (grp_id, gsim) -> rlzs are:
{
0,BooreAtkinson2008: ['<0,SM1,BA2008_C2003,w=0.125>', '<1,SM1,BA2008_T2002,w=0.125>']
0,CampbellBozorgnia2008: ['<2,SM1,CB2008_C2003,w=0.125>', '<3,SM1,CB2008_T2002,w=0.125>']
1,Campbell2003: ['<0,SM1,BA2008_C2003,w=0.125>', '<2,SM1,CB2008_C2003,w=0.125>']
1,ToroEtAl2002: ['<1,SM1,BA2008_T2002,w=0.125>', '<3,SM1,CB2008_T2002,w=0.125>']
2,BooreAtkinson2008: ['<4,SM2_a3pt2b0pt8,BA2008_*,w=0.125>']
2,CampbellBozorgnia2008: ['<5,SM2_a3pt2b0pt8,CB2008_*,w=0.125>']
3,BooreAtkinson2008: ['<6,SM2_a3b1,BA2008_*,w=0.125>']
3,CampbellBozorgnia2008: ['<7,SM2_a3b1,CB2008_*,w=0.125>']
}
"""
