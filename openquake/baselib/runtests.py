#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from setuptools.command.test import ScanningLoader


class TestLoader(object):
    def loadTestsFromNames(self, suitename, module=None):
        names = suitename[0].split(',')
        return ScanningLoader().loadTestsFromNames(names, module)


# hack to make unittest to understand the attributes added by nose
# this is used only to skip the slow tests
def addTest(self, test):
    if hasattr(test, '_testMethodName'):
        attrs = vars(getattr(test, test._testMethodName))
        if 'slow' in attrs:
            return
    self._tests.append(test)
unittest.BaseTestSuite.addTest = addTest


if __name__ == '__main__':
    import sys
    suite = TestLoader().loadTestsFromNames([sys.argv[1]])
    unittest.TextTestRunner(verbosity=2).run(suite)
