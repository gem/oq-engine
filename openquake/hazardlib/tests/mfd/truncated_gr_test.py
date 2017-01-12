# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=missing-docstring,protected-access

from openquake.hazardlib.mfd import TruncatedGRMFD

from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase


class TruncatedGRMFDConstraintsTestCase(BaseMFDTestCase):
    def test_negative_min_mag(self):
        exc = self.assert_mfd_error(
            TruncatedGRMFD,
            min_mag=-1, max_mag=2, bin_width=0.4, a_val=1, b_val=2
        )
        self.assertEqual(str(exc), 'minimum magnitude -1 must be non-negative')

    def test_min_higher_than_max_mag(self):
        min_mags = [2.4, 6.5, 6.7]
        max_mags = [2, 6.5, 7.3]
        bin_widths = [0.4, 0.1, 1.0]
        for min_mag, max_mag, bin_width in zip(min_mags, max_mags, bin_widths):
            exc = self.assert_mfd_error(
                TruncatedGRMFD,
                min_mag=min_mag, max_mag=max_mag, bin_width=bin_width,
                a_val=1, b_val=0.2
            )
            error = 'maximum magnitude %g must be higher ' % max_mag + \
                    'than minimum magnitude %g by ' % min_mag + \
                    'bin width %g at least' % bin_width
            self.assertEqual(str(exc), error)

    def test_negative_bin_width(self):
        exc = self.assert_mfd_error(
            TruncatedGRMFD,
            min_mag=1, max_mag=2, bin_width=-0.4, a_val=1, b_val=0.2
        )
        self.assertEqual(str(exc), 'bin width -0.4 must be positive')

    def test_non_positive_b_val(self):
        for b_val in [-2, 0]:
            exc = self.assert_mfd_error(
                TruncatedGRMFD,
                min_mag=1, max_mag=2, bin_width=0.4, a_val=1, b_val=b_val
            )
            self.assertEqual(str(exc),
                             'b-value %g must be non-negative' % b_val)


class TruncatedGRMFDMFDGetRatesTestCase(BaseMFDTestCase):
    def _test(self, expected_rates, rate_tolerance, **kwargs):
        mfd = TruncatedGRMFD(**kwargs)
        actual_rates = mfd.get_annual_occurrence_rates()
        self.assertEqual(len(actual_rates), len(expected_rates))
        for i, (mag, rate) in enumerate(actual_rates):
            expected_mag, expected_rate = expected_rates[i]
            self.assertAlmostEqual(mag, expected_mag, delta=1e-14)
            self.assertAlmostEqual(rate, expected_rate, delta=rate_tolerance)
            if i == 0:
                self.assertEqual((mag, mag + 2), mfd.get_min_max_mag())

    def test_1_different_min_mag_and_max_mag(self):
        # pylint: disable=invalid-name
        expected_rates = [
            (5.5, 2.846049894e-5),
            (6.5, 2.846049894e-6),
            (7.5, 2.846049894e-7),
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.0, max_mag=8.0, bin_width=1.0,
                   a_val=0.5, b_val=1.0)

    def test_2_different_min_mag_and_max_mag(self):
        # pylint: disable=invalid-name
        expected_rates = [
            (5.5, 2.846049894e-5),
            (6.5, 2.846049894e-6),
            (7.5, 2.846049894e-7),
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.1, max_mag=7.9, bin_width=1.0,
                   a_val=0.5, b_val=1.0)


class TruncatedGRMFDMFDRoundingTestCase(BaseMFDTestCase):
    # pylint: disable=too-few-public-methods
    def test(self):
        mfd = TruncatedGRMFD(min_mag=0.61, max_mag=0.94, bin_width=0.1,
                             a_val=1, b_val=0.2)
        # mag values should be rounded to 0.6 and 0.9 and there
        # should be three bins with the first having center at 0.65
        min_mag, num_bins = mfd._get_min_mag_and_num_bins()
        self.assertAlmostEqual(min_mag, 0.65)
        self.assertEqual(mfd.get_min_max_mag(), (min_mag, min_mag + 0.2))
        self.assertEqual(num_bins, 3)


