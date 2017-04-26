# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation, G. Weatherill, M. Pagani
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

    package_init = 'openquake/hazardlib/__init__.py'
    for line in open(package_init, 'r'):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            version = version_match.group(1)
            break
    else:
        sys.exit('__version__ variable not found in %s' % package_init)

    return version
version = get_version()

url = "http://github.com/gem/oq-hazardlib"

README = """
hazardlib includes modules for modeling seismic sources (point, area and
fault), earthquake ruptures, temporal (e.g. Poissonian) and magnitude
occurrence models (e.g. Gutenberg-Richter), magnitude/area scaling
relationships, ground motion and intensity prediction equations (i.e. GMPEs and
IPEs). Eventually it will offer a number of calculators for hazard curves,
stochastic event sets, ground motion fields and disaggregation histograms.

hazardlib aims at becoming an open and comprehensive tool for seismic hazard
analysis. The GEM Foundation (http://www.globalquakemodel.org/) supports
the development of the  library by adding the most recent methodologies
adopted by the seismological/seismic hazard communities. Comments,
suggestions and criticisms from the community are always very welcome.

Copyright (C) 2014-2017 GEM Foundation
"""

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
    'matplotlib >=1.5',
    'PyYAML',
]

if sys.version < '3':
    install_requires.append(
        'futures >=2.1, <3.1'
    )

extras_require = {
    'rtree':  ["Rtree >=0.8.2, <0.8.4"],
    'plotting':  [
        'basemap >=1.0',
        'pyproj >=1.9',
    ]
}

setup(
    name='openquake.hazardlib',
    version=version,
    description="hazardlib is a library for performing seismic "
    "hazard analysis",
    long_description=README,
    url=url,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=install_requires,
    extras_require=extras_require,
    scripts=['openquake/hazardlib/tests/gsim/check_gsim.py'],
    author='GEM Foundation',
    author_email='devops@openquake.org',
    maintainer='GEM Foundation',
    maintainer_email='devops@openquake.org',
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
    keywords="seismic hazard",
    license="AGPL3",
    platforms=["any"],
    package_data={"openquake.hazardlib": [
        "README.md", "LICENSE", "CONTRIBUTORS.txt"]},
    namespace_packages=['openquake'],
    include_package_data=True,
    test_loader='openquake.baselib.runtests:TestLoader',
    test_suite='openquake.baselib,openquake.hazardlib',
    zip_safe=False,
)
