import unittest
import numpy
from openquake.commonlib.calculators import calc

aaae = numpy.testing.assert_array_almost_equal


class TestByImt(unittest.TestCase):

    def test_data_by_imt(self):
        dda = {'x': dict(PGA=[1, 2], PGV=[3, 4]),
               'y': dict(PGA=[5, 6], PGV=[7, 8])}

        expected = {'PGA': numpy.array([{'x': 1, 'y': 5}, {'x': 2, 'y': 6}]),
                    'PGV': numpy.array([{'x': 3, 'y': 7}, {'x': 4, 'y': 8}])}

        actual = calc.data_by_imt(dda, ['PGA', 'PGV'], 2)
        for imt in ('PGA', 'PGV'):
            numpy.testing.assert_equal(actual[imt], expected[imt])


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
        actual = calc.compute_hazard_maps(curves, imls, poe)
        aaae(expected, actual)

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
        actual = calc.compute_hazard_maps(curves, imls, poes)
        aaae(expected, actual)
