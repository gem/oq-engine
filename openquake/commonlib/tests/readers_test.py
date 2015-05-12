import unittest
import tempfile
import numpy
from openquake.baselib.general import writetmp
from openquake.commonlib import InvalidFile
from openquake.commonlib.writers import write_csv
from openquake.commonlib.readers import read_composite_array

fname = writetmp('''\
asset_ref:|S20:,lon:float64:,poe~0.9:float64:,lat:float64:,poe~0.5:float64:,poe~0.1:float64:
a0,8.129850E+01,0.000000E+00,2.910980E+01,0.000000E+00,5.421328E+02
a1,8.308230E+01,0.000000E+00,2.790060E+01,0.000000E+00,2.547904E+02
a2,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,6.538710E+02
a3,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,8.062714E+02
''')

wrong1 = writetmp('''\
asset_ref:|S20:,lon:float64:,poe~0.9:float64:,lat:float64:,poe~0.5:float64:,poe~0.1:float64:
a0,8.129850E+01,0.000000E+00,2.910980E+01,0.000000E+00 5.421328E+02
a1,8.308230E+01,0.000000E+00,2.790060E+01,0.000000E+00,2.547904E+02
a2,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,6.538710E+02
a3,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,8.062714E+02
''')


wrong2 = writetmp('''\
asset_ref:|S20:,lon:float64:,poe~0.9:float64:,lat:float64:,poe~0.5:float64:,poe~0.1:float64:
a0,8.129850E+01,0.000000E+00,2.910980E+01,0.0 0.0,5.421328E+02
a1,8.308230E+01,0.000000E+00,2.790060E+01,0.000000E+00,2.547904E+02
a2,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,6.538710E+02
a3,8.574770E+01,0.000000E+00,2.790150E+01,0.000000E+00,8.062714E+02
''')


class ReadCompositeArrayTestCase(unittest.TestCase):
    def test_read_written(self):
        dtype = numpy.dtype([('a', float), ('b', float, 2)])
        written = numpy.array([(.1, [.2, .3]), (.3, [.4, .5])], dtype)
        with tempfile.NamedTemporaryFile() as dest:
            write_csv(dest.name, written)
            read = read_composite_array(dest.name)
        numpy.testing.assert_equal(read, written)

    def test_read_ok(self):
        got = read_composite_array(fname)
        expected = '''\
[('a0', 81.2985, 0.0, 29.1098, 0.0, 542.1328)
 ('a1', 83.0823, 0.0, 27.9006, 0.0, 254.7904)
 ('a2', 85.7477, 0.0, 27.9015, 0.0, 653.871)
 ('a3', 85.7477, 0.0, 27.9015, 0.0, 806.2714)]'''
        self.assertEqual(str(got), expected)

    def test_read_err1(self):
        with self.assertRaises(InvalidFile) as ctx:
            read_composite_array(wrong1)
        self.assertIn('expected 6 columns, found 5 in file',
                      str(ctx.exception))

    def test_read_err2(self):
        with self.assertRaises(InvalidFile) as ctx:
            read_composite_array(wrong2)
        self.assertIn("Could not cast '0.0 0.0' in file",
                      str(ctx.exception))
