# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
This is an example with a simple source model logic tree
sampled 5 times (one path is sampled four times).
The associations (grp_id, gsim) -> rlzs are:
{
0,SadighEtAl1997: ['<0,b2,b1,w=0.2>']
1,SadighEtAl1997: ['<1,b2,b1,w=0.2>']
2,SadighEtAl1997: ['<2,b1,b1,w=0.2>']
3,SadighEtAl1997: ['<3,b2,b1,w=0.2>']
4,SadighEtAl1997: ['<4,b2,b1,w=0.2>']
}
"""
