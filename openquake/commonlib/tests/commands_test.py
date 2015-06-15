import os
import mock
import shutil
import tempfile
import unittest
from openquake.commonlib.commands.info import info
from openquake.commonlib.commands.reduce import reduce
from openquake.qa_tests_data.classical_risk import case_3

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class Print(object):
    def __init__(self):
        self.lst = []

    def __call__(self, *args):
        self.lst.append(' '.join(map(str, args)))

    def __str__(self):
        return '\n'.join(self.lst)

    @classmethod
    def patch(cls):
        return mock.patch('__builtin__.print', cls())


class InfoTestCase(unittest.TestCase):
    EXPECTED = '''Reading the source model...
<CompositionInfo
b1, x15.xml, trt=[0]: 1 realization(s)>
See https://github.com/gem/oq-risklib/blob/master/docs/effective-realizations.rst for an explanation
<RlzsAssoc(1)
0,AkkarBommer2010: ['<0,b1,*_AkkarBommer2010_*_*_*_*_*,w=1.0>']>'''

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path)
        self.assertEqual(self.EXPECTED, str(p))

    def test_zip_filtering(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path, filtersources=True)
        exp = self.EXPECTED + '''
c_matrix 232 B
input_weight 1
max_realizations 1
n_imts 1
n_levels 29.0
n_sites 1
n_sources 1
output_weight 29.0'''
        self.assertEqual(exp, str(p))

    def test_zip_splitting(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path, splitsources=True)
        exp = self.EXPECTED + '''
c_matrix 232 B
input_weight 1
max_realizations 1
n_imts 1
n_levels 29.0
n_sites 1
n_sources 1
output_weight 29.0'''
        self.assertEqual(exp, str(p))


class ReduceTestCase(unittest.TestCase):
    TESTDIR = os.path.dirname(case_3.__file__)

    def test_exposure(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'exposure_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'exposure_model.xml'), dest)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 182 nodes out of 375', str(p))
        shutil.rmtree(tempdir)

    def test_source_model(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'source_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'source_model.xml'), tempdir)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 196 nodes out of 398', str(p))
        shutil.rmtree(tempdir)
