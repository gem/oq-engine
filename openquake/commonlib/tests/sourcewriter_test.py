import os
import unittest
import tempfile
from openquake.commonlib.sourcewriter import write_source_model
from openquake.commonlib.sourceconverter import SourceConverter
from openquake.commonlib.source import parse_source_model
from openquake.commonlib import nrml_examples

NONPARAM = os.path.join(os.path.dirname(__file__), 'data',
                        'nonparametric-source.xml')
MIXED = os.path.join(os.path.dirname(nrml_examples.__file__),
                     'source_model/mixed.xml')


def get_source_model(source_file, inv_time=50.0, simple_mesh_spacing=1.0,
                     complex_mesh_spacing=10.0, mfd_spacing=0.1,
                     area_discretisation=10.0):
    conv = SourceConverter(
        inv_time, simple_mesh_spacing, complex_mesh_spacing, mfd_spacing,
        area_discretisation)
    return parse_source_model(source_file, conv)


class SourceWriterTestCase(unittest.TestCase):

    def check_round_trip(self, fname):
        sources = []
        for trt_model in get_source_model(fname):
            sources.extend(trt_model.sources)

        fd, name = tempfile.mkstemp(suffix='.xml')
        with os.fdopen(fd, 'w'):
            write_source_model(name, sources, 'Test Source Model')
        if open(name).read() != open(fname).read():
            raise Exception('Different files: %s %s' % (name, fname))
        os.remove(name)

    def test_mixed(self):
        self.check_round_trip(MIXED)

    def test_nonparam(self):
        self.check_round_trip(NONPARAM)
