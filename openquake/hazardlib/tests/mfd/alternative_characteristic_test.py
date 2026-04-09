# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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

import unittest

from openquake.hazardlib.mfd.alternative_characteristic_mfd import (
    AlternativeCharacteristicMFD)
from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase


# AC specific params are taken from BC Hydro AC memo (pp. 2 bottom of page)
TEST_MFD_INPUTS = dict(min_mag=4.0, # Generic testing value
                       max_mag=7.5, # Generic testing value
                       bin_width=0.1, # Generic testing value
                       b_GR=0.8,
                       b_AC=0.3,
                       gamma=0.96,
                       delta_m_AC=1.0,
                       total_rate=5.0 # Generic testing value not from report
                       )


class AlternativeCharacteristicMFDConstraintsTestCase(BaseMFDTestCase):
    """
    Tests that invalid inputs raise appropriate errors.
    """
    def test_negative_bin_width(self):
        # Bin width must be positive
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS, 'bin_width': -0.1})
        self.assertEqual(str(exc), 'bin width -0.1 must be positive')

    def test_negative_min_mag(self):
        # Min mag must be non-negative
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS, 'min_mag': -1})
        self.assertEqual(str(exc), 'minimum magnitude -1 must be non-negative')

    def test_max_mag_too_low(self):
        # Max mag must exceed min_mag
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS,
                                       'min_mag': 5.0, 'max_mag': 5.0})
        self.assertIn('must be higher than', str(exc))

    def test_negative_b_GR(self):
        # b_GR must be positive
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS, 'b_GR': -0.5})
        self.assertEqual(str(exc), 'b_GR -0.5 must be positive')

    def test_negative_b_AC(self):
        # b_AC must be positive
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS, 'b_AC': -0.1})
        self.assertEqual(str(exc), 'b_AC -0.1 must be positive')

    def test_b_AC_equals_c_val(self):
        # b_AC == c (1.5) causes the moment rate integral in the
        # AC zone to diverge (division by zero in the TMR formula)
        exc = self.assert_mfd_error(AlternativeCharacteristicMFD,
                                    **{**TEST_MFD_INPUTS, 'b_AC': 1.5})
        self.assertIn('b_AC cannot equal c_val', str(exc))

    def test_gamma_out_of_range(self):
        # Gamma must be strictly between 0 and 1; at the boundaries
        # the moment-rate partitioning ratio becomes undefined
        for gamma in [0.0, 1.0, -0.1, 1.5]:
            exc = self.assert_mfd_error(
                AlternativeCharacteristicMFD,
                **{**TEST_MFD_INPUTS, 'gamma': gamma})
            self.assertIn('must be between 0 and 1', str(exc))

    def test_negative_delta_m_AC(self):
        # delta_m_AC defines the width of the AC zone and must
        # be positive for the two-zone decomposition to be valid
        exc = self.assert_mfd_error(
            AlternativeCharacteristicMFD,
            **{**TEST_MFD_INPUTS, 'delta_m_AC': -0.5})
        self.assertEqual(str(exc), 'delta_m_AC -0.5 must be positive')

    def test_delta_m_AC_too_large(self):
        # AC zone too wide so it pushes the boundary below
        # min_mag which leaves no room for the GR zone
        exc = self.assert_mfd_error(
            AlternativeCharacteristicMFD,
            **{**TEST_MFD_INPUTS, 'delta_m_AC': 4.0})
        self.assertIn('AC zone boundary', str(exc))

    def test_negative_total_rate(self):
        # Total rate must be positive
        exc = self.assert_mfd_error(
            AlternativeCharacteristicMFD,
            **{**TEST_MFD_INPUTS, 'total_rate': -1.0})
        self.assertEqual(str(exc), 'total_rate -1 must be positive')


