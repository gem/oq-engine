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

from openquake.hazardlib import const, valid
from openquake.hazardlib.gsim.base import (
    GMPE, gsim_aliases, NotVerifiedWarning, DeprecationWarning)
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


class GsimInstantiationTestCase(unittest.TestCase):
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
