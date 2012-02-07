from nhe.mfd import TruncatedGR

from tests.mfd.base_test import BaseMFDTestCase


class TruncatedGRConstraintsTestCase(BaseMFDTestCase):
    def test_negative_min_mag(self):
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=-1, max_mag=2, bin_width=0.4, a_val=1, b_val=2
        )

    def test_min_mag_higher_than_max_mag(self):
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=2.4, max_mag=2, bin_width=0.4, a_val=1, b_val=0.2
        )

    def test_negative_bin_width(self):
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=1, max_mag=2, bin_width=-0.4, a_val=1, b_val=0.2
        )

    def test_non_positive_b_val(self):
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=1, max_mag=2, bin_width=0.4, a_val=1, b_val=-2
        )
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=1, max_mag=2, bin_width=0.4, a_val=1, b_val=0
        )

    def test_equal_min_mag_and_max_mag(self):
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=6.5, max_mag=6.5, bin_width=0.1, a_val=0.5, b_val=1.0
        )
        self.assert_mfd_error(
            TruncatedGR,
            min_mag=6.7, max_mag=7.3, bin_width=1.0, a_val=0.5, b_val=1.0
        )


class TruncatedGRMFDGetRatesTestCase(BaseMFDTestCase):
    def _test(self, expected_rates, rate_tolerance, **kwargs):
        mfd = TruncatedGR(**kwargs)
        actual_rates = mfd.get_annual_occurrence_rates()
        self.assertEqual(len(actual_rates), len(expected_rates))
        for i, (mag, rate) in enumerate(actual_rates):
            expected_mag, expected_rate = expected_rates[i]
            self.assertAlmostEqual(mag, expected_mag, delta=1e-14)
            self.assertAlmostEqual(rate, expected_rate, delta=rate_tolerance)

    def test_1_different_min_mag_and_max_mag(self):
        expected_rates = [
            (5.5, 2.846049894e-5),
            (6.5, 2.846049894e-6),
            (7.5, 2.846049894e-7),
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.0, max_mag=8.0, bin_width=1.0,
                   a_val=0.5, b_val=1.0)

    def test_2_different_min_mag_and_max_mag(self):
        expected_rates = [
            (5.5, 2.846049894e-5),
            (6.5, 2.846049894e-6),
            (7.5, 2.846049894e-7),
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.1, max_mag=7.9, bin_width=1.0,
                   a_val=0.5, b_val=1.0)


class TruncatedGRMFDRoundingTestCase(BaseMFDTestCase):
    def test(self):
        mfd = TruncatedGR(min_mag=0.61, max_mag=0.94, bin_width=0.1,
                          a_val=1, b_val=0.2)
        # mag values should be rounded to 0.6 and 0.9 and there
        # should be three bins with the first having center at 0.65
        min_mag, num_bins = mfd._get_min_mag_and_num_bins()
        self.assertAlmostEqual(min_mag, 0.65)
        self.assertEqual(num_bins, 3)


