# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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

"""
Test of flake8 violations
"""
import io
import os
import ast
import importlib
import unittest
from contextlib import redirect_stdout
import numba

REPO = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__))))

LF = ord('\n')
CR = ord('\r')


def _long_funcs(module, maxlen):
    out = []
    code = open(module.__file__, encoding='utf-8').read()
    tree = ast.parse(code, module.__file__)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            numlines = node.end_lineno - node.lineno + 1
            if numlines > maxlen:
                out.append((module.__name__ + '.' + node.name, numlines))
    return out


def get_long_funcs(mod_or_pkg, maxlen):
    mod_or_pkg = importlib.import_module(mod_or_pkg)
    out = set()
    if hasattr(mod_or_pkg, '__path__'):  # is a package
        [pkg_path] = mod_or_pkg.__path__
        n = len(pkg_path)
        for cwd, dirs, files in os.walk(pkg_path):
            if all(os.path.basename(f) != '__init__.py' for f in files):
                # the current working directory is not a subpackage
                continue
            for f in files:
                if f.endswith('.py'):
                    # convert PKGPATH/subpackage/module.py -> subpackage.module
                    # works at any level of nesting
                    name = (mod_or_pkg.__name__ + cwd[n:].replace(os.sep, '.') +
                            '.' + os.path.basename(f[:-3]))
                    mod = importlib.import_module(name)
                    out.update(_long_funcs(mod, maxlen))
    else:  # is a module
        out.update(_long_funcs(mod_or_pkg, maxlen))
    return sorted(out, key=lambda x: x[1], reverse=True)


@numba.njit
def check_newlines(bytes):
    """
    :returns: 0 if the newlines are \r\n, 1 for \n and 2 for \r
    """
    n1 = len(bytes) - 1
    for i, byte in enumerate(bytes):
        if byte == LF:
            if (i > 0 and bytes[i-1] != CR) or i == 0:
                return 1  # \n ending
        elif byte == CR:
            if (i < n1 and bytes[i+1] != LF) or i == n1:
                return 2  # \r ending
    return 0


def test_serious_violations():
    try:
        from flake8.main import application
    except ImportError:
        raise unittest.SkipTest('no flake8 installed')

    app = application.Application()
    buf = io.BytesIO()
    with redirect_stdout(buf) as out:
        out.buffer = buf
        app.run([REPO, '--select', 'F82'])
    assert out.getvalue().decode('utf8') == ''


# cut & paste from github cause the following character to creep inside
# the codebase
def test_annoying_character():
    object_replacement_character = b'\xef\xbf\xbc'
    for cwd, dirs, files in os.walk(REPO):
        for f in files:
            fname = os.path.abspath(os.path.join(cwd, f))
            if os.path.exists(fname) and fname.endswith(
                    ('changelog', '.txt', '.md', '.rst', '.csv', '.py')):
                data = open(fname, 'rb').read()
                if object_replacement_character in data:
                    for i, line in enumerate(open(fname, 'rb'), 1):
                        if b'\xef\xbf\xbc' in line:
                            raise ValueError('%s:%d: %s' % (fname, i, line))


def fix_newlines(fname, lines):
    with open(fname, 'wb') as f:
        for line in lines:
            f.write((line + '\r\n').encode('utf8'))


def fix_encoding(fname, encoding):
    with open(fname, newline='', encoding=encoding) as f:
        lines = f.read().splitlines()
    fix_newlines(fname, lines)


# check encoding and newlines
def test_csv(OVERWRITE=False):
    for cwd, dirs, files in os.walk(REPO):
        for f in files:
            if f.endswith('.csv'):
                fname = os.path.abspath(os.path.join(cwd, f))
                # read using universal newlines, check encoding
                with open(fname, newline='', encoding='utf8') as f:
                    try:
                        lines = f.read().splitlines()
                    except UnicodeDecodeError as exc:
                        if OVERWRITE:
                            fix_encoding(fname, 'latin1')
                        else:
                            raise UnicodeDecodeError('%s: %s' % (fname, exc))
                # read in binary, check newlines
                error = check_newlines(open(fname, 'rb').read())
                if error and OVERWRITE:
                    try:
                        fix_newlines(fname, lines)
                    except Exception as exc:
                        raise ValueError('%s: %s' % (fname, exc))
                elif error == 1:
                    raise ValueError('Found \\n line ending in %s' % fname)
                elif error == 2:
                    raise ValueError('Found \\r line ending in %s' % fname)


def test_forbid_long_funcs():
    long_funcs = get_long_funcs('openquake.hazardlib', 100)
    assert not long_funcs, long_funcs
