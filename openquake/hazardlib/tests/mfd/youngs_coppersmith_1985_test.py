# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
from openquake.hazardlib.mfd import YoungsCoppersmith1985MFD

from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase

import numpy


class YoungsCoppersmith1985MFDConstraintsTestCase(BaseMFDTestCase):
    def test_negative_or_zero_min_mag(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=-4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'minimum magnitude must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=0.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'minimum magnitude must be positive')

    def test_negative_or_zero_b_val(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=-1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'b value must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=0.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'b value must be positive')

    def test_negative_or_zero_char_mag(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=-6.0, char_rate=0.001,
            bin_width=0.1
        )
        error = 'characteristic magnitude must be positive'
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=0.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), error)

    def test_negative_or_zero_char_rate(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=-0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'characteristic rate must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.0,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'characteristic rate must be positive')

    def test_bin_width_out_of_valid_range(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=-0.1
        )
        error = 'bin width must be in the range (0, 0.5] to allow for at ' \
                'least one magnitude bin representing the characteristic ' \
                'distribution'
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.0
        )
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.6
        )
        self.assertEqual(str(exc), error)

    def test_max_mag_GR_too_close_to_min_mag(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, a_val=2.0, b_val=1.0, char_mag=4.3, char_rate=0.001,
            bin_width=0.1
        )
        error = ('Maximum magnitude of the G-R distribution (char_mag - 0.25) '
                 'must be greater than the minimum magnitude by at least one '
                 'magnitude bin.')
        self.assertEqual(str(exc), error)

    def test_rate_char_mag_not_equal_rate_char_mag_less_1_pt_25(self):
        # Given the parameters below:
        # min = 5.0
        # b_val = 1
        # char_mag = 6.5
        # char_rate = 0.001
        # we can compute an a_val that satisfies the condition using the
        # following equations
        # a_incr = b_val * (char_mag - 1.25) + log10(char_rate / 0.5)
        # a_val = a_incr - log10(b_val * log(10))
        # if we add 1e-4 to a_val, this raises the error
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=5.0, a_val=2.1888143 + 1e-4, b_val=1.0, char_mag=6.5,
            char_rate=0.001, bin_width=0.1
        )
        error = 'Rate of events at the characteristic magnitude is not ' \
                'equal to the rate of events for magnitude equal to ' \
                'char_mag - 1.25'
        self.assertEqual(str(exc), error)

    def test_from_total_moment_rate(self):
        mfd = YoungsCoppersmith1985MFD.from_total_moment_rate(
            min_mag=5.0, b_val=0.85, char_mag=6.75,
            total_moment_rate=6.38119198365e15, bin_width=0.1
        )
        computed_rates = mfd.get_annual_occurrence_rates()
        expected_rates = [(5.05, 0.00017054956240777723),
                          (5.15, 0.00014023312414148282),
                          (5.25, 0.00011530565560445073),
                          (5.35, 9.480922781808791e-05),
                          (5.45, 7.795619072057948e-05),
                          (5.55, 6.409890483786924e-05),
                          (5.65, 5.27048533725948e-05),
                          (5.75, 4.333617830215377e-05),
                          (5.85, 3.5632854085742086e-05),
                          (5.95, 2.9298852368637887e-05),
                          (6.05, 2.4090766011996856e-05),
                          (6.15, 1.9808455284958928e-05),
                          (6.25, 1.6287356764862893e-05),
                          (6.35, 1.3392159386974224e-05),
                          (6.45, 1.1011604622859124e-05),
                          (6.55, 7.057610011964502e-05),
                          (6.65, 7.057610011964502e-05),
                          (6.75, 7.057610011964502e-05),
                          (6.85, 7.057610011964502e-05),
                          (6.95, 7.057610011964502e-05)]
        numpy.testing.assert_allclose(computed_rates, expected_rates)

        self.assertEqual((5.05, 6.95), mfd.get_min_max_mag())

    def test_from_characteristic_rate(self):
        mfd = YoungsCoppersmith1985MFD.from_characteristic_rate(
            min_mag=5.0, b_val=0.85, char_mag=6.75,
            char_rate=0.000125, bin_width=0.1
        )
        computed_rates = mfd.get_annual_occurrence_rates()
        expected_rates = [(5.05, 6.041335597980433e-05),
                          (5.15, 4.967443791302958e-05),
                          (5.25, 4.084444146424117e-05),
                          (5.35, 3.358404178516568e-05),
                          (5.45, 2.7614231513367556e-05),
                          (5.55, 2.270559889580352e-05),
                          (5.65, 1.8669511804720695e-05),
                          (5.75, 1.535086885953161e-05),
                          (5.85, 1.2622139090051389e-05),
                          (5.95, 1.0378461093404372e-05),
                          (6.05, 8.533613351813384e-06),
                          (6.15, 7.016700856018683e-06),
                          (6.25, 5.7694307057387526e-06),
                          (6.35, 4.74387199217263e-06),
                          (6.45, 3.900613877853681e-06),
                          (6.55, 2.5e-05),
                          (6.65, 2.5e-05),
                          (6.75, 2.5e-05),
                          (6.85, 2.5e-05),
                          (6.95, 2.5e-05)]
        numpy.testing.assert_allclose(computed_rates, expected_rates)

        self.assertEqual((5.05, 6.95), mfd.get_min_max_mag())
