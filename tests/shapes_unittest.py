import unittest

from openquake import shapes

class ShapesTestCase(unittest.TestCase):

    def test_safe_float(self):
        """
        """
        in_values = (29.000000000000004, -121.00000009, -121.00000001, 121.00000005, 121.00000006)
        out_values = (29.0, -121.0000001, -121.0, 121.0, 121.0000001)

        for i, val in enumerate(in_values):
            self.assertEqual(out_values[i], shapes.safe_float(in_values[i]))
