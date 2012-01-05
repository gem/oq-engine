# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Tests related to the various Writer base classes.
"""

import mock
import unittest

from openquake import writer


class FileWriterTestCase(unittest.TestCase):
    """Tests related to the `FileWriter` abstract base class."""

    def test__init_file_with_mode_not_set(self):
        """
        _init_file() will open and truncate the file if no mode was specified.
        """
        path = "/tmp/a"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])

    def test__init_file_with_mode_start(self):
        """
        _init_file() will not open the file in mode `MODE_START`.
        """
        path = "/tmp/b"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.set_mode(writer.MODE_START)
            fw.open()
            self.assertEqual(0, mock_open.call_count)

    def test__init_file_with_mode_start_and_end(self):
        """
        _init_file() will open and truncate the file if the mode passed was
        `MODE_START_AND_END`.
        """
        path = "/tmp/c"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.set_mode(writer.MODE_START_AND_END)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])

    def test__init_file_with_mode_in_the_middle(self):
        """
        _init_file() will not open the file in mode `MODE_IN_THE_MIDDLE`.
        """
        path = "/tmp/d"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.set_mode(writer.MODE_IN_THE_MIDDLE)
            fw.open()
            self.assertEqual(0, mock_open.call_count)

    def test__init_file_with_mode_end(self):
        """
        _init_file() will open and truncate the file if the mode passed was
        `MODE_END`.
        """
        path = "/tmp/e"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.set_mode(writer.MODE_END)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])
