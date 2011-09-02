# Copyright (c) 2010-2011, GEM Foundation.
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
OpenQuake is an open-source platform for the calculation of hazard, risk,
and socio-economic impact. It is a project of the Global Earthquake Model,
nd may be extended by other organizations to address additional classes
of peril.

For more information, please see the website at http://www.globalquakemodel.org
This software may be downloaded at http://github.com/gem/openquake

The continuous integration server is at
    http://openquake.globalquakemodel.org

Up-to-date sphinx documentation is at
    http://openquake.globalquakemodel.org/docs

This software is licensed under the LGPL license, for more details
please see the LICENSE file.

Copyright (c) 2010, GEM Foundation.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

# Please note: the release date should always have a value of 0 (zero) in the
# master branch. It will only be set to a meaningful value in *packaged* and
# released OpenQuake code.
__version__ = (
    0,  # major
    4,  # minor
    3,  # sprint number
    0)  # release date (seconds since the "Epoch"), do *not* set in master!

# The path to the OpenQuake root directory
OPENQUAKE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
