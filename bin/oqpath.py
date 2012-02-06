# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
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
