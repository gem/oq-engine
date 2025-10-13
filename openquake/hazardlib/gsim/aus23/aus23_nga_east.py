# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`NGAEastAUS23_vs3000`
"""
import pathlib
from openquake.hazardlib.gsim.base import add_alias
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE

path = pathlib.Path(__file__).parent



class NGAEastAUS2023GMPE(GMPETable):
    def __init__(self, table_relpath):
        super().__init__(gmpe_table=path / table_relpath)


add_alias("NGAEastAUS23_vs3000", ModifiableGMPE,
          gmpe={'NGAEastAUS2023GMPE': dict(
              table_relpath='NGA-East_Backbone_Model.geometric.3000.mps.hdf5')},
          ceus2020_site_term=dict(ref_vs30=3000, wimp=0.0))
