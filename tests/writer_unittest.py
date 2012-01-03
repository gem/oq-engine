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
        """_init_file() will truncate the file when opening it."""
        path = "/tmp/a"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path)
            fw._init_file()
            self.assertEqual((path, "w"), mock_open.call_args[0])

    def test__init_file_with_valid_mode(self):
        """_init_file() will open the file in append mode."""
        path = "/tmp/b"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path, mode="a")
            fw._init_file()
            self.assertEqual((path, "a"), mock_open.call_args[0])

    def test__init_file_with_invalid_mode(self):
        """
        An invalid mode (not in ('a', 'w')) will be ignored and the file be
        truncated.
        """
        path = "/tmp/c"
        # Only mock the open() built-in in the writer module.
        with mock.patch("openquake.writer.open", create=True) as mock_open:
            fw = writer.FileWriter(path, mode="what!?")
            fw._init_file()
            self.assertEqual((path, "w"), mock_open.call_args[0])
