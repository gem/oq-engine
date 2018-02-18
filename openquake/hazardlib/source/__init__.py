# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
Package :mod:`openquake.hazardlib.source` deals with various types
of seismic sources.
"""
import copy
from openquake.hazardlib import mfd
from openquake.hazardlib.source.rupture import BaseRupture, \
ParametricProbabilisticRupture, NonParametricProbabilisticRupture
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.complex_fault import (
    ComplexFaultSource, MINWEIGHT)
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.non_parametric import NonParametricSeismicSource
from openquake.hazardlib.source.multi import MultiPointSource


def split_source(src):
    """
    :param src: a source to split
    :returns: a list of split sources
    """
    splits = list(src)
    if len(splits) > 1:
        has_serial = hasattr(src, 'serial')
        start = 0
        for split in splits:
            split.src_group_id = src.src_group_id
            split.num_ruptures = split.count_ruptures()
            split.ngsims = src.ngsims
            if has_serial:
                nr = split.num_ruptures
                split.serial = src.serial[start:start + nr]
                start += nr
    return splits
