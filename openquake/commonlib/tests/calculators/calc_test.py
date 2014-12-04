import unittest
import numpy
from openquake.commonlib.calculators.calc import data_by_imt


class TestByImt(unittest.TestCase):

    def test_data_by_imt(self):
        dda = {'x': dict(PGA=[1, 2], PGV=[3, 4]),
               'y': dict(PGA=[5, 6], PGV=[7, 8])}

        expected = {'PGA': numpy.array([{'x': 1, 'y': 5}, {'x': 2, 'y': 6}]),
                    'PGV': numpy.array([{'x': 3, 'y': 7}, {'x': 4, 'y': 8}])}

        actual = data_by_imt(dda, ['PGA', 'PGV'], 2)
        for imt in ('PGA', 'PGV'):
            numpy.testing.assert_equal(actual[imt], expected[imt])
