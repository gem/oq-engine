# coding=utf-8
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import re
from openquake.risklib.scientific import (
    VulnerabilityFunction, DegenerateDistribution, classical)


__all__ = ["VulnerabilityFunction", "DegenerateDistribution", "classical"]

__version__ = '0.4.0'


def get_commonlib_version():
    """Read the version of commonlib without importing it"""
    version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
    package_init = 'openquake/commonlib/__init__.py'
    for line in open(package_init):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            return version_match.group(1)

assert get_commonlib_version() >= '0.2.0', \
    'You have an old version of commonlib. Please remove it.'
