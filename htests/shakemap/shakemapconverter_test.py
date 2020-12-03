import os.path
import unittest
import numpy
from openquake.baselib.general import gettemp
from openquake.hazardlib.shakemapconverter import (
    get_shakemap_array, example_pga, example_sa)

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32
CDIR = os.path.dirname(__file__)


class ShakemapConverterTestCase(unittest.TestCase):
    def test_pga(self):
        imt_dt = numpy.dtype([('PGA', F32)])
        array = get_shakemap_array(gettemp(example_pga))
        n = 3  # number of sites
        self.assertEqual(len(array), n)
        self.assertEqual(array.dtype.names,
                         ('lon', 'lat', 'vs30', 'val', 'std'))
        dec = 4  # four digits
        aae(array['lon'], [13.580, 13.5883, 13.5967], dec)
        aae(array['lat'], [39.3103, 39.3103, 39.3103], dec)
        aae(array['vs30'], [603, 603, 603], dec)
        val = numpy.zeros(n, imt_dt)
        std = numpy.array([(0.51,), (0.51,), (0.51,)], imt_dt)
        for imt in imt_dt.names:
            aae(array['val'][imt], val[imt])
            aae(array['std'][imt], std[imt])

    def test_sa(self):
        imt_dt = numpy.dtype([('PGA', F32), ('SA(0.3)', F32),
                              ('SA(1.0)', F32), ('SA(3.0)', F32)])
        array = get_shakemap_array(gettemp(example_sa))
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

    def test_ghorka(self):
        # this is a test considering also the uncertainty
        grid_file = os.path.join(CDIR, 'ghorka_grid.xml')
        uncertainty_file = os.path.join(CDIR, 'ghorka_uncertainty.xml')
        array = get_shakemap_array(grid_file, uncertainty_file)
        aae(array['std']['SA(0.3)'], [0.57, 0.55, 0.56, 0.52])
