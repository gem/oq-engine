# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
from openquake.hazardlib import imt, valid


class ValidationTestCase(unittest.TestCase):
    # more is done in the doctests inside baselib.valid

    def test_simple_id(self):
        self.assertEqual(valid.simple_id('0'), '0')
        self.assertEqual(valid.simple_id('1-0'), '1-0')
        self.assertEqual(valid.simple_id('a_x'), 'a_x')
        with self.assertRaises(ValueError) as ctx:
            valid.simple_id('a x')
        self.assertEqual(
            str(ctx.exception),
            "Invalid ID 'a x': the only accepted chars are a-zA-Z0-9_-")
        with self.assertRaises(ValueError):
            valid.simple_id('0|1')
        with self.assertRaises(ValueError):
            valid.simple_id('à')
        with self.assertRaises(ValueError):
            valid.simple_id('\t')
        with self.assertRaises(ValueError):
            valid.simple_id('a' * 101)

    def test_source_id(self):
        valid.source_id('ab_2.3_-27.0')

    def test_name(self):
        self.assertEqual(valid.name('x'), 'x')
        with self.assertRaises(ValueError):
            valid.name('1')
        with self.assertRaises(ValueError):
            valid.name('x y')

    def test_namelist(self):
        self.assertEqual(valid.namelist('x y'), ['x', 'y'])
        self.assertEqual(valid.namelist(' '), [])
        with self.assertRaises(ValueError):
            valid.namelist('x 1')

    def test_longitude(self):
        self.assertEqual(valid.longitude('1'), 1.0)
        self.assertEqual(valid.longitude('180'), 180.0)
        with self.assertRaises(ValueError):
            valid.longitude('181')
        with self.assertRaises(ValueError):
            valid.longitude('-181')

    def test_latitude(self):
        self.assertEqual(valid.latitude('1'), 1.0)
        self.assertEqual(valid.latitude('90'), 90.0)
        with self.assertRaises(ValueError):
            valid.latitude('91')
        with self.assertRaises(ValueError):
            valid.latitude('-91')

    def test_positiveint(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positiveint('-1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.0')

    def test_positivefloat(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positivefloat('-1')
        self.assertEqual(valid.positivefloat('1.1'), 1.1)

    def test_probability(self):
        self.assertEqual(valid.probability('1'), 1.0)
        self.assertEqual(valid.probability('.5'), 0.5)
        self.assertEqual(valid.probability('0'), 0.0)
        with self.assertRaises(ValueError):
            valid.probability('1.1')
        with self.assertRaises(ValueError):
            valid.probability('-0.1')

    def test_IMTstr(self):
        self.assertEqual(imt.from_string('SA(1)'), ('SA', 1, 5))
        self.assertEqual(imt.from_string('SA(1.)'), ('SA', 1, 5))
        self.assertEqual(imt.from_string('SA(0.5)'), ('SA', 0.5, 5))
        self.assertEqual(imt.from_string('PGV'), ('PGV', None, None))
        with self.assertRaises(ValueError):
            imt.from_string('S(1)')

    def test_choice(self):
        validator = valid.Choice('aggregated', 'per_asset')
        self.assertEqual(validator.__name__,
                         "Choice('aggregated', 'per_asset')")
        self.assertEqual(validator('aggregated'), 'aggregated')
        self.assertEqual(validator('per_asset'), 'per_asset')
        with self.assertRaises(ValueError):
            validator('xxx')

    def test_empty(self):
        self.assertEqual(valid.not_empty("text"), "text")
        with self.assertRaises(ValueError):
            valid.not_empty("")

    def test_none_or(self):
        validator = valid.NoneOr(valid.positiveint)
        self.assertEqual(validator(''), None)
        self.assertEqual(validator('1'), 1)

    def test_gsim(self):
        class FakeGsim(object):
            def __init__(self, arg):
                self.arg = arg

            def __repr__(self):
                return '<FakeGsim(%s)>' % self.arg
        valid.GSIM['FakeGsim'] = FakeGsim
        try:
            gsim = valid.gsim('FakeGsim', arg='0.1')
            self.assertEqual(repr(gsim), '<FakeGsim(0.1)>')
        finally:
            del valid.GSIM['FakeGsim']
