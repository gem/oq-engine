import os
import tempfile
import unittest
import numpy
from openquake.baselib import hdf5
from openquake.commonlib import nrml_examples, calc, source
from openquake.commonlib.sourceconverter import SourceConverter

NRML_DIR = os.path.dirname(nrml_examples.__file__)
MIXED_SRC_MODEL = os.path.join(NRML_DIR, 'source_model/mixed.xml')
parser = source.SourceModelParser(SourceConverter(
    investigation_time=50.,
    rupture_mesh_spacing=1,  # km
    complex_fault_mesh_spacing=1,  # km
    width_of_mfd_bin=1.,  # for Truncated GR MFDs
    area_source_discretization=1.,  # km
))


class SerializeRuptureTestCase(unittest.TestCase):
    def test(self):
        groups = parser.parse_groups(MIXED_SRC_MODEL)
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
                ebr = calc.EBRupture(
                    rup, self.sids, self.events, src.source_id, 0, self.i)
                f[str(self.i)] = ebr
                self.i += 1
        with hdf5.File(self.path, 'r') as f:
            for key in f:
                f[key]
