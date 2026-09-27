# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import json
import numpy
from openquake.baselib import general
from openquake.baselib.hdf5 import dumps, obj_to_json, json_to_obj


class DumpsTestCase(unittest.TestCase):
    def test(self):
        dic = dict(imts=numpy.array([0.1, 0.2, 0.3]))
        self.assertEqual(dumps(dic), '{\n"imts": [0.1, 0.2, 0.3]}')

        dic = dict(base_path=r"C:\Users\test")
        self.assertEqual(dumps(dic), '{\n"base_path": "C:\\\\Users\\\\test"}')

    def test_non_finite_floats(self):
        # the values are interpolated as strings, so a bare str(inf) would
        # be invalid json; they must be serialised as Infinity/NaN
        dic = dict(a=numpy.float64(numpy.inf), b=-numpy.inf,
                   c=float('nan'), d=dict(default=numpy.inf),
                   e=[1.5, numpy.inf])
        txt = dumps(dic)
        self.assertIn('"a": Infinity', txt)
        self.assertIn('"b": -Infinity', txt)
        self.assertIn('"c": NaN', txt)
        self.assertIn('"default": Infinity', txt)
        self.assertIn('[1.5, Infinity]', txt)
        # and it must be readable back, as OqParam.__fromh5__ does
        back = json.loads(general.decode(txt))
        self.assertEqual(back['a'], numpy.inf)
        self.assertEqual(back['b'], -numpy.inf)
        self.assertTrue(numpy.isnan(back['c']))
        self.assertEqual(back['d'], dict(default=numpy.inf))
        self.assertEqual(back['e'][1], numpy.inf)


class Obj:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class ObjToJsonTestCase(unittest.TestCase):
    def test_flat(self):
        obj = Obj(1, 0)
        js = obj_to_json(obj)
        self.assertEqual(js, '{\n"openquake.baselib.tests.hdf5_test.Obj":'
                         ' {\n"a": 1,\n"b": 0}}')
        ob = json_to_obj(js)
        self.assertEqual(vars(obj), vars(ob))

    def test_nested(self):
        obj = Obj(1, Obj(1, 2))
        js = obj_to_json(obj)
        print(js)
