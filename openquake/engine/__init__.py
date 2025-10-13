# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
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

"""
OpenQuake is an open-source platform for the calculation of hazard and risk
impact. It is a project of the Global Earthquake Model, and may be extended
by other organizations to address additional classes of peril.

For more information, please see the website at http://www.globalquakemodel.org
This software may be downloaded at http://github.com/gem/openquake

The continuous integration server is at
    https://ci.openquake.org

Up-to-date sphinx documentation is at
    http://docs.openquake.org

This software is licensed under the AGPL license, for more details
please see the LICENSE file.

Copyright (C) 2010-2025 GEM Foundation

OpenQuake is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenQuake is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
from openquake.baselib import __version__  # noqa

# The path to the OpenQuake root directory
OPENQUAKE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
