# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

README = """
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation
"""

PY_MODULES = ['openquake.commands.__main__']

install_requires = [
    'mock >=1.0, <1.4',
    'h5py >=2.2, <2.8',
    'nose >=1.3, <1.4',
    'numpy >=1.8, <1.12',
    'scipy >=0.13, <0.18',
    'psutil >=1.2, <4.5',
    'shapely >=1.3, <1.6',
    'docutils >=0.11, <0.14',
    'decorator >=3.4, <4.1',
    'django >=1.6, <1.11',
    'matplotlib >=1.5, <2.0',
    'requests >=2.2, <2.13',
    # pyshp is fragile, we want only versions we have tested
    'pyshp >=1.2.3, <1.2.11',
    'PyYAML',
]

if sys.version < '3':
    install_requires.append(
        'futures >=2.1, <3.1'
    )

extras_require = {
    'prctl': ["python-prctl ==1.6.1"],
    'rtree':  ["Rtree >=0.8.2, <0.8.4"],
    'celery':  ["celery >=3.1, <4.0"],
    'pam': ["python-pam", "django-pam"],
    'plotting':  [
        'basemap >=1.0',
        'pyproj >=1.9',
    ]
}

setup(
    name="openquake.engine",
    version=version,
    author="GEM Foundation",
    author_email="devops@openquake.org",
    maintainer='GEM Foundation',
    maintainer_email='devops@openquake.org',
    description=("Computes earthquake hazard and risk."),
    license="AGPL3",
    keywords="earthquake seismic hazard risk",
    url=url,
    long_description=README,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Environment :: Console',
        'Environment :: Web Environment',
    ],
    packages=find_packages(exclude=["qa_tests", "qa_tests.*",
                                    "tools",
                                    "openquake.engine.bin",
                                    "openquake.engine.bin.*"]),
    py_modules=PY_MODULES,
    include_package_data=True,
    package_data={"openquake.engine": [
        "openquake.cfg", "README.md",
        "LICENSE", "CONTRIBUTORS.txt"]},
    namespace_packages=['openquake'],
    install_requires=install_requires,
    extras_require=extras_require,
    scripts=['bin/oq'],
    test_loader='openquake.baselib.runtests:TestLoader',
    test_suite='openquake.risklib,openquake.commonlib,openquake.calculators',
    zip_safe=False,
    )
