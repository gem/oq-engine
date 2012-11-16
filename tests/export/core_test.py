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
import uuid

from django.core.exceptions import ObjectDoesNotExist

from openquake.db import models
from openquake import engine
from openquake.export import core as export

from tests.utils import helpers


@export.makedirs
def _decorated(_output, _target_dir):
    """Just a test function for exercising the `makedirs` decorator."""
    return []


class UtilsTestCase(unittest.TestCase):
    """Tests for misc. export utilties."""

    def test_makedirs_deco(self):
        temp_dir = tempfile.mkdtemp()

        try:
            target_dir = os.path.join(temp_dir, 'some', 'nonexistent', 'dir')

            self.assertFalse(os.path.exists(target_dir))

            _decorated(None, target_dir)

            self.assertTrue(os.path.exists(target_dir))
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirs_deco_dir_already_exists(self):
        # If the dir already exists, this should work with no errors.
        # The decorator should just gracefully pass through.
        temp_dir = tempfile.mkdtemp()
        try:
            _decorated(None, temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirs_deco_target_exists_as_file(self):
        # If a file exists with the exact path of the target dir,
        # we should get a RuntimeError.
        _, temp_file = tempfile.mkstemp()

        try:
            self.assertRaises(RuntimeError, _decorated, None, temp_file)
        finally:
            os.unlink(temp_file)
