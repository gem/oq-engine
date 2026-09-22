# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import tempfile
import unittest
from types import SimpleNamespace

from openquake.baselib import hdf5
from openquake.commonlib.model_provenance import (
    collect_model_provenance, copy_model_provenance,
    read_model_provenance, store_model_provenance)


class ModelProvenanceTestCase(unittest.TestCase):
    """Test model provenance collection and HDF5 storage."""

    def make_repository(self, root):
        """Create a small Git repository for testing."""
        path = os.path.join(root, 'Africa')
        os.mkdir(path)
        self.git(path, 'init', '-q')
        self.git(path, 'config', 'user.email', 'test@example.com')
        self.git(path, 'config', 'user.name', 'Test User')
        with open(os.path.join(path, 'model.txt'), 'w') as stream:
            stream.write('model')
        self.git(path, 'add', 'model.txt')
        self.git(path, 'commit', '-qm', 'initial commit')
        return path

    @staticmethod
    def git(path, *args):
        """Run Git in a test repository."""
        return subprocess.run(
            ['git', *args], cwd=path, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_detached_and_dirty(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.make_repository(root)
            self.git(path, 'tag', 'v1.0.0')
            self.git(path, 'checkout', '-q', 'v1.0.0')
            with open(os.path.join(path, 'model.txt'), 'a') as stream:
                stream.write(' changed')

            summary = collect_model_provenance(root)
            [repository] = summary['repositories']
            self.assertTrue(repository['detached'])
            self.assertEqual(repository['detached_ref'], 'v1.0.0')
            self.assertIsNone(repository['branch'])
            self.assertTrue(repository['dirty'])
            self.assertEqual(len(repository['commit']), 40)

    def test_store_and_copy(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_repository(root)
            source_path = os.path.join(root, 'source.hdf5')
            target_path = os.path.join(root, 'target.hdf5')
            with hdf5.File(source_path, 'w') as source:
                source_store = SimpleNamespace(hdf5=source)
                expected = store_model_provenance(source_store, root)
            with hdf5.File(source_path, 'r') as source, \
                    hdf5.File(target_path, 'w') as target:
                target_store = SimpleNamespace(
                    hdf5=target, getitem=target.__getitem__)
                self.assertTrue(
                    copy_model_provenance(source_path, target_store))
                actual = read_model_provenance(target_store)
                self.assertEqual(actual, expected)
                self.assertEqual(
                    target['model_provenance'].attrs['format'], 'json')


if __name__ == '__main__':
    unittest.main()
