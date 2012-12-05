# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Package :mod:`nhlib.gsim` contains base and specific implementations of
ground shaking intensity models. See :mod:`nhlib.gsim.base`.
"""
from nhlib.gsim.base import GMPE, IPE, CoeffsTable
# the import is needed otherwise GMPE.__subclasses__() is empty
from nhlib.gsim import (
    abrahamson_silva_2008, akkar_cagnan_2010, boore_atkinson_2008,
    chiou_youngs_2008, sadigh_1997, chiou_youngs_2008, zhao_2006)


AVAILABLE_GSIMS = [cls.__name__ for cls in GMPE.__subclasses__()]