class AlternativeCharacteristicMFDModificationsTestCase(BaseMFDTestCase):
    """
    Tests for MDF modification.
    """
    def test_set_max_mag(self):
        # set_max_mag replaces max_mag directly
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        acmfd.modify('set_max_mag', {'value': 8.0})
        self.assertEqual(acmfd.max_mag, 8.0)

    def test_set_bGR(self):
        # set_bGR replaces b_GR directly
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        acmfd.modify('set_bGR', {'b_val': 1.0})
        self.assertEqual(acmfd.b_GR, 1.0)

    def test_set_bAC(self):
        # set_bAC replaces b_AC directly
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        acmfd.modify('set_bAC', {'b_val': 0.5})
        self.assertEqual(acmfd.b_AC, 0.5)

    def test_increment_b_GR(self):
        # Incrementing b_GR preserves total moment rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        old_tmr = acmfd._get_total_moment_rate()
        acmfd.modify('increment_b_GR', {'value': 0.1})
        self.assertAlmostEqual(acmfd.b_GR, 0.9)
        self.assertAlmostEqual(
            acmfd._get_total_moment_rate(), old_tmr, delta=old_tmr * 1E-8) 

    def test_increment_b_AC(self):
        # Incrementing b_AC preserves total moment rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        old_tmr = acmfd._get_total_moment_rate()
        acmfd.modify('increment_b_AC', {'value': 0.1})
        self.assertAlmostEqual(acmfd.b_AC, 0.4)
        self.assertAlmostEqual(
            acmfd._get_total_moment_rate(), old_tmr, delta=old_tmr * 1E-8) 

    def test_increment_b_AC_check_constraints(self):
        # b_AC = 0.3 + 1.2 = 1.5 should fail (equals c_val)
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        self.assert_mfd_error(acmfd.modify, 'increment_b_AC', {'value': 1.2})

    def test_increment_max_mag(self):
        # Incrementing max_mag preserves total moment rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        old_tmr = acmfd._get_total_moment_rate()
        acmfd.modify('increment_max_mag', {'value': 0.5})
        self.assertAlmostEqual(acmfd.max_mag, 8.0)
        self.assertAlmostEqual(
            acmfd._get_total_moment_rate(), old_tmr, delta=old_tmr * 1E-8)

    def test_increment_max_mag_check_constraints(self):
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        # Decrease max_mag so m_c <= min_mag
        self.assert_mfd_error(acmfd.modify, 'increment_max_mag', {'value': -3.0})

    def test_increment_max_mag_no_mo_balance(self):
        # Shifts max_mag without rebalancing total_rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        old_rate = acmfd.total_rate
        acmfd.modify('increment_max_mag_no_mo_balance', {'value': 0.5})
        self.assertAlmostEqual(acmfd.max_mag, 8.0)
        self.assertEqual(acmfd.total_rate, old_rate)


class AlternativeCharacteristicMFDZoneRatesTestCase(unittest.TestCase):
    """
    Tests for the GR / AC zone rate partitioning.
    """
    def test_rates_sum_to_total_rate(self):
        # GR + AC zone rates must equal the total rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        n_GR, n_AC = acmfd._compute_zone_rates()
        self.assertAlmostEqual(
            n_GR + n_AC, TEST_MFD_INPUTS['total_rate'], places=10)

    def test_rates_are_positive(self):
        # Both zone rates must be positive
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        n_GR, n_AC = acmfd._compute_zone_rates()
        self.assertGreater(n_GR, 0)
        self.assertGreater(n_AC, 0)


class AlternativeCharacteristicMFDGetRatesTestCase(BaseMFDTestCase):
    """
    Tests for get_annual_occurrence_rates output.
    """
    def test_rates_are_positive(self):
        # Every bin must have a positive occurrence rate
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        rates = acmfd.get_annual_occurrence_rates()
        self.assertGreater(len(rates), 0)
        for mag, rate in rates:
            self.assertGreater(
                rate, 0, 'rate at mag %g should be positive' % mag)

    def test_magnitudes_are_ascending(self):
        # Magnitude bins must be in increasing order
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        rates = acmfd.get_annual_occurrence_rates()
        mags = [mag for mag, _ in rates]
        for i in range(1, len(mags)):
            self.assertGreater(mags[i], mags[i - 1])

    def test_bin_width_consistency(self):
        # Spacing between consecutive bins must equal bin_width
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        rates = acmfd.get_annual_occurrence_rates()
        mags = [mag for mag, _ in rates]
        for i in range(1, len(mags)):
            self.assertAlmostEqual(
                mags[i] - mags[i - 1], TEST_MFD_INPUTS['bin_width'], places=10)

    def test_get_min_max_mag(self):
        # Min/max mag must match the first/last bin centres
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        min_mag, max_mag = acmfd.get_min_max_mag()
        rates = acmfd.get_annual_occurrence_rates()
        self.assertAlmostEqual(min_mag, rates[0][0])
        self.assertAlmostEqual(max_mag, rates[-1][0])


