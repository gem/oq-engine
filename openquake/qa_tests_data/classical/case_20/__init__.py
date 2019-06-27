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
This is an example with a source model logic tree containing uncertainties
on the fault geometry. The GMPE is fixed as the Sadigh et al. 1997 model.

The source model contains three faults SFLT1 (simple fault), COMFLT1 (complex
fault) and CHAR1 (characteristic fault). Two geometries are defined for
SFLT1 (sg1, sg2), two for COMFLT1 (cog1, cog2) and three for CHAR1
(char_simple, char_complex, char_planar)

12 curves output:
*_sg1_cog1_char_simple-*
*_sg1_cog1_char_complex-*
*_sg1_cog1_char_planar-*
*_sg1_cog2_char_simple-*
*_sg1_cog2_char_complex-*
*_sg1_cog2_char_planar-*
*_sg2_cog1_char_simple-*
*_sg2_cog1_char_complex-*
*_sg2_cog1_char_planar-*
*_sg2_cog2_char_simple-*
*_sg2_cog2_char_complex-*
*_sg2_cog2_char_planar-*
"""
