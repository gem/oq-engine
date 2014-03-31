# -*- coding: utf-8 -*-

# Copyright (c) 2010-2014, GEM Foundation.
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

"""
Helper code to set up system path values properly (for bin/ scripts).
"""

import os
import sys


def set_oq_path():
    """
    Adds the current directory to the system PATH so scripts can be run from
    root source dir.
    """
    if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                  'openquake')):
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
