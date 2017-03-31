import unittest
import numpy
from openquake.baselib import general
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.commonlib import calc

converter = SourceConverter(
    investigation_time=50.,
    rupture_mesh_spacing=1,  # km
    complex_fault_mesh_spacing=1,  # km
    width_of_mfd_bin=1.,  # for Truncated GR MFDs
    area_source_discretization=1.,  # km
)
aaae = numpy.testing.assert_array_almost_equal

planar = general.writetmp('''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <singlePlaneRupture>
        <magnitude>6.8</magnitude>
        <rake>0.0</rake>
        <hypocenter lat="37.5349" lon="-121.9033" depth="8.0"/>
        <planarSurface>
           <topLeft depth="2.4" lat="37.5349" lon="-121.9033"/>
           <topRight depth="2.4" lat="37.932" lon="-122.259"/>
           <bottomLeft depth="9.4" lat="37.5349" lon="-121.9033"/>
           <bottomRight depth="9.4" lat="37.932" lon="-122.259"/>
        </planarSurface>
    </singlePlaneRupture>
</nrml>''')


class HazardMapsTestCase(unittest.TestCase):

    def test_compute_hazard_map(self):
        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poe = 0.2

        expected = [[0.00847798, 0.00664814, 0.0098, 0, 0.007]]
        actual = calc.compute_hazard_maps(numpy.array(curves), imls, poe)
        aaae(expected, actual.T)

    def test_compute_hazard_map_multi_poe(self):
        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poes = [0.1, 0.2]
        expected = [
            [0.0098, 0.00792555, 0.0098, 0.005,  0.0098],
            [0.00847798, 0.00664814, 0.0098, 0, 0.007]
        ]
        actual = calc.compute_hazard_maps(numpy.array(curves), imls, poes)
        aaae(expected, actual.T)
