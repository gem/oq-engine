import unittest
from openquake.commonlib.calculators.calc import data_by_imt


class TestByImt(unittest.TestCase):

    def test_data_by_imt(self):
        dda = {'x': dict(PGA=[1, 2], PGV=[3, 4]),
               'y': dict(PGA=[5, 6], PGV=[7, 8])}

        expected = {'PGA': [{'x': 1, 'y': 5}, {'x': 2, 'y': 6}],
                    'PGV': [{'x': 3, 'y': 7}, {'x': 4, 'y': 8}]}

        self.assertEqual(data_by_imt(dda, ['PGA', 'PGV'], 2), expected)
