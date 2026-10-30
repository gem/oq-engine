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
import logging
import unittest
import numpy as np

from openquake.commonlib.oqvalidation import OqParam
from openquake.hazardlib import imc_conversion
from openquake.hazardlib.const import IMC
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.gsim.akkar_bommer_2010 import AkkarBommer2010
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.imt import PGA, PGV, SA

PGA = PGA()
PGV = PGV()
SA_SHORT = SA(0.05)   # below BB06 lower knot
SA_MID = SA(0.5)      # inside BB06 piecewise
SA_PIVOT = SA(1.0)


class ApplyConversionTestCase(unittest.TestCase):
    """
    Testing the apply_conversion function. Covers src equal to tgt,
    BB06 and BK17 direct ratios at PGA and across the SA knot regions,
    forward/reverse tags, and the KeyError on pairs without a direct
    ratio.
    """
    def test_identity_same_component(self):
        for tgt in (IMC.GEOMETRIC_MEAN, IMC.RotD50, IMC.RotD100,
                    IMC.GMRotI50, IMC.GREATER_OF_TWO_HORIZONTAL,
                    IMC.RANDOM_HORIZONTAL):
            self.assertEqual(
                imc_conversion.apply_conversion(tgt, tgt, SA_PIVOT), ())

    def test_gmroti50_mixed_source(self):
        # BB06 Table 3 drives SA; BK17 e-supp fills the PGA/PGV gap
        # (BB06 Table 2 has no GMRotI50/GMxy row)
        pga_steps = imc_conversion.apply_conversion(
            IMC.GMRotI50, IMC.GEOMETRIC_MEAN, PGA)
        self.assertEqual(pga_steps, (('forward', 1.013, 0.076, 1.0),))
        pgv_steps = imc_conversion.apply_conversion(
            IMC.GMRotI50, IMC.GEOMETRIC_MEAN, PGV)
        self.assertEqual(pgv_steps, (('forward', 1.011, 0.085, 1.0),))

    def test_bb06_random_pga_pgv(self):
        # BB06 Table 2 Random/GMxy row
        pga_steps = imc_conversion.apply_conversion(
            IMC.RANDOM_HORIZONTAL, IMC.GEOMETRIC_MEAN, PGA)
        self.assertEqual(pga_steps, (('forward', 1.0, 0.07, 1.03),))
        pgv_steps = imc_conversion.apply_conversion(
            IMC.RANDOM_HORIZONTAL, IMC.GEOMETRIC_MEAN, PGV)
        self.assertEqual(pgv_steps, (('forward', 1.0, 0.09, 1.03),))

    def test_bk17_direct_pgv(self):
        # BK17 e-supp RotD50/GMAR PGV row: 1.021, 0.088
        steps = imc_conversion.apply_conversion(
            IMC.RotD50, IMC.GEOMETRIC_MEAN, PGV)
        self.assertEqual(steps, (('forward', 1.021, 0.088, 1.0),))

    def test_bb06_sa_flat_below_knot(self):
        # T=0.05 s < 0.15 s -> hits the flat extrapolation branch
        steps = imc_conversion.apply_conversion(
            IMC.GMRotI50, IMC.GEOMETRIC_MEAN, SA_SHORT)
        self.assertEqual(steps, (('forward', 1.0, 0.03, 1.0),))

    def test_bb06_sa_interpolation(self):
        # T=0.5 s lies inside the piecewise log10 region, so conv_sigma
        # interpolates between the short (0.03) and long (0.04) knots.
        steps = imc_conversion.apply_conversion(
            IMC.GMRotI50, IMC.GEOMETRIC_MEAN, SA_MID)
        kind, conv_median, conv_sigma, ratio_sigma = steps[0]
        w = np.log10(0.5 / 0.15) / np.log10(0.80 / 0.15)
        self.assertAlmostEqual(conv_sigma, 0.03 + 0.01 * w)
        self.assertEqual((kind, conv_median, ratio_sigma),
                         ('forward', 1.0, 1.0))

    def test_bk17_direct_pga(self):
        # BK17 RotD50/GMAR: PGA uses R1 proxy from Table 2 col 2 (1.009)
        steps = imc_conversion.apply_conversion(
            IMC.RotD50, IMC.GEOMETRIC_MEAN, PGA)
        self.assertEqual(steps, (('forward', 1.009, 0.0, 1.0),))

    def test_bk17_direct_between_two_non_geom(self):
        # BK17 col 1 directly tabulates (RotD50, GMRotI50); no pivot
        steps = imc_conversion.apply_conversion(
            IMC.RotD50, IMC.GMRotI50, PGA)
        self.assertEqual(steps, (('forward', 0.999, 0.0, 1.0),))

    def test_reverse_direction_tag(self):
        # GEOM -> RotD50 reuses the BK17 col 2 ratio tagged 'reverse'
        steps = imc_conversion.apply_conversion(
            IMC.GEOMETRIC_MEAN, IMC.RotD50, PGA)
        self.assertEqual(steps, (('reverse', 1.009, 0.0, 1.0),))

    def test_pair_without_direct_ratio_raises(self):
        # RotD100 -> GEOM has no direct ratio in either BB06 or BK17
        with self.assertRaises(KeyError):
            imc_conversion.apply_conversion(
                IMC.RotD100, IMC.GEOMETRIC_MEAN, PGA)


