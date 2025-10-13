# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
import logging
from openquake.baselib import parallel
from openquake.hazardlib.source.rupture import (  # noqa
    BaseRupture,
    ParametricProbabilisticRupture,
    NonParametricProbabilisticRupture
)
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.source.point import PointSource  # noqa
from openquake.hazardlib.source.area import AreaSource  # noqa
from openquake.hazardlib.source.simple_fault import SimpleFaultSource  # noqa
from openquake.hazardlib.source.complex_fault import ComplexFaultSource, MINWEIGHT  # noqa
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource  # noqa
from openquake.hazardlib.source.non_parametric import NonParametricSeismicSource   # noqa
from openquake.hazardlib.source.multi_point import MultiPointSource   # noqa
from openquake.hazardlib.source.kite_fault import KiteFaultSource  # noqa
from openquake.hazardlib.source.multi_fault import MultiFaultSource  # noqa


def splittable(src):
    """
    :returns: True if the source is splittable, False otherwise
    """
    return (src.__class__.__iter__ is not BaseSeismicSource.__iter__
            and getattr(src, 'mutex_weight', 1) == 1 and src.splittable)


def check_complex_fault(src):
    """
    Make sure all the underlying rupture surfaces are valid
    """
    for rup in src.iter_ruptures():
        try:
            rup.surface.get_dip()
        except Exception as exc:
            yield '%s: %s' % (src.source_id, exc)
            break


def check_complex_faults(srcs):
    """
    Check the geometries of the passed complex fault sources
    """
    sources = [(src,) for src in srcs if src.code == b'C']
    for err in parallel.Starmap(check_complex_fault, sources):
        logging.error(err)
    parallel.Starmap.shutdown()
