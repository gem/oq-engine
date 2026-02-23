# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
Package :mod:`openquake.fdha.primary_surf_rup` contains implementations
of fault displacement prediction models.
"""

from openquake.fdha.primary_surf_rup.youngs2003 import Youngs2003PrimarySR_ExC
from openquake.fdha.primary_surf_rup.youngs2003 import Youngs2003PrimarySR_GB
from openquake.fdha.primary_surf_rup.youngs2003 import Youngs2003PrimarySR_nBR

# from openquake.fdha.primary_surf_rup.wells_coppersmith1993 import ...
# from openquake.fdha.primary_surf_rup.moss_ross2011 import ...
# from openquake.fdha.primary_surf_rup.takao2013 import ...
# from openquake.fdha.primary_surf_rup.moss2013 import ...
# from openquake.fdha.primary_surf_rup.yang2021 import ...
# from openquake.fdha.primary_surf_rup.pizza2023 import ...
# from openquake.fdha.primary_surf_rup.mammarella2024 import ...
#from openquake.fdha.primary_surf_rup.fixed import FixedPrimarySR