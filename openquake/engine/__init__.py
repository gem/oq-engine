# Copyright (c) 2010-2013, GEM Foundation.
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

This software is licensed under the AGPL license, for more details
please see the LICENSE file.

Copyright (c) 2010-2013, GEM Foundation.

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
from openquake.engine.utils import general as general_utils

# Please note: the release date should always have a value of 0 (zero) in the
# master branch. It will only be set to a meaningful value in *packaged* and
# released OpenQuake code.
__version_tuple__ = (
    1,  # major
    0,  # minor
    0,  # sprint number
    0)  # release date (seconds since the "Epoch"), do *not* set in master!

__version__ = '.'.join(str(x) for x in __version_tuple__[:3])

# The path to the OpenQuake root directory
OPENQUAKE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

NO_DISTRIBUTE_VAR = 'OQ_NO_DISTRIBUTE'


def no_distribute():
    """
    Check the `OQ_NO_DISTRIBUTE` environment var to determine if calculations
    should be distributed or not.

    :returns:
        `True` if the envvar value is "true", "yes", "t", or "1", regardless of
        case. Otherwise, return `False`.

        If the variable is undefined, it defaults to `False`.
    """
    nd = os.environ.get(NO_DISTRIBUTE_VAR)

    if nd is None:
        return False
    else:
        return general_utils.str2bool(nd)


def set_django_settings_module():
    if not os.getenv('DJANGO_SETTINGS_MODULE', False):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'openquake.engine.settings'

set_django_settings_module()
