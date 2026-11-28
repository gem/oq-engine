# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest
import unittest.mock as mock
import numpy

from openquake.baselib.general import duplicated, gen_subclasses
from openquake.hazardlib import const, valid
from openquake.hazardlib.gsim.backbone import shifted_compute
from openquake.hazardlib.gsim.base import (
    GMPE, GroundShakingIntensityModel, gsim_aliases, NotVerifiedWarning,
    DeprecationWarning, get_central_key)
from openquake.hazardlib.gsim.kotha_2020 import (
    KothaEtAl2020, KothaEtAl2020ESHM20)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.contexts import ContextMaker
aac = numpy.testing.assert_allclose


class _FakeGSIMTestCase(unittest.TestCase):
    DEFAULT_IMT = PGA
    DEFAULT_COMPONENT = const.IMC.GMRotI50

    def setUp(self):
        class FakeGSIM(GMPE):
            DEFINED_FOR_TECTONIC_REGION_TYPE = None
            DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
            DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
            DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
            REQUIRES_SITES_PARAMETERS = set()
            REQUIRES_RUPTURE_PARAMETERS = set()
            REQUIRES_DISTANCES = set()
        super().setUp()
        self.gsim_class = FakeGSIM
        self.gsim = self.gsim_class()
        self.cmaker = ContextMaker('faketrt', [self.gsim], dict(imtls={}))
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
            self.DEFAULT_COMPONENT
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES = frozenset(
            self.gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES | {self.DEFAULT_IMT})

    def _assert_value_error(self, func, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            func(**kwargs)
        self.assertEqual(str(ar.exception), error)


class TGMPE(GMPE):
    DEFINED_FOR_TECTONIC_REGION_TYPE = ()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = ()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_SITES_PARAMETERS = ()
    REQUIRES_RUPTURE_PARAMETERS = ()
    REQUIRES_DISTANCES = ()


def apply_test_shift(gsim, ctx, imts, mean, *_stddevs):
    pass


class ShiftedGMPE(TGMPE):
    @shifted_compute(apply_test_shift, 'shift')
    def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi):
        pass


class CentralKeyTestCase(unittest.TestCase):
    def test_options_preserve_values_and_order(self):
        gsim = ShiftedGMPE()
        values = [[1], (1,), '', 'None', '/first/table', '/second/table']
        keys = set()
        for value in values:
            gsim.kwargs = {'option': value}
            keys.add(get_central_key(gsim))
        self.assertEqual(len(keys), len(values))
        gsim.kwargs = {'first': 1, 'second': 2}
        key = get_central_key(gsim)
        gsim.kwargs = {'second': 2, 'first': 1}
        self.assertNotEqual(get_central_key(gsim), key)

    def test_branch_options_are_excluded(self):
        gsim = ShiftedGMPE()
        gsim.kwargs = {'option': 1, 'shift': -1.}
        key = get_central_key(gsim)
        gsim.kwargs = {'option': 1, 'shift': 1.}
        self.assertEqual(get_central_key(gsim), key)

    def test_kotha_eshm20_can_share_across_dl2l_values(self):
        lower, upper = {'PGA': -0.2}, {'PGA': 0.2}
        self.assertEqual(KothaEtAl2020ESHM20(dl2l=lower).central_key,
                         KothaEtAl2020ESHM20(dl2l=upper).central_key)
        self.assertNotEqual(KothaEtAl2020(dl2l=lower).central_key,
                            KothaEtAl2020(dl2l=upper).central_key)


class GsimInstantiationTestCase(unittest.TestCase):
    def test_unique_class_names(self):
        # The registry can overwrite earlier classes with the same name.
        classes = gen_subclasses(GroundShakingIntensityModel)
        names = [cls.__name__ for cls in classes
                 if cls.__module__.startswith('openquake.hazardlib.gsim.')]
        self.assertEqual(duplicated(names), [])
    def test_none_default_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "option must default to ''"):
            class NoneDefaultGMPE(TGMPE):
                def __init__(self, *, option=None):
                    pass

    def test_explicit_none_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "option must use ''"):
            TGMPE(option=None)

    def test_non_literal_options_are_rejected(self):
        with self.assertRaisesRegex(
                ValueError, 'TGMPE.option must be a Python literal'):
            TGMPE(option={'unsupported': object()})

    def test_deprecated(self):
        # check that a deprecation warning is raised when a deprecated
        # GSIM is instantiated

        class NewGMPE(TGMPE):
            'The version which is not deprecated'

        class OldGMPE(NewGMPE):
            'The version which is deprecated'
            superseded_by = NewGMPE

        with mock.patch('warnings.warn') as warn:
            OldGMPE()  # instantiating this class will call warnings.warn

        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, DeprecationWarning)
        self.assertEqual(
            warning_msg, 'OldGMPE is deprecated - use NewGMPE instead')

    def test_non_verified(self):
        # check that a NonVerifiedWarning is raised when a non-verified
        # GSIM is instantiated

        class MyGMPE(TGMPE):
            non_verified = True

        with mock.patch('warnings.warn') as warn:
            MyGMPE()  # instantiating this class will call warnings.warn

        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, NotVerifiedWarning)
        self.assertEqual(
            warning_msg, 'MyGMPE is not independently verified - '
            'the user is liable for their application')


class AliasesTestCase(unittest.TestCase):
    """
    Check that all aliases are valid
    """
    def test_valid(self):
        n = 0
        for toml in gsim_aliases.values():
            valid.gsim(toml)
            n += 1
        print('Checked %d valid aliases' % n)
