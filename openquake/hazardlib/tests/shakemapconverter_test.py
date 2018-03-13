import unittest
import numpy
from openquake.baselib.general import writetmp
from openquake.hazardlib.shakemapconverter import get_shakemap_array, example

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32

imt_dt = numpy.dtype(
    [('PGA', F32), ('SA(0.3)', F32), ('SA(1.0)', F32), ('SA(3.0)', F32)])


class ShakemapConverterTestCase(unittest.TestCase):
    def test_nepal(self):
        array = get_shakemap_array(writetmp(example))
        n = 4  # number of sites
        self.assertEqual(len(array), n)
        self.assertEqual(array.dtype.names,
                         ('lon', 'lat', 'vs30', 'val', 'std'))
        dec = 4  # four digits
        aae(array['lon'], [81.7314, 81.7481, 81.7647, 81.7814], dec)
        aae(array['lat'], [30.8735, 30.8735, 30.8735, 30.8735], dec)
        aae(array['vs30'], [400.758, 352.659, 363.687, 301.17], dec)
        val = numpy.array([(0.44, 1.82, 2.80, 1.26),
                           (0.47, 1.99, 3.09, 1.41),
                           (0.47, 1.97, 3.04, 1.38),
                           (0.52, 2.23, 3.51, 1.64)], imt_dt)
        std = numpy.array([(0.53, 0.00, 0.00, 0.00),
                           (0.52, 0.00, 0.00, 0.00),
                           (0.52, 0.00, 0.00, 0.00),
                           (0.50, 0.00, 0.00, 0.0)], imt_dt)
        for imt in imt_dt.names:
            aae(array['val'][imt], val[imt])
            aae(array['std'][imt], std[imt])
