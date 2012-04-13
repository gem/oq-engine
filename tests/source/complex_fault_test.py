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
from nhlib.source.complex_fault import ComplexFaultSource
from nhlib.geo import Line
from nhlib.geo.surface.simple_fault import SimpleFaultSurface

from tests.source import simple_fault_test


class ComplexFaultSourceIterRupturesTestCase(
        simple_fault_test.SimpleFaultIterRupturesTestCase):
    # test that complex fault sources of simple geometry behave
    # exactly the same as simple fault sources of the same geometry
    def _make_source(self, *args, **kwargs):
        source = super(ComplexFaultSourceIterRupturesTestCase,
                       self)._make_source(*args, **kwargs)
        surface = SimpleFaultSurface.from_fault_data(
            source.fault_trace, source.upper_seismogenic_depth,
            source.lower_seismogenic_depth, source.dip,
            source.rupture_mesh_spacing
        )
        mesh = surface.get_mesh()
        top_edge = Line(list(mesh[0:1]))
        bottom_edge = Line(list(mesh[-1:]))

        return ComplexFaultSource(
            source.source_id, source.name, source.tectonic_region_type,
            source.mfd, source.rupture_mesh_spacing,
            source.magnitude_scaling_relationship, source.rupture_aspect_ratio,
            [top_edge, bottom_edge], source.rake
        )