class CanConvertTestCase(unittest.TestCase):
    """
    Testing the can_convert function. Covers src equal to tgt, both
    directions of a tabulated pair, and the two kinds of unsupported
    pair.
    """
    def test_can_convert(self):
        can = imc_conversion.can_convert
        # same IMC on both sides is always convertible (nothing to do)
        self.assertTrue(can(IMC.VECTORIAL, IMC.VECTORIAL))
        # a tabulated pair is convertible in either direction
        self.assertTrue(can(IMC.RotD100, IMC.RotD50))
        self.assertTrue(can(IMC.RotD50, IMC.RotD100))
        # two supported IMCs but no direct ratio between them
        self.assertFalse(can(IMC.RotD100, IMC.GEOMETRIC_MEAN))
        # an IMC that is not in any ratio at all
        self.assertFalse(can(IMC.VECTORIAL, IMC.GEOMETRIC_MEAN))


class ApplyInPlaceTestCase(unittest.TestCase):
    """
    Testing the apply_in_place function. Empty steps leave the input
    alone, a forward step shifts the mean, and forward then reverse
    returns to the input.
    """
    def _mean_sig(self, mean=0.5, sigma=0.6):
        return np.array([mean]), np.array([sigma])

    def test_empty_steps_leaves_input_unchanged(self):
        me, si = self._mean_sig()
        imc_conversion.apply_in_place((me, si), ())
        np.testing.assert_array_equal(me, [0.5])
        np.testing.assert_array_equal(si, [0.6])

    def test_single_forward_step_shifts_mean(self):
        # RotD50 -> GEOM at PGA divides exp(me) by 1.009 (R1 proxy)
        me, si = self._mean_sig()
        steps = imc_conversion.apply_conversion(
            IMC.RotD50, IMC.GEOMETRIC_MEAN, PGA)
        imc_conversion.apply_in_place((me, si), steps)
        np.testing.assert_allclose(me, [0.5 - np.log(1.009)])
        np.testing.assert_array_equal(si, [0.6])

    def test_round_trip_direct_ratio(self):
        # RotD50 -> GMRotI50 then back round-trips mean and sigma
        me, si = self._mean_sig()
        me0, si0 = me.copy(), si.copy()
        fwd = imc_conversion.apply_conversion(
            IMC.RotD50, IMC.GMRotI50, PGA)
        back = imc_conversion.apply_conversion(
            IMC.GMRotI50, IMC.RotD50, PGA)
        imc_conversion.apply_in_place((me, si), fwd)
        imc_conversion.apply_in_place((me, si), back)
        np.testing.assert_allclose(me, me0, atol=1e-12)
        np.testing.assert_allclose(si, si0, atol=1e-12)


