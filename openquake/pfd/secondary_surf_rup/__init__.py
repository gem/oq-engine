# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Package :mod:`openquake.pfd.secondary_surf_rup` contains implementations of different
surface rupture prediction models
"""

from openquake.pfd.secondary_surf_rup.youngs2003 import Youngs2003SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.petersen2011 import Petersen2011SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.petersen2011 import Petersen2011SecondarySR_default  # noqa: F401
from openquake.pfd.secondary_surf_rup.visini2025 import Visini2025SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.takao2014 import Takao2014SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.ferrario2021 import FerrarioLivio2021SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.takao2013 import Takao2013SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.rodriguez2023 import Rodriguez2023SecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.fixed import FixedSecondarySR  # noqa: F401
from openquake.pfd.secondary_surf_rup.moss2022 import Moss2022SecondarySR  # noqa: F401
