# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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

import re
import sys
from setuptools import setup, find_packages


def get_version():
    version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
    version = None

    package_init = 'openquake/baselib/__init__.py'
    for line in open(package_init, 'r'):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            version = version_match.group(1)
            break
    else:
        sys.exit('__version__ variable not found in %s' % package_init)

    return version

version = get_version()

url = "https://github.com/gem/oq-engine"

install_requires = [
    'mock >=1.0, <1.4',
    'h5py >=2.2, <2.8',
    'numpy >=1.8, <1.12',
    'psutil >=1.2, <4.5',
    'decorator >=3.4, <4.1',
]

if sys.version < '3':
    install_requires.append(
        'futures >=2.1, <3.1'
    )

setup(
    name="openquake.baselib",
    version=version,
    author="GEM Foundation",
    author_email="devops@openquake.org",
    maintainer='GEM Foundation',
    maintainer_email='devops@openquake.org',
    description=("Basic libraries for parallelization, XML, etc"),
    license="AGPL3",
    keywords="parallel programming",
    url=url,
    long_description="Basic libraries for parallelization, XML, etc",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
    ],
    packages=find_packages(),
    namespace_packages=['openquake'],
    install_requires=install_requires,
    zip_safe=False,
    )
