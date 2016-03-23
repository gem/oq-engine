# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

"""
Tests for code in :mod:`openquake.engine.__init__`.
"""

import os
import unittest

from openquake.commonlib.parallel import no_distribute

from mock import patch


class NoDistributeTestCase(unittest.TestCase):

    def test_no_distribute_not_set(self):
        with patch.dict('os.environ'):
            if 'OQ_DISTRIBUTE' in os.environ:
                os.environ.pop('OQ_DISTRIBUTE')

            self.assertFalse(no_distribute())

    def test_no_distribute_set_true(self):
        with patch.dict('os.environ'):
            os.environ['OQ_DISTRIBUTE'] = 'no'
            self.assertTrue(no_distribute())

    def test_no_distribute_set_false(self):
        with patch.dict('os.environ'):
            os.environ['OQ_DISTRIBUTE'] = 'celery'
            self.assertFalse(no_distribute())

            os.environ['OQ_DISTRIBUTE'] = 'futures'
            self.assertFalse(no_distribute())

            os.environ['OQ_DISTRIBUTE'] = 'blarg'
            self.assertFalse(no_distribute())
