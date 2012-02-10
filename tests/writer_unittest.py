# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
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

from collections import namedtuple
import mock
import unittest

from openquake import writer


class FileWriterTestCase(unittest.TestCase):
    """Tests related to the `FileWriter` abstract base class."""

    SerializerMode = namedtuple("SerializerMode", "start, middle, end")

    def test_open_with_mode_not_set(self):
        """
        open() will open and truncate the file if no mode was specified.
        """
        path = "/tmp/a"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])

    def test_open_with_mode_start(self):
        """
        open() will not open the file if we are at the start of a multi-stage
        serialization.
        """
        path = "/tmp/b"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.mode = self.SerializerMode(True, False, False)
            fw.open()
            self.assertEqual(0, mock_open.call_count)

    def test_open_with_mode_start_and_end(self):
        """
        open() will open and truncate the file in the case of a single pass
        serialization.
        """
        path = "/tmp/c"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.mode = self.SerializerMode(True, False, True)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])

    def test_open_with_mode_in_the_middle(self):
        """
        open() will not open the file in the middle of a multi-stage
        serialization.
        """
        path = "/tmp/d"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.mode = self.SerializerMode(False, True, False)
            fw.open()
            self.assertEqual(0, mock_open.call_count)

    def test_open_with_mode_end(self):
        """
        open() will open and truncate the file if we are at the very end
        of a multi-stage serialization.
        """
        path = "/tmp/e"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw.mode = self.SerializerMode(False, False, True)
            fw.open()
            self.assertEqual((path, "w"), mock_open.call_args[0])