class AlternativeCharacteristicMFDRoundingTestCase(BaseMFDTestCase):
    """
    Tests that non-round magnitude bounds snap correctly.
    """
    def test(self):
        # Non-round min/max values assigned to correct bin centres
        acmfd = AlternativeCharacteristicMFD(
            **{**TEST_MFD_INPUTS, 'min_mag': 4.01, 'max_mag': 7.49})
        min_mag, num_bins = acmfd._get_min_mag_and_num_bins()
        self.assertAlmostEqual(min_mag, 4.05) # First bin centre is Mw 4.05
        self.assertEqual(num_bins, 35)


class AlternativeCharacteristicMFDTotalMomentRateTestCase(unittest.TestCase):
    """
    Tests for the get_total_moment_rate method.
    """
    def test_tmr_is_positive(self):
        # Total moment rate must be positive for valid inputs
        acmfd = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        tmr = acmfd._get_total_moment_rate()
        self.assertGreater(tmr, 0)

    def test_tmr_scales_with_total_rate(self):
        # Doubling total_rate must double the moment rate
        acmfd1 = AlternativeCharacteristicMFD(**TEST_MFD_INPUTS)
        acmfd2 = AlternativeCharacteristicMFD(**{**TEST_MFD_INPUTS, 'total_rate': 10.0})
        tmr1 = acmfd1._get_total_moment_rate()
        tmr2 = acmfd2._get_total_moment_rate()
        self.assertAlmostEqual(
            tmr2 / tmr1, 10.0 / TEST_MFD_INPUTS['total_rate'], places=10)


class AlternativeCharacteristicMFDFromMomentTestCase(unittest.TestCase):
    """
    Tests for the from_moment class method.
    """
    def test_moment_rate_preserved(self):
        # Constructed TMR must match the target moment_rate
        moment_rate = 1.0e18
        inputs = {**TEST_MFD_INPUTS}
        inputs.pop('total_rate') # Need to remove total_rate
        acmfd = AlternativeCharacteristicMFD.from_moment(
            **inputs, moment_rate=moment_rate)
        computed_tmr = acmfd._get_total_moment_rate()
        self.assertAlmostEqual(computed_tmr, moment_rate, delta=moment_rate * 1e-8) 

    def test_from_moment_returns_correct_type(self):
        # Class method must return an AlternativeCharacteristicMFD instance
        inputs = {**TEST_MFD_INPUTS}
        inputs.pop('total_rate') # Need to remove total_rate
        acmfd = AlternativeCharacteristicMFD.from_moment(
            **inputs, moment_rate=1.0e18)
        self.assertIsInstance(acmfd, AlternativeCharacteristicMFD)


class AlternativeCharacteristicMFDFromSlipRateTestCase(unittest.TestCase):
    """
    Tests for the from_slip_rate class method.
    """
    def test_slip_rate_to_moment(self):
        # TMR must equal slip_rate * rigidity * area
        slip_rate = 2.0  # mm/yr
        rigidity = 30.0  # GPa
        area = 500.0  # km^2
        expected_tmr = (slip_rate * 1e-3) * (rigidity * 1e9) * (area * 1e6) # N·m/yr
        inputs = {**TEST_MFD_INPUTS}
        inputs.pop('total_rate')
        acmfd = AlternativeCharacteristicMFD.from_slip_rate(
            **inputs,
            slip_rate=slip_rate,
            rigidity=rigidity,
            area=area
            )
        computed_tmr = acmfd._get_total_moment_rate()
        self.assertAlmostEqual(computed_tmr, expected_tmr, delta=expected_tmr * 1e-8)

    def test_slip_rate_attributes(self):
        # slip_rate and rigidity are stored as attributes
        inputs = {**TEST_MFD_INPUTS}
        inputs.pop('total_rate')
        acmfd = AlternativeCharacteristicMFD.from_slip_rate(
            **inputs,
            slip_rate=2.0,
            rigidity=30.0,
            area=500.0
            )
        self.assertEqual(acmfd.slip_rate, 2.0)
        self.assertEqual(acmfd.rigidity, 30.0)

    def test_from_slip_rate_returns_correct_type(self):
        # Class method must return an AlternativeCharacteristicMFD instance
        inputs = {**TEST_MFD_INPUTS}
        inputs.pop('total_rate')
        acmfd = AlternativeCharacteristicMFD.from_slip_rate(
            **inputs, slip_rate=2.0, rigidity=30.0, area=500.0)
        self.assertIsInstance(acmfd, AlternativeCharacteristicMFD)
