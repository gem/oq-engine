import unittest

from nhe.mfd import EvenlyDiscretized, MFDError


class BaseConstraintsTestCase(unittest.TestCase):
    def assert_constraint_violation(self, mfd_class, *args, **kwargs):
        self.assertRaises(MFDError, mfd_class, *args, **kwargs)


class EvenlyDiscretizedMFDConstraintsTestCase(BaseConstraintsTestCase):
    def test_empty_occurrence_rates(self):
        self.assert_constraint_violation(
            EvenlyDiscretized,
            min_mag=1, bin_width=2, occurrence_rates=[]
        )

    def test_negative_occurrence_rate(self):
        self.assert_constraint_violation(
            EvenlyDiscretized,
            min_mag=1, bin_width=2, occurrence_rates=[-0.1, 1]
        )

    def test_negative_minimum_magnitude(self):
        self.assert_constraint_violation(
            EvenlyDiscretized,
            min_mag=-1, bin_width=2, occurrence_rates=[0.1, 1]
        )

    def test_negative_bin_width(self):
        self.assert_constraint_violation(
            EvenlyDiscretized,
            min_mag=1, bin_width=-2, occurrence_rates=[0.1, 1]
        )


class EvenlyDiscretizedMFDGetRatesTestCase(unittest.TestCase):
    def test_zero_min_width(self):
        mfd = EvenlyDiscretized(min_mag=0, bin_width=1, occurrence_rates=[1])
        self.assertEqual(mfd.get_annual_occurrence_rates(), [(0, 1)])

    def test(self):
        evenly_discretized = EvenlyDiscretized(
            min_mag=0.2, bin_width=0.3, occurrence_rates=[2.1, 2.4, 5.3]
        )
        self.assertEqual(evenly_discretized.get_annual_occurrence_rates(),
                         [(0.2, 2.1), (0.5, 2.4), (0.8, 5.3)])
