# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
This is the dependency tower:

level 8            commands
level 7            server
level 6            engine
level 5            calculators
level 4            commonlib
level 3            risklib
level 2            hazardlib
level 1            baselib
"""
import os.path
import unittest
import collections
from openquake.baselib.general import assert_independent


class IndependenceTestCase(unittest.TestCase):
    def test_risklib(self):
        assert_independent('openquake.risklib', 'openquake.commonlib')
        assert_independent('openquake.risklib', 'openquake.calculators')

    def test_hmtk(self):
        assert_independent('openquake.hmtk', 'openquake.risklib')
        assert_independent('openquake.hmtk', 'openquake.commonlib')

    def test_commonlib(self):
        assert_independent('openquake.commonlib', 'openquake.calculators')
        assert_independent('openquake.baselib.node', 'openquake.hazardlib')
        assert_independent('openquake.baselib.parallel', 'openquake.hazardlib')

    def test_engine(self):
        assert_independent('openquake.engine', 'openquake.server')


class CaseConsistencyTestCase(unittest.TestCase):
    """
    Make sure all the files in the repo are distinct
    """
    def test(self):
        repodir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))))
        fnames = []
        for cwd, dirs, files in os.walk(repodir):
            for f in files:
                fnames.append(os.path.join(cwd, f))
        cnt = collections.Counter([f.lower() for f in fnames])
        for key, counts in cnt.items():
            if counts > 1:
                raise RuntimeError('There are case-inconsistent files %s' %
                                   [f for f in fnames if f.lower() == key])
