# Copyright (c) 2010-2014, GEM Foundation.
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
Tests for code in :mod:`openquake.engine.__init__`.
"""

import os
import unittest

import openquake.engine

from mock import patch


class NoDistributeTestCase(unittest.TestCase):

    def test_no_distribute_not_set(self):
        with patch.dict('os.environ'):
            if openquake.engine.NO_DISTRIBUTE_VAR in os.environ:
                os.environ.pop(openquake.engine.NO_DISTRIBUTE_VAR)

            self.assertFalse(openquake.engine.no_distribute())

    def test_no_distribute_set_true(self):
        with patch.dict('os.environ'):
            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = '1'
            self.assertTrue(openquake.engine.no_distribute())

            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = 'true'
            self.assertTrue(openquake.engine.no_distribute())

            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = 'yes'
            self.assertTrue(openquake.engine.no_distribute())

            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = 't'
            self.assertTrue(openquake.engine.no_distribute())

    def test_no_distribute_set_false(self):
        with patch.dict('os.environ'):
            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = '0'
            self.assertFalse(openquake.engine.no_distribute())

            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = 'false'
            self.assertFalse(openquake.engine.no_distribute())

            os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = 'blarg'
            self.assertFalse(openquake.engine.no_distribute())
