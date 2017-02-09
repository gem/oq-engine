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
from openquake.baselib import sap


def f(a, b, c, d=1):
    return [a, b, c, d]


class SapTestCase(unittest.TestCase):
    def test_ok(self):
        p = sap.Script(f)
        p.arg('a', 'first argument')
        p.opt('b', 'second argument')
        p.flg('c', 'third argument')
        p.opt('d', 'fourth argument')
        self.assertEqual(
            ['1', '2', False, '3'], p.callfunc('1 -b=2 -d=3'.split()))

    def test_group(self):
        p = sap.Script(f)
        p.arg('a', 'first argument')
        p.opt('b', 'second argument')
        p.group('other arguments')
        p.flg('c', 'third argument')
        p.opt('d', 'fourth argument')
        self.assertEqual(p.help(), '''\
usage: %s [-h] [-b B] [-c] [-d 1] a

positional arguments:
  a            first argument

optional arguments:
  -h, --help   show this help message and exit
  -b B, --b B  second argument

other arguments:
  -c, --c      third argument
  -d 1, --d 1  fourth argument
''' % p.parentparser.prog)

    def test_NameError(self):
        p = sap.Script(f)
        p.arg('a', 'first argument')
        with self.assertRaises(NameError):
            p.flg('c', 'third argument')

    def test_no_help(self):
        p = sap.Script(f, help=None)
        p.arg('a', 'first argument')
        p.opt('b', 'second argument')
        self.assertEqual(p.help(), '''\
usage: %s [-b B] a

positional arguments:
  a            first argument

optional arguments:
  -b B, --b B  second argument
''' % p.parentparser.prog)
        # missing argparse specification for 'c'
        with self.assertRaises(NameError):
            p.check_arguments()

    def test_long_argument(self):
        # test the replacement '_' -> '-' in variable names
        p = sap.Script(lambda a_long_argument: None)
        p.opt('a_long_argument', 'a long argument')
        self.assertEqual(p.help(), '''\
usage: %s [-h] [-a A_LONG_ARGUMENT]

optional arguments:
  -h, --help            show this help message and exit
  -a A_LONG_ARGUMENT, --a-long-argument A_LONG_ARGUMENT
                        a long argument
''' % p.parentparser.prog)
