# Copyright (c) 2014, GEM Foundation.
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

import unittest
from nose.plugins.attrib import attr as noseattr
from qa_tests import risk


# the GMF-on-the-fly feature will be removed, this test must be
# changed; for the moment it is skipped (MS)
class EventBaseDumpRestoreSESTestCase(
        risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = ("QA (regression) test for Risk Event "
                                  "Based from Stochastic Event Set")
    dump_restore = True

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        raise unittest.SkipTest
        self._run_test()
