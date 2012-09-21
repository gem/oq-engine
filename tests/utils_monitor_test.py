# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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
Unit tests for the utils.stats module.
"""


import unittest

from openquake import engine
from openquake.db import models
from openquake.utils import monitor

from tests.utils.helpers import patch


class GetCnodeStatusTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor._get_cnode_status()."""

    def test__get_cnode_status(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(
                ["gemsun02: OK", "gemsun01: OK", "gemsun03: OK", "",
                 "3 nodes online."])
            actual = monitor._get_cnode_status()
            expected = {"gemsun01": "OK", "gemsun02": "OK", "gemsun03": "OK"}
            self.assertEqual(expected, actual)

    def test__get_cnode_status_with_one(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(["usc: OK", "", "1 node online."])
            actual = monitor._get_cnode_status()
            expected = {"usc": "OK"}
            self.assertEqual(expected, actual)

    def test__get_cnode_status_with_mixed(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(
                ["oqt: OK", "usc: ERROR", "", "2 nodes online."])
            actual = monitor._get_cnode_status()
            expected = {"oqt": "OK", "usc": "ERROR"}
            self.assertEqual(expected, actual)


class GetCnodeStatusInDbTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor._get_cnode_status_in_db()."""

    def test__get_cnode_status_in_db(self):
        job = engine.prepare_job()
        for node, status in [("N1", "up"), ("N2", "down"), ("N3", "error")]:
            ns = models.NodeStats(oq_job=job, node=node, status=status)
            ns.save()
        expected = {"N1": "up", "N2": "down", "N3": "error"}
        self.assertEqual(expected, monitor._get_cnode_status_in_db(job.id))
