
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


import os
import shutil
import tempfile
import unittest
import openquake.nrmllib

from openquake.engine.export import core as export


def number_of(elem_name, tree):
    """
    Given an element name (including the namespaces prefix, if applicable),
    return the number of occurrences of the element in a given XML document.
    """
    expr = '//%s' % elem_name
    return len(tree.xpath(expr, namespaces=openquake.nrmllib.PARSE_NS_MAP))


class BaseExportTestCase(unittest.TestCase):
    def _test_exported_file(self, filename):
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.path.isabs(filename))
        self.assertTrue(os.path.getsize(filename) > 0)


@export.makedirsdeco
def _decorated(_output, _target_dir):
    """Just a test function for exercising the `makedirsdeco` decorator."""
    return []


class UtilsTestCase(unittest.TestCase):
    """Tests for misc. export utilties."""

    def test_makedirsdeco(self):
        temp_dir = tempfile.mkdtemp()

        try:
            target_dir = os.path.join(temp_dir, 'some', 'nonexistent', 'dir')

            self.assertFalse(os.path.exists(target_dir))

            _decorated(None, target_dir)

            self.assertTrue(os.path.exists(target_dir))
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirsdeco_dir_already_exists(self):
        # If the dir already exists, this should work with no errors.
        # The decorator should just gracefully pass through.
        temp_dir = tempfile.mkdtemp()
        try:
            _decorated(None, temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirsdeco_target_exists_as_file(self):
        # If a file exists with the exact path of the target dir,
        # we should get a RuntimeError.
        _, temp_file = tempfile.mkstemp()

        try:
            self.assertRaises(RuntimeError, _decorated, None, temp_file)
        finally:
            os.unlink(temp_file)
