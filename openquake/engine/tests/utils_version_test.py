# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Unit tests for the utils.version module.
"""


from datetime import datetime
from datetime import timedelta
import unittest

from openquake.engine.utils import version


class VersionInfoTestCase(unittest.TestCase):
    """Tests the behaviour of utils.version.info()."""

    def __init__(self, *args, **kwargs):
        super(VersionInfoTestCase, self).__init__(*args, **kwargs)

    def test_info_with_major_number_only(self):
        """Only the major version number is set."""
        self.assertEqual(
            "OpenQuake version 2.0.0", version.info((2, -1, -1, -1)))

    def test_info_with_minor_number_only(self):
        """Only the minor version number is set."""
        self.assertEqual(
            "OpenQuake version 0.2.0", version.info((-1, 2, -1, -1)))

    def test_info_with_sprint_number_only(self):
        """Only the sprint number is set."""
        self.assertEqual(
            "OpenQuake version 0.0.2", version.info((-1, -1, 2, -1)))

    def test_info_with_all_data_in_place(self):
        """All the version information is in place."""
        self.assertEqual(
            "OpenQuake version 0.3.2, released 2011-04-08T06:04:11Z",
            version.info((0, 3, 2, 1302242651)))

    def test_info_with_malformed_version_information(self):
        """The version information is malformed."""
        self.assertEqual(
            "The OpenQuake version is not available.", version.info((-1,)))

    def test_info_with_data_not_integer(self):
        """The version information is malformed (non-integers)."""
        self.assertEqual(
            "The OpenQuake version is not available.",
            version.info(("2", "-1", "-1", "-1")))

    def test_info_with_data_not_a_tuple(self):
        """The version information is malformed (not in a tuple)."""
        self.assertEqual(
            "The OpenQuake version is not available.",
            version.info([2, -1, -1, -1]))

    def test_info_with_datum_less_than_minus_one(self):
        """The version information is malformed (datum less than -1)."""
        self.assertEqual(
            "The OpenQuake version is not available.",
            version.info([2, -1, -1, -2]))

    def test_info_with_release_date_more_than_a_month_in_future(self):
        """The release date is ignored since it is too far in the future."""
        today_plus_60_days = int(
            (datetime.today() + timedelta(days=60)).strftime("%s"))
        self.assertEqual(
            "OpenQuake version 0.3.2",
            version.info((0, 3, 2, today_plus_60_days)))
