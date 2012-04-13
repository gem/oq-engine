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
from nhlib.geo import Line, Point
from nhlib.geo.surface.simple_fault import SimpleFaultSurface
from nhlib.scalerel.peer import PeerMSR

from tests.source import simple_fault_test
from tests.source import _complex_fault_test_data as test_data


class ComplexFaultSourceSimpleGeometryIterRupturesTestCase(
        simple_fault_test.SimpleFaultIterRupturesTestCase):
    # test that complex fault sources of simple geometry behave
    # exactly the same as simple fault sources of the same geometry
    def _make_source(self, *args, **kwargs):
        source = super(ComplexFaultSourceSimpleGeometryIterRupturesTestCase,
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

class ComplexFaultSourceIterRupturesTestCase(
        simple_fault_test._BaseFaultSourceTestCase):
    def _make_source(self, mfd, aspect_ratio, rupture_mesh_spacing, edges):
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        edges = [Line([Point(*coords) for coords in edge])
                 for edge in edges]
        return ComplexFaultSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            edges, rake
        )

    def test_1(self):
        self._test_ruptures(test_data.TEST1_RUPTURES, test_data.TEST1_MFD,
                            test_data.TEST1_RUPTURE_ASPECT_RATIO,
                            rupture_mesh_spacing=test_data.TEST1_MESH_SPACING,
                            edges=test_data.TEST1_EDGES)

    def test_2(self):
        self._test_ruptures(test_data.TEST2_RUPTURES, test_data.TEST2_MFD,
                            test_data.TEST2_RUPTURE_ASPECT_RATIO,
                            rupture_mesh_spacing=test_data.TEST2_MESH_SPACING,
                            edges=test_data.TEST2_EDGES)

    def test_3(self):
        self._test_ruptures(test_data.TEST3_RUPTURES, test_data.TEST3_MFD,
                            test_data.TEST3_RUPTURE_ASPECT_RATIO,
                            rupture_mesh_spacing=test_data.TEST3_MESH_SPACING,
                            edges=test_data.TEST3_EDGES)

    def test_4(self):
        self._test_ruptures(test_data.TEST4_RUPTURES, test_data.TEST4_MFD,
                            test_data.TEST4_RUPTURE_ASPECT_RATIO,
                            rupture_mesh_spacing=test_data.TEST4_MESH_SPACING,
                            edges=test_data.TEST4_EDGES)
