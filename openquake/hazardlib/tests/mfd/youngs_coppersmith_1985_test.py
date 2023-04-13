
# Copyright (C) 2013-2023 GEM Foundation
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
            min_mag=-4.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'minimum magnitude must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=0.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'minimum magnitude must be positive')

    def test_negative_or_zero_b_val(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=-1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'b value must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=0.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'b value must be positive')

    def test_negative_or_zero_char_mag(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=-6.0, char_rate=0.001,
            bin_width=0.1
        )
        error = 'characteristic magnitude must be positive'
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=0.0, char_rate=0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), error)

    def test_negative_or_zero_char_rate(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=6.0, char_rate=-0.001,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'characteristic rate must be positive')

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=6.0, char_rate=0.0,
            bin_width=0.1
        )
        self.assertEqual(str(exc), 'characteristic rate must be positive')

    def test_bin_width_out_of_valid_range(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=-0.1
        )
        error = 'bin width must be in the range (0, 0.5] to allow for at ' \
                'least one magnitude bin representing the characteristic ' \
                'distribution'
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.0
        )
        self.assertEqual(str(exc), error)

        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=6.0, char_rate=0.001,
            bin_width=0.6
        )
        self.assertEqual(str(exc), error)

    def test_max_mag_GR_too_close_to_min_mag(self):
        exc = self.assert_mfd_error(
            YoungsCoppersmith1985MFD,
            min_mag=4.0, b_val=1.0, char_mag=4.3, char_rate=0.001,
            bin_width=0.1
        )
        error = ('Maximum magnitude of the G-R distribution (char_mag - 0.25) '
                 'must be greater than the minimum magnitude by at least one '
                 'magnitude bin.')
        self.assertEqual(str(exc), error)

    def test_from_total_moment_rate(self):
        total_moment_rate = 6.38119198365e15
        mfd = YoungsCoppersmith1985MFD.from_total_moment_rate(
            min_mag=5.0, b_val=0.85, char_mag=6.75,
            total_moment_rate=total_moment_rate, bin_width=0.1)
        computed_rates = mfd.get_annual_occurrence_rates()

        expected_rates = [(5.05, 0.00017254493595137864),
                          (5.15, 0.000141873805371608),
                          (5.25, 0.00011665469368682727),
                          (5.35, 9.591846446582074e-05),
                          (5.45, 7.88682524012297e-05),
                          (5.55, 6.484884085108228e-05),
                          (5.65, 5.3321482747389806e-05),
                          (5.75, 4.384319727332041e-05),
                          (5.85, 3.6049746708167595e-05),
                          (5.95, 2.9641639263244427e-05),
                          (6.05, 2.4372620016585263e-05),
                          (6.15, 2.004020766858989e-05),
                          (6.25, 1.647791345891117e-05),
                          (6.35, 1.3548843228053625e-05),
                          (6.45, 1.1140436759552141e-05),
                          (6.55, 7.140181717808345e-05),
                          (6.65, 7.140181717808345e-05),
                          (6.75, 7.140181717808345e-05),
                          (6.85, 7.140181717808345e-05),
                          (6.95, 7.140181717808345e-05)]

        computed_total_moment_rate = sum([rate * 10.**(1.5 * mag + 9.05) 
                                          for (mag, rate) in computed_rates])

        numpy.testing.assert_allclose(computed_rates, expected_rates)
        numpy.testing.assert_almost_equal(computed_total_moment_rate,
                                          total_moment_rate)

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
