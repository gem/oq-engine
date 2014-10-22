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

Copyright (c) 2010-2014, GEM Foundation.

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
import subprocess


def git_suffix():
    """
    extract short git hash if runned from sources

    :returns:
        `<short git hash>` if git repository found

        `""` otherwise.
    """
    old_dir = os.getcwd()
    py_dir = os.path.dirname(__file__)
    os.chdir(py_dir)
    try:
        FNULL = open(os.devnull, 'w')
        # with this fix we are missing the case where we are really in git
        # installation scenario but, for some reason, git not works properly
        # and not return the hash but it is an acceptable compromise
        process = subprocess.Popen(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stdout=subprocess.PIPE, stderr=FNULL)
        output = process.communicate()[0]
        os.chdir(old_dir)
        return "-git" + output
    except Exception:
        # trapping everything on purpose
        os.chdir(old_dir)
        return ''

# version number follows the syntax <major>.<minor>.<patchlevel>[<suffix>]
# where major, minor and patchlevel are numbers.
# suffix follows the ubuntu versioning rules.
# for development version suffix is:
#  "-" + <pkg-version> + "+dev" + <secs_since_epoch> + "-" + <commit-id>
# NB: the next line is managed by packager.sh script (we retrieve the version
#     using sed and optionally replace it)
__version__ = '1.2.0'
__version__ += git_suffix()

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
    if nd:
        return nd.lower() in ("true", "yes", "t", "1")


def set_django_settings_module():
    if not os.getenv('DJANGO_SETTINGS_MODULE', False):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'openquake.engine.settings'

set_django_settings_module()
