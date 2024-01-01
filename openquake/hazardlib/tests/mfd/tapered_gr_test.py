# The Hazard Library
# Copyright (C) 2012-2020 GEM Foundation
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

from openquake.hazardlib.mfd import TaperedGRMFD

from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase

class TaperedGRMFDConstraintsTestCase(BaseMFDTestCase):
    def test_negative_min_mag(self):
        exc = self.assert_mfd_error(
            TaperedGRMFD,
            min_mag=-1, max_mag=2, corner_mag=1.5, bin_width=0.4, a_val=1, 
            b_val=2
        )
        self.assertEqual(str(exc), 'minimum magnitude -1 must be non-negative')

    def test_min_higher_than_max_mag(self):
        min_mags = [2.4, 6.5, 6.7]
        max_mags = [2, 6.5, 7.3]
        bin_widths = [0.4, 0.1, 1.0]
        for min_mag, max_mag, bin_width in zip(min_mags, max_mags, bin_widths):
            exc = self.assert_mfd_error(
                TaperedGRMFD,
                min_mag=min_mag, max_mag=max_mag, corner_mag=1.5,
                bin_width=bin_width, a_val=1, b_val=0.2
            )
            error = 'maximum magnitude %g must be higher ' % max_mag + \
                    'than minimum magnitude %g by ' % min_mag + \
                    'bin width %g at least' % bin_width
            self.assertEqual(str(exc), error)

    def test_corner_mag_higher_than_min_plus_bin_width(self):
        min_mag = 1.
        corner_mag = 1.5
        bin_width = 1.
        exc = self.assert_mfd_error(
            TaperedGRMFD,
            min_mag=min_mag, max_mag=3., corner_mag=corner_mag,
            bin_width=bin_width, a_val=1., b_val=0.2
        )

        error = "corner magnitude %g must be higher " % corner_mag + \
                "than minimum magnitude %g " % min_mag + \
                "by bin width %g at least" % bin_width
        self.assertEqual(str(exc), error)

    def test_negative_bin_width(self):
        exc = self.assert_mfd_error(
            TaperedGRMFD,
            min_mag=1, max_mag=2, corner_mag=1.5, bin_width=-0.4, a_val=1.,
            b_val=0.2
        )
        self.assertEqual(str(exc), 'bin width -0.4 must be positive')

    def test_non_positive_b_val(self):
        for b_val in [-2, 0]:
            exc = self.assert_mfd_error(
                TaperedGRMFD,
                min_mag=1, max_mag=2, corner_mag=1.5, bin_width=0.4,
                a_val=1, b_val=b_val
            )
            self.assertEqual(str(exc),
                             'b-value %g must be non-negative' % b_val)


class TaperedGRMFDMFDGetRatesTestCase(BaseMFDTestCase):
    def _test(self, expected_rates, rate_tolerance, **kwargs):
        mfd = TaperedGRMFD(**kwargs)
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
            (5.5, 2.8472710716199842e-05),
            (6.5, 2.879666945859692e-06),
            (7.5, 2.640735968005631e-07)
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.0, max_mag=8.0, corner_mag=7.5, bin_width=1.0,
                   a_val=0.5, b_val=1.0)

    def test_2_different_min_mag_and_max_mag(self):
        # pylint: disable=invalid-name
        expected_rates = [
            (5.5, 2.8472710716199842e-05),
            (6.5, 2.879666945859692e-06),
            (7.5, 2.640735968005631e-07)
        ]
        self._test(expected_rates=expected_rates, rate_tolerance=1e-14,
                   min_mag=5.1, max_mag=7.9, corner_mag=7.5, bin_width=1.0,
                   a_val=0.5, b_val=1.0)


class TaperedGRMFDMFDRoundingTestCase(BaseMFDTestCase):
    # pylint: disable=too-few-public-methods
    def test(self):
        mfd = TaperedGRMFD(min_mag=0.61, max_mag=0.94, corner_mag=7.5,
                            bin_width=0.1, a_val=1, b_val=0.2)
        # mag values should be rounded to 0.6 and 0.9 and there
        # should be three bins with the first having center at 0.65
        min_mag, num_bins = mfd._get_min_mag_and_num_bins()
        self.assertAlmostEqual(min_mag, 0.65)
        self.assertEqual(mfd.get_min_max_mag(), (min_mag, min_mag + 0.2))
        self.assertEqual(num_bins, 3)