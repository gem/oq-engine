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
This is an example with a nontrivial source model logic tree
sampled 10 times (no path is sampled twice).
The associations (grp_id, gsim) -> rlzs are:
{
0,BooreAtkinson2008: ['<0,b11_b24_b33_b40_b52_b62_b72_b81_b91_b102_b112,b11,w=0.1>']
1,BooreAtkinson2008: ['<1,b11_b20_b31_b43_b52_b62_b72_b82_b91_b103_b112,b11,w=0.1>']
2,BooreAtkinson2008: ['<2,b11_b22_b33_b42_b52_b62_b72_b82_b92_b100_b112,b11,w=0.1>']
3,BooreAtkinson2008: ['<3,b11_b22_b32_b42_b51_b61_b72_b83_b91_b101_b111,b11,w=0.1>']
4,BooreAtkinson2008: ['<4,b11_b21_b32_b43_b52_b62_b72_b82_b92_b102_b112,b11,w=0.1>']
5,BooreAtkinson2008: ['<5,b11_b23_b32_b43_b52_b62_b73_b82_b93_b101_b113,b11,w=0.1>']
6,BooreAtkinson2008: ['<6,b11_b22_b31_b43_b52_b64_b73_b84_b92_b104_b112,b11,w=0.1>']
7,BooreAtkinson2008: ['<7,b11_b24_b32_b41_b51_b62_b71_b84_b93_b101_b111,b11,w=0.1>']
8,BooreAtkinson2008: ['<8,b11_b21_b32_b43_b52_b62_b73_b82_b92_b103_b113,b11,w=0.1>']
9,BooreAtkinson2008: ['<9,b11_b22_b32_b42_b53_b62_b72_b81_b92_b103_b112,b11,w=0.1>']
}
"""
