import os
import mock
import unittest
from openquake.commonlib.commands.info import info

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
<RlzsAssoc
0,AkkarBommer2010: ['<0,b1,*_AkkarBommer2010_*_*_*_*_*,w=1.0>']>'''

    EXTRA = '''
input_weight 43.05
max_realizations 1
n_imts 1
n_levels 29.0
n_sites 1
output_weight 29.0'''

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path)
        self.assertEqual(self.EXPECTED, str(p))

    def test_zip_filtering(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path, filtersources=True)
        self.assertEqual(self.EXPECTED + self.EXTRA, str(p))
