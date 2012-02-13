import unittest

from nhe.geo.nodalplane import NodalPlane


class NodalPlaneTestCase(unittest.TestCase):
    def _test_broken_input(self, broken_parameter, **kwargs):
        with self.assertRaises(ValueError) as ae:
            NodalPlane(**kwargs)
        self.assertTrue(ae.exception.message.startswith(broken_parameter),
                        ae.exception.message)

        checker = getattr(NodalPlane, 'check_%s' % broken_parameter)
        with self.assertRaises(ValueError) as ae:
            checker(kwargs[broken_parameter])
        self.assertTrue(ae.exception.message.startswith(broken_parameter),
                        ae.exception.message)

    def test_strike_out_of_range(self):
        self._test_broken_input('strike', strike=-0.1, dip=1, rake=0)
        self._test_broken_input('strike', strike=360.1, dip=1, rake=0)

    def test_dip_out_of_range(self):
        self._test_broken_input('dip', strike=0, dip=-0.1, rake=0)
        self._test_broken_input('dip', strike=0, dip=0, rake=0)
        self._test_broken_input('dip', strike=0, dip=90.1, rake=0)

    def test_rake_out_of_range(self):
        self._test_broken_input('rake', strike=0, dip=1, rake=-180.1)
        self._test_broken_input('rake', strike=0, dip=1, rake=-180)
        self._test_broken_input('rake', strike=0, dip=1, rake=180.1)

    def test_corner_cases(self):
        np = NodalPlane(strike=0, dip=0.001, rake=-180 + 1e-5)
        self.assertEqual((np.strike, np.dip, np.rake), (0, 0.001, -180 + 1e-5))
        np = NodalPlane(strike=360, dip=90, rake=+180)
        self.assertEqual((np.strike, np.dip, np.rake), (360, 90, +180))
