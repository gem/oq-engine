# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2017 GEM Foundation

# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import time
import operator
import unittest
from setuptools.command.test import ScanningLoader


class TestLoader(object):
    def loadTestsFromNames(self, suitename, module=None):
        names = suitename[0].split(',')
        return ScanningLoader().loadTestsFromNames(names, module)


class TestResult(unittest.TextTestResult):
    timedict = {}

    def startTest(self, test):
        tname = getattr(test, '_testMethodName', None)
        self.testname = '%s:%s' % (test.__module__, tname)
        self.timedict[self.testname] = time.time()
        unittest.TextTestResult.startTest(self, test)

    def stopTest(self, test):
        unittest.TextTestResult.stopTest(self, test)
        self.timedict[self.testname] = (
            time.time() - self.timedict[self.testname])

    def save_times(self, fname):
        items = sorted(self.timedict.items(), key=operator.itemgetter(1),
                       reverse=True)
        with open(fname, 'w') as f:
            for name, value in items:
                f.write('%s %s\n' % (name, value))
        print(''.join(open(fname).readlines()[:20]))
        print('Saved times in ' + fname)
        if self.errors or self.failures:
            raise SystemExit(len(self.errors) + len(self.failures))

unittest.TextTestRunner.resultclass = TestResult


# hack to make unittest to understand the attributes added by nose
# this is used only to skip the slow tests
def addTest(self, test):
    tname = getattr(test, '_testMethodName', None)
    if tname:
        attrs = vars(getattr(test, tname))
        if 'slow' in attrs:
            return
    self._tests.append(test)
unittest.BaseTestSuite.addTest = addTest


if __name__ == '__main__':
    import sys
    pkgnames = sys.argv[1]  # comma separated package names
    suite = TestLoader().loadTestsFromNames([pkgnames])
    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    runner.run(suite).save_times(pkgnames)
