# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
from openquake.commonlib import readinput

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class DifferentFiles(Exception):
    """Raised for different files"""


def get_oqparam(ini):
    """
    Read OqParam from an ini file in the tests/data directory
    """
    return readinput.get_oqparam(os.path.join(DATADIR, ini))


def check_equal(filepath, expected, actual_path):
    """
    Compare two files for equality of content. Usage:

    >> check_equal(__file__, 'expected.xml', 'actual.xml')
    """
    expected_path = os.path.join(os.path.dirname(filepath), expected)
    expected_content = open(expected_path).read()
    actual_content = open(actual_path).read()
    if expected_content != actual_content:
        raise DifferentFiles('%s %s' % (expected_path, actual_path))
