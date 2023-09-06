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
import unittest
from contextlib import redirect_stdout

REPO = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__))))


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


def test_csv_endlines():

    # change to True to add final endlines where absent
    FIX_FINAL_ENDLINES = False

    # change to True to replace \n with \r\n where needed
    FIX_LF_TO_CRLF = False

    # change to True to replace \r with \r\n where needed
    FIX_CR_TO_CRLF = False

    only_slash_r_endlines = []
    only_slash_n_endlines = []
    no_endlines = []
    for cwd, dirs, files in os.walk(REPO):
        for f in files:
            fname = os.path.abspath(os.path.join(cwd, f))
            if fname.endswith('.csv'):
                for i, line in enumerate(open(fname, 'rb'), 1):
                    if not line.endswith(b'\r\n'):
                        # raise ValueError('%s:%d: %s' % (fname, i, line))
                        if line.endswith(b'\n'):
                            only_slash_n_endlines.append(fname)
                        elif line.endswith(b'\r'):
                            only_slash_r_endlines.append(fname)
                        else:
                            no_endlines.append(fname)
                        break
    if only_slash_r_endlines or only_slash_n_endlines or no_endlines:
        err_msg = ''
        if only_slash_r_endlines:
            err_msg += f'Only \\r were found in:\n{only_slash_r_endlines}'
        if only_slash_n_endlines:
            err_msg += f'Only \\n were found in:\n{only_slash_n_endlines}'
        if no_endlines:
            err_msg += f'No endlines were found in:\n{no_endlines}'
        if FIX_FINAL_ENDLINES:
            for fname in no_endlines:
                with open(fname, 'a') as f:
                    f.write('\r\n')
        if FIX_LF_TO_CRLF:
            for fname in only_slash_n_endlines:
                with open(fname, 'r') as f:
                    contents = f.read()
                contents = contents.replace('\n', '\r\n')
                with open(fname, 'w') as f:
                    f.write(contents)
        if FIX_CR_TO_CRLF:
            for fname in only_slash_r_endlines:
                with open(fname, 'r') as f:
                    contents = f.read()
                contents = contents.replace('\r', '\r\n')
                with open(fname, 'w') as f:
                    f.write(contents)
        raise ValueError(err_msg)