class TargetFromNameTestCase(unittest.TestCase):
    """
    Testing the target_from_name function. Covers the empty string,
    known names, and the ValueError raised on an unknown name.
    """
    def test_target_from_name(self):
        from_name = imc_conversion.target_from_name
        # empty string means no conversion requested
        self.assertIsNone(from_name(''))
        # known names map to the IMC enum member
        self.assertIs(from_name('rotd50'), IMC.RotD50)
        self.assertIs(from_name('rotd100'), IMC.RotD100)
        self.assertIs(from_name('geometric_mean'), IMC.GEOMETRIC_MEAN)
        # anything else raises
        with self.assertRaises(ValueError):
            from_name('max_horizontal')


class ContextMakerConversionTestCase(unittest.TestCase):
    """
    Testing the ContextMaker conversion setup. ContextMaker.conv is
    empty for a GSIM when its native component is already the target
    or no direct ratio connects native to target.
    """
    def _cmaker(self, target, gsim):
        param = {
            'imtls': {'PGA': [0.01, 0.1, 1.0]},
            'maximum_distance': 300.,
            'horiz_comp_to': target,
        }
        return ContextMaker('Active Shallow Crust', [gsim], param)

    def test_native_equals_target_is_skipped(self):
        cmaker = self._cmaker('rotd50', BooreEtAl2014())
        self.assertEqual(next(iter(cmaker.conv.values())), {})

    def test_empty_target_disables_conversion(self):
        cmaker = self._cmaker('', BooreEtAl2014())
        self.assertEqual(cmaker.conv, {})

    def test_unreachable_pair_is_skipped(self):
        # AkkarBommer2010 is defined for GEOMETRIC_MEAN; RotD100 has no
        # direct ratio to GEOM, so the GSIM is left unconverted.
        cmaker = self._cmaker('rotd100', AkkarBommer2010())
        self.assertEqual(next(iter(cmaker.conv.values())), {})


class LogUnsupportedTestCase(unittest.TestCase):
    """
    Testing the log_unsupported deduplication. The same
    (gsim, src, tgt) triple logs once, and distinct triples each log
    once.
    """
    def test_only_logs_once_per_triple(self):
        imc_conversion._LOGGED_UNSUPPORTED.clear()
        with self.assertLogs(level=logging.INFO) as captured:
            imc_conversion.log_unsupported(
                'FakeGSIM', IMC.RotD100, IMC.GEOMETRIC_MEAN)
            imc_conversion.log_unsupported(
                'FakeGSIM', IMC.RotD100, IMC.GEOMETRIC_MEAN)
            imc_conversion.log_unsupported(
                'FakeGSIM', IMC.RotD100, IMC.GEOMETRIC_MEAN)
            # a different triple logs separately
            imc_conversion.log_unsupported(
                'OtherGSIM', IMC.RotD100, IMC.GEOMETRIC_MEAN)
        self.assertEqual(len(captured.output), 2)


class LegacyFlagTestCase(unittest.TestCase):
    """
    Testing the legacy horiz_comp_to_geom_mean back-compat alias. When
    set to true it translates to horiz_comp_to = geometric_mean inside
    OqParam.
    """
    def test_legacy_flag_sets_target(self):
        oq = OqParam(
            calculation_mode='classical',
            description='legacy flag test',
            intensity_measure_types_and_levels='{"PGA": [0.01, 0.1, 1.0]}',
            reference_vs30_value='760',
            reference_vs30_type='measured',
            reference_depth_to_1pt0km_per_sec='100.0',
            reference_depth_to_2pt5km_per_sec='5.0',
            maximum_distance='200',
            sites='0 0',
            inputs={'job_ini': '<in-memory>'},
            horiz_comp_to_geom_mean='true',
        )
        self.assertEqual(oq.horiz_comp_to, 'geometric_mean')
