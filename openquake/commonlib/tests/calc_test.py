import os
import tempfile
import unittest
import numpy
from openquake.baselib import hdf5, general
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import (
    SourceConverter, RuptureConverter)
from openquake.commonlib import nrml_examples, calc

NRML_DIR = os.path.dirname(nrml_examples.__file__)
MIXED_SRC_MODEL = os.path.join(NRML_DIR, 'source_model/mixed.xml')
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


class SerializeRuptureTestCase(unittest.TestCase):
    def test(self):
        groups = nrml.SourceModelParser(converter).parse_groups(
            MIXED_SRC_MODEL)
        ([point], [cmplx], [area, simple],
         [char_simple, char_complex, char_multi]) = groups
        fh, self.path = tempfile.mkstemp(suffix='.hdf5')
        os.close(fh)
        print('Writing on %s' % self.path)
        self.i = 0
        self.sids = numpy.array([0], numpy.uint32)
        self.events = numpy.array([(0, 1, 1, 0)], calc.event_dt)
        self.write_read(point)
        self.write_read(char_simple)
        self.write_read(char_complex)
        self.write_read(char_multi)

    def write_read(self, src):
        with hdf5.File(self.path, 'r+') as f:
            for rup in src.iter_ruptures():
                rup.seed = 0
                ebr = calc.EBRupture(
                    rup, self.sids, self.events, src.source_id, 0, self.i)
                f[str(self.i)] = ebr
                self.i += 1
        with hdf5.File(self.path, 'r') as f:
            for key in f:
                f[key]

    def test_planar(self):
        fh, self.path = tempfile.mkstemp(suffix='.hdf5')
        os.close(fh)
        sids = numpy.array([0], numpy.uint32)
        events = numpy.array([(0, 1, 1, 0)], calc.event_dt)
        [rup_node] = nrml.read(planar)
        conv = RuptureConverter(1.0, 1.0)
        rup = conv.convert_node(rup_node)
        rup.seed = 0
        ebr1 = calc.EBRupture(rup, sids, events, '*', 0, 0)
        with hdf5.File(self.path, 'w') as f:
            f['ebr'] = ebr1
        with hdf5.File(self.path, 'r') as f:
            ebr2 = f['ebr']
        [s1] = ebr1.rupture.surface.surfaces
        [s2] = ebr2.rupture.surface.surfaces
        self.assertEqual(s1.__class__.__name__, s2.__class__.__name__)


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