class TruncatedGRModificationsTestCase(BaseMFDTestCase):
    def test_get_total_moment_rate(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                          a_val=-17.2, b_val=0.4)
        self.assertAlmostEqual(mfd._get_total_moment_rate(), 1.6140553)

    def test_get_total_moment_rate_when_b_equal_to_1_5(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                          a_val=-9.4, b_val=1.5)
        self.assertAlmostEqual(mfd._get_total_moment_rate(),  1.3400508)

    def test_set_a(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                          a_val=1.5, b_val=0.5)
        mfd._set_a(123.45)
        self.assertAlmostEqual(mfd.a_val, -14.6531141)

    def test_set_a_when_b_equal_to_1_5(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                          a_val=1.5, b_val=1.5)
        mfd._set_a(12.45)
        self.assertAlmostEqual(mfd.a_val, -8.4319519)

    def test_set_a_and_get_total_moment_rate(self):
        mfd = TruncatedGR(min_mag=3.0, max_mag=4.0, bin_width=0.1,
                          a_val=4.4, b_val=0.5)
        tmr = mfd._get_total_moment_rate()
        mfd._set_a(tmr)
        self.assertAlmostEqual(mfd.a_val, 4.4)
        self.assertEqual(mfd._get_total_moment_rate(), tmr)

    def test_set_a_and_get_total_moment_rate_when_b_equal_to_1_5(self):
        mfd = TruncatedGR(min_mag=2.4, max_mag=5.6, bin_width=0.4,
                          a_val=-0.44, b_val=1.5)
        tmr = mfd._get_total_moment_rate()
        mfd._set_a(tmr)
        self.assertAlmostEqual(mfd.a_val, -0.44)
        self.assertEqual(mfd._get_total_moment_rate(), tmr)

    def test_increment_max_mag(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                          a_val=-18.2, b_val=0.41)
        old_tmr = mfd._get_total_moment_rate()
        mfd.modify('increment_max_mag', {'value': 1})
        self.assertEqual(mfd.max_mag, 8.0)
        self.assertEqual(mfd.b_val, 0.41)
        self.assertEqual(mfd.min_mag, 6.0)
        self.assertAlmostEqual(mfd._get_total_moment_rate(), old_tmr)
        mfd.modify('increment_max_mag', {'value': -1})
        self.assertAlmostEqual(mfd._get_total_moment_rate(), old_tmr)
        self.assertEqual(mfd.max_mag, 7.0)
        self.assertAlmostEqual(mfd.a_val, -18.2)

    def test_increment_max_mag_check_constraints(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                          a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_max_mag', {'value': -1})

    def test_set_max_mag(self):
        mfd = TruncatedGR(min_mag=3.5, max_mag=5.5, bin_width=0.5,
                          a_val=1, b_val=1.3)
        mfd.modify('set_max_mag', {'value': 4.2})
        self.assertEqual(mfd.max_mag, 4.2)
        self.assertEqual(mfd.a_val, 1)
        self.assertEqual(mfd.b_val, 1.3)
        self.assertEqual(mfd.min_mag, 3.5)

    def test_set_max_mag_check_constraints(self):
        mfd = TruncatedGR(min_mag=3.5, max_mag=5.5, bin_width=0.5,
                          a_val=1, b_val=1.3)
        self.assert_mfd_error(mfd.modify, 'set_max_mag', {'value': 3.6})

    def test_increment_b(self):
        mfd = TruncatedGR(min_mag=4.2, max_mag=6.6, bin_width=0.2,
                          a_val=-20.5, b_val=0.51)
        old_tmr = mfd._get_total_moment_rate()
        mfd.modify('increment_b', {'value': 1.46})
        self.assertEqual(mfd.max_mag, 6.6)
        self.assertEqual(mfd.b_val, 0.51 + 1.46)
        self.assertEqual(mfd.min_mag, 4.2)
        self.assertAlmostEqual(mfd._get_total_moment_rate(), old_tmr)
        mfd.modify('increment_b', {'value': -1.46})
        self.assertAlmostEqual(mfd._get_total_moment_rate(), old_tmr)
        self.assertEqual(mfd.b_val, 0.51)
        self.assertAlmostEqual(mfd.a_val, -20.5)

    def test_increment_b_check_constraints(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                          a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_b', {'value': -1})
        mfd = TruncatedGR(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                          a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_b', {'value': -2})

    def test_set_ab(self):
        mfd = TruncatedGR(min_mag=2.5, max_mag=3.5, bin_width=0.25,
                          a_val=1, b_val=1.3)
        mfd.modify('set_ab', {'a_val': -4.2, 'b_val': 1.45})
        self.assertEqual(mfd.max_mag, 3.5)
        self.assertEqual(mfd.a_val, -4.2)
        self.assertEqual(mfd.b_val, 1.45)
        self.assertEqual(mfd.min_mag, 2.5)

    def test_set_ab_check_constraints(self):
        mfd = TruncatedGR(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                          a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'set_ab', {'a_val': 0, 'b_val': 0})
