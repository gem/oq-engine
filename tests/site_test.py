import unittest

from nhe.site import Site
from nhe.geo.point import Point


class SiteTestCase(unittest.TestCase):
    def _assert_creation(self, error=None, **kwargs):
        default_kwargs = {
            'location': Point(10, 20),
            'vs30': 10,
            'vs30measured': False,
            'z1pt0': 20,
            'z2pt5': 30
        }
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        if error is not None:
            with self.assertRaises(ValueError) as ar:
                Site(**kwargs)
            self.assertEqual(ar.exception.message, error)
        else:
            site = Site(**kwargs)
            for attr in kwargs:
                self.assertEqual(getattr(site, attr), kwargs[attr])

    def test_wrong_vs30(self):
        error = 'vs30 must be positive'
        self._assert_creation(error=error, vs30=0)
        self._assert_creation(error=error, vs30=-1)

    def test_wrong_z1pt0(self):
        error = 'z1pt0 must be positive'
        self._assert_creation(error=error, z1pt0=0)
        self._assert_creation(error=error, z1pt0=-1)

    def test_wrong_z2pt5(self):
        error = 'z2pt5 must be positive'
        self._assert_creation(error=error, z2pt5=0)
        self._assert_creation(error=error, z2pt5=-1)

    def test_successful_creation(self):
        self._assert_creation()
