# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
from openquake.hazardlib.gsim import registry
from openquake.hazardlib.gsim.base import dump_gsim_toml, load_gsim_toml
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014


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
            r"Invalid ID 'a x': the only accepted chars are ^[\w_\-:]+$")
        with self.assertRaises(ValueError):
            valid.simple_id('0|1')
        with self.assertRaises(ValueError):
            valid.simple_id('à')
        with self.assertRaises(ValueError):
            valid.simple_id('\t')
        with self.assertRaises(ValueError):
            valid.simple_id('a' * 101)

    def test_source_id(self):
        valid.source_id('ab_2:3_-27:0')

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
            valid.namelist('x É')

    def test_longitude(self):
        self.assertEqual(valid.longitude('1'), 1.0)
        self.assertEqual(valid.longitude('180'), 180.0)
        with self.assertRaises(ValueError):
            valid.longitude('181')
        with self.assertRaises(ValueError):
            valid.longitude('-181')
        with self.assertRaises(ValueError):
            valid.longitude('nan')

    def test_latitude(self):
        self.assertEqual(valid.latitude('1'), 1.0)
        self.assertEqual(valid.latitude('90'), 90.0)
        with self.assertRaises(ValueError):
            valid.latitude('91')
        with self.assertRaises(ValueError):
            valid.latitude('-91')
        with self.assertRaises(ValueError):
            valid.latitude('nan')

    def test_depth(self):
        self.assertEqual(valid.depth('-1.5'), -1.5)
        for value in ('nan', 'inf'):
            with self.assertRaises(ValueError):
                valid.depth(value)

    def test_positiveint(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positiveint('-1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.0')

    def test_positiveints(self):
        self.assertEqual(valid.positiveints('1'), [1])
        self.assertEqual(valid.positiveints('1 2'), [1, 2])
        with self.assertRaises(ValueError):
            valid.positiveints('1 -1')
        with self.assertRaises(ValueError):
            valid.positiveints('1.1')
        with self.assertRaises(ValueError):
            valid.positiveints('1.0')

    def test_positivefloat(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positivefloat('-1')
        self.assertEqual(valid.positivefloat('1.1'), 1.1)

    def test_positivefloats(self):
        self.assertEqual(valid.positivefloats('1 2'), [1, 2])
        with self.assertRaises(ValueError):
            valid.positivefloat('-1 -2.5')

    def test_positivefloatorsentinel(self):
        self.assertEqual(valid.positivefloatorsentinel('-999'), -999)
        self.assertEqual(valid.positivefloatorsentinel('2.5'), 2.5)
        with self.assertRaises(ValueError):
            valid.positivefloatorsentinel('-1')
            valid.positivefloatorsentinel('0.0')

    def test_positivefloatsorsentinels(self):
        self.assertEqual(valid.positivefloatsorsentinels('-999 2.5'), [-999, 2.5])
        with self.assertRaises(ValueError):
            valid.positivefloatsorsentinels('-1 0.')

    def test_probability(self):
        self.assertEqual(valid.probability('1'), 1.0)
        self.assertEqual(valid.probability('.5'), 0.5)
        self.assertEqual(valid.probability('0'), 0.0)
        with self.assertRaises(ValueError):
            valid.probability('1.1')
        with self.assertRaises(ValueError):
            valid.probability('-0.1')

    def test_IMTstr(self):
        self.assertEqual(imt.from_string('SA(1)'), ('SA(1.0)', 1, 5, None))
        self.assertEqual(imt.from_string('SA(1.)'), ('SA(1.0)', 1, 5, None))
        self.assertEqual(imt.from_string('SA(0.5)'), ('SA(0.5)', 0.5, 5, None))
        self.assertEqual(imt.from_string('PGV'), ('PGV', 0., 5, None))
        self.assertEqual(imt.from_string('SDi(1.,2.)'),
                         ('SDi(1.0,2.0)', 1, 5, 2))
        with self.assertRaises(KeyError):
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

    def test_full_instantiation(self):
        # test for https://github.com/gem/oq-engine/issues/7363
        abr = valid.gsim("AbrahamsonEtAl2014")
        self.assertIsNone(abr.region)

    def test_gsim(self):
        class FakeGsim(object):
            def __init__(self, arg):
                self.arg = arg

            def init(self):
                pass

            def __repr__(self):
                return '<FakeGsim(%s)>' % self.arg
        registry['FakeGsim'] = FakeGsim
        try:
            gsim = valid.gsim('[FakeGsim]\narg=0.1', '/fake/dir')
            self.assertEqual(repr(gsim), '<FakeGsim(0.1)>')
        finally:
            del registry['FakeGsim']

    def test_gsim_explicit_none(self):
        default = BooreEtAl2014()
        explicit = BooreEtAl2014(region=None)
        restored = valid.gsim(repr(explicit))
        self.assertIsNone(restored.region)
        self.assertEqual(restored, explicit)
        self.assertEqual(hash(restored), hash(explicit))
        self.assertEqual(len({default, explicit, restored}), 2)
        self.assertEqual(explicit._toml,
                         '[BooreEtAl2014]\nregion = "__None__"')
        for region in ('', 'prefix__None__'):
            model = valid.gsim(f'[BooreEtAl2014]\nregion = "{region}"')
            self.assertEqual(valid.gsim(repr(model)).region, region)
            self.assertNotEqual(model, explicit)
        with self.assertRaisesRegex(ValueError, '__None__.*reserved'):
            BooreEtAl2014(region='__None__')

    def test_gsim_explicit_none_nested(self):
        name = 'TestGSIM'
        options = {'entries': [None, 'ordinary', None],
                   'nested': [{'unset': None, 'empty': ''}]}
        serialized = dump_gsim_toml(name, options)
        self.assertEqual(load_gsim_toml(serialized), (name, options))
        self.assertEqual(dump_gsim_toml(*load_gsim_toml(serialized)),
                         serialized)

    def test_modifiable_gmpe_explicit_none(self):
        base = BooreEtAl2014(region=None)
        gmpe = valid.modified_gsim(
            base, set_scale_median_scalar={'scaling_factor': 1.1})
        restored = valid.gsim(repr(gmpe))
        self.assertIsNone(restored.gmpe.region)
        self.assertIsNone(valid.gsim(repr(restored.gmpe)).region)
        self.assertEqual(restored, gmpe)

    def test_modifiable_gmpe(self):
        gsim = valid.gsim('Lin2011foot')
        gmpe = valid.modified_gsim(
            gsim, add_between_within_stds={'with_betw_ratio':1.5})
        valid.gsim(gmpe._toml)  # make sure the generated _toml is valid

    def test_modifiable_gmpe_complex(self):
        # Make an NGAEast GMPE and apply modifiable GMPE to it
        text = "[NBCC2015_AA13]\nREQUIRES_DISTANCES=['RJB']\n"
        text += "DEFINED_FOR_TECTONIC_REGION_TYPE='Active Crust Fault'\n"
        text += "gmpe_table='WcrustFRjb_low_clC.hdf5'"
        gsim = valid.gsim(text)
        gmpe = valid.modified_gsim(
            gsim, add_between_within_stds={'with_betw_ratio':1.5})
        valid.gsim(gmpe._toml)  # make sure the generated _toml is valid

    def test_gsim_alias(self):
        # fixes https://github.com/gem/oq-engine/issues/10489
        ag20_alaska = valid.gsim("AbrahamsonGulerce2020SInterAlaska")
        self.assertEqual(ag20_alaska.region, 'USA-AK')
        self.assertEqual(ag20_alaska._toml,
                         '[AbrahamsonGulerce2020SInter]\nregion = "USA-AK"')
