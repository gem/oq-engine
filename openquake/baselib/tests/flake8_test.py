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
