#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2019, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import pathlib
import unittest

openquake = pathlib.Path(__file__).parent.parent.parent


class LowerCaseTestCase(unittest.TestCase):
    def test(self):
        # make sure there are no Python files with the wrong case
        n = 0
        for cwd, dirs, files in os.walk(openquake):
            cwd = pathlib.Path(cwd)
            for f in files:
                if f.endswith('.py'):
                    n += 1
                    if f != f.lower():
                        raise RuntimeError('%s is not lowercase!' % (cwd / f))
        print('Checked %d Python files' % n)