class TruncatedGRMFDModificationsTestCase(BaseMFDTestCase):
    def test_get_total_moment_rate(self):
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                             a_val=-17.2, b_val=0.4)
        self.assertAlmostEqual(mfd._get_total_moment_rate(), 1.6140553)

    def test_get_total_moment_rate_when_b_equal_to_1_5(self):
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                             a_val=-9.4, b_val=1.5)
        self.assertAlmostEqual(mfd._get_total_moment_rate(), 1.3400508)

    def test_set_a(self):
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                             a_val=1.5, b_val=0.5)
        mfd._set_a(123.45)
        self.assertAlmostEqual(mfd.a_val, -14.6531141)

    def test_set_a_when_b_equal_to_1_5(self):
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=8.0, bin_width=0.1,
                             a_val=1.5, b_val=1.5)
        mfd._set_a(12.45)
        self.assertAlmostEqual(mfd.a_val, -8.4319519)

    def test_set_a_and_get_total_moment_rate(self):
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=3.0, max_mag=4.0, bin_width=0.1,
                             a_val=4.4, b_val=0.5)
        tmr = mfd._get_total_moment_rate()
        mfd._set_a(tmr)
        self.assertAlmostEqual(mfd.a_val, 4.4)
        self.assertEqual(mfd._get_total_moment_rate(), tmr)

    def test_set_a_and_get_total_moment_rate_when_b_equal_to_1_5(self):
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=2.4, max_mag=5.6, bin_width=0.4,
                             a_val=-0.44, b_val=1.5)
        tmr = mfd._get_total_moment_rate()
        mfd._set_a(tmr)
        self.assertAlmostEqual(mfd.a_val, -0.44)
        self.assertEqual(mfd._get_total_moment_rate(), tmr)

    def test_increment_max_mag(self):
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=7.0, bin_width=0.1,
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
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                             a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_max_mag', {'value': -1})

    def test_set_max_mag(self):
        mfd = TruncatedGRMFD(min_mag=3.5, max_mag=5.5, bin_width=0.5,
                             a_val=1, b_val=1.3)
        mfd.modify('set_max_mag', {'value': 4.2})
        self.assertEqual(mfd.max_mag, 4.2)
        self.assertEqual(mfd.a_val, 1)
        self.assertEqual(mfd.b_val, 1.3)
        self.assertEqual(mfd.min_mag, 3.5)

    def test_set_max_mag_check_constraints(self):
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=3.5, max_mag=5.5, bin_width=0.5,
                             a_val=1, b_val=1.3)
        self.assert_mfd_error(mfd.modify, 'set_max_mag', {'value': 3.6})

    def test_increment_b(self):
        mfd = TruncatedGRMFD(min_mag=4.2, max_mag=6.6, bin_width=0.2,
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
        # pylint: disable=invalid-name
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                             a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_b', {'value': -1})
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                             a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'increment_b', {'value': -2})

    def test_set_ab(self):
        mfd = TruncatedGRMFD(min_mag=2.5, max_mag=3.5, bin_width=0.25,
                             a_val=1, b_val=1.3)
        mfd.modify('set_ab', {'a_val': -4.2, 'b_val': 1.45})
        self.assertEqual(mfd.max_mag, 3.5)
        self.assertEqual(mfd.a_val, -4.2)
        self.assertEqual(mfd.b_val, 1.45)
        self.assertEqual(mfd.min_mag, 2.5)

    def test_set_ab_check_constraints(self):
        mfd = TruncatedGRMFD(min_mag=6.0, max_mag=7.0, bin_width=0.1,
                             a_val=1, b_val=1)
        self.assert_mfd_error(mfd.modify, 'set_ab', {'a_val': 0, 'b_val': 0})
