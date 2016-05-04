# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2016 GEM Foundation
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

from openquake.hazardlib import speedups


class SpeedupsRegistryTestCase(unittest.TestCase):
    def setUp(self):
        super(SpeedupsRegistryTestCase, self).setUp()

        def orig():
            return 'orig'

        def alt():
            return 'alt'

        self.orig = orig
        self.alt = alt
        self.registry = speedups.SpeedupsRegistry()

    def test_register_enabled(self):
        self.registry.enable()
        self.assertEqual(self.orig(), 'orig')
        self.registry.register(self.orig, self.alt)
        self.assertEqual(self.orig(), 'alt')
        self.assertEqual(list(self.registry.funcs), [self.orig])

    def test_register_disabled(self):
        self.registry.disable()
        self.assertEqual(self.orig(), 'orig')
        self.registry.register(self.orig, self.alt)
        self.assertEqual(self.orig(), 'orig')
        self.assertEqual(list(self.registry.funcs), [self.orig])

    def test_enable_disable(self):
        self.registry.register(self.orig, self.alt)
        self.assertEqual(self.registry.enabled, True)
        self.registry.disable()
        self.assertEqual(self.registry.enabled, False)
        self.assertEqual(self.orig(), 'orig')
        self.registry.enable()
        self.assertEqual(self.orig(), 'alt')

    def test_different_signature(self):
        def alt2(foo):
            pass
        with self.assertRaises(AssertionError) as ar:
            self.registry.register(self.orig, alt2)
        self.assertTrue(str(ar.exception).startswith('functions signatures ' \
                                                     'are different'))
