from nhe.mfd import EvenlyDiscretizedMFD

from tests.mfd.base_test import BaseMFDTestCase


class EvenlyDiscretizedMFDMFDConstraintsTestCase(BaseMFDTestCase):
    def test_empty_occurrence_rates(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[]
        )
        self.assertEqual(exc.message, 'at least one bin must be specified')

    def test_negative_occurrence_rate(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[-0.1, 1]
        )
        self.assertEqual(exc.message, 'all occurrence rates must be positive')

    def test_zero_occurrence_rate(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[1, 2, 0]
        )
        self.assertEqual(exc.message, 'all occurrence rates must be positive')

    def test_negative_minimum_magnitude(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=-1, bin_width=2, occurrence_rates=[0.1, 1]
        )
        self.assertEqual(exc.message, 'minimum magnitude must be non-negative')

    def test_negative_bin_width(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=-2, occurrence_rates=[0.1, 1]
        )
        self.assertEqual(exc.message, 'bin width must be positive')


class EvenlyDiscretizedMFDMFDGetRatesTestCase(BaseMFDTestCase):
    def test_zero_min_width(self):
        mfd = EvenlyDiscretizedMFD(min_mag=0, bin_width=1,
                                   occurrence_rates=[1])
        self.assertEqual(mfd.get_annual_occurrence_rates(), [(0, 1)])

    def test(self):
        evenly_discretized = EvenlyDiscretizedMFD(
            min_mag=0.2, bin_width=0.3, occurrence_rates=[2.1, 2.4, 5.3]
        )
        self.assertEqual(evenly_discretized.get_annual_occurrence_rates(),
                         [(0.2, 2.1), (0.5, 2.4), (0.8, 5.3)])
