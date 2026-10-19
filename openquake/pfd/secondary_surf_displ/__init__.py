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
Package :mod:`openquake.pfd.secondary_surf_displ` contains implementations of different
fault displacement prediction models
"""
from openquake.pfd.secondary_surf_displ.youngs2003 import Youngs2003SecondaryFD  # noqa: F401
from openquake.pfd.secondary_surf_displ.takao2013 import Takao2013SecondaryFD  # noqa: F401
from openquake.pfd.secondary_surf_displ.petersen2011 import Petersen2011SecondaryFD  # noqa: F401
from openquake.pfd.secondary_surf_displ.visini2025 import Visini2025SecondaryFD  # noqa: F401
from openquake.pfd.secondary_surf_displ.moss2022 import Moss2022SecondaryFD  # noqa: F401
