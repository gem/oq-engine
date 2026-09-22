# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Some modules read data files (CSV/HDF5/...) at import time, so those
files must be shipped in the distribution. ``MANIFEST.in`` is the source
of truth for the included package data, therefore this test flags any
data file opened while importing ``PACKAGES`` that ``MANIFEST.in`` does
not cover.
"""
import os
import sys
import pathlib
import logging
import subprocess
import textwrap
import unittest

try:
    from setuptools._distutils.filelist import FileList
except ImportError:  # pragma: no cover
    from distutils.filelist import FileList

# repo root (the folder containing MANIFEST.in)
ROOT = pathlib.Path(__file__).parents[3]

# packages whose submodules are imported to trigger the import-time reads
PACKAGES = ['openquake.hazardlib', 'openquake.pfd']

# file extensions considered package data
DATA_EXT = {'.csv', '.hdf5', '.onnx', '.gz', '.npz', '.npy', '.txt',
            '.dat', '.json', '.xml', '.geojson'}

# imports every submodule of PACKAGES in a fresh interpreter and prints
# the data files opened while doing so (a fresh process is required
# because the audit hook only sees the opens happening after it is
# installed, and in the test process the modules are already imported)
_IMPORTER = textwrap.dedent('''\
    import importlib, os, pkgutil, sys, warnings
    warnings.simplefilter('ignore')
    root, packages, exts = {root!r}, {packages!r}, {exts!r}
    opened = []
    def _hook(event, args):
        if event == 'open' and isinstance(args[0], str):
            opened.append(os.path.abspath(args[0]))
    sys.addaudithook(_hook)
    for pkg in packages:
        mod = importlib.import_module(pkg)
        for info in pkgutil.walk_packages(mod.__path__, pkg + '.'):
            if '.tests' in info.name or 'qa_tests_data' in info.name:
                continue
            try:
                importlib.import_module(info.name)
            except Exception:
                pass
    for path in sorted(set(opened)):
        if path.startswith(root + os.sep) and \
                os.path.splitext(path)[1] in exts:
            print(path)
''')


def _manifest_files():
    """
    :returns: the set of repo-relative paths that MANIFEST.in includes
    """
    allfiles = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '.git' in pathlib.Path(dirpath).parts:
            continue
        for fname in filenames:
            allfiles.append(
                os.path.relpath(os.path.join(dirpath, fname), ROOT))
    filelist = FileList()
    filelist.set_allfiles(allfiles)
    logging.disable(logging.WARNING)  # FileList warns about empty patterns
    try:
        with open(ROOT / 'MANIFEST.in') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line:
                    filelist.process_template_line(line)
    finally:
        logging.disable(logging.NOTSET)
    return set(filelist.files)


def _imported_data_files():
    """
    :returns: the repo-relative data files read at import time
    """
    code = _IMPORTER.format(
        root=str(ROOT), packages=PACKAGES, exts=DATA_EXT)
    env = dict(os.environ, OQ_DISTRIBUTE='no')
    proc = subprocess.run(
        [sys.executable, '-c', code], cwd=str(ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = []
    for line in proc.stdout.splitlines():
        path = line.strip()
        if path.startswith(str(ROOT) + os.sep) and '.egg-info' not in path:
            out.append(os.path.relpath(path, ROOT))
    return out


class ManifestTestCase(unittest.TestCase):
    def test_import_time_data_is_packaged(self):
        # every data file read at import time must be in MANIFEST.in
        included = _manifest_files()
        missing = sorted(set(_imported_data_files()) - included)
        self.assertFalse(
            missing, 'data files read at import time but not included in '
            'MANIFEST.in:\n%s' % '\n'.join(missing))