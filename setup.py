# The Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
hazardlib includes modules for modeling seismic sources (point, area and fault),
earthquake ruptures, temporal (e.g. Poissonian) and magnitude occurrence
models (e.g. Gutenberg-Richter), magnitude/area scaling relationships,
ground motion and intensity prediction equations (i.e. GMPEs and IPEs).
Eventually it will offer a number of calculators for hazard curves,
stochastic event sets, ground motion fields and disaggregation histograms.

hazardlib aims at becoming an open and comprehensive tool for seismic hazard
analysis. The GEM Foundation (http://www.globalquakemodel.org/) supports
the development of the  library by adding the most recent methodologies
adopted by the seismological/seismic hazard communities. Comments,
suggestions and criticisms from the community are always very welcome.

Copyright (C) 2012-2013 GEM Foundation.
"""
import re
import sys
from setuptools import setup, find_packages, Extension

import numpy


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

geoutils_speedups = Extension('openquake.hazardlib.geo._utils_speedups',
                              sources=['speedups/geoutilsmodule.c'],
                              extra_compile_args=['-Wall', '-O2'])
geodetic_speedups = Extension('openquake.hazardlib.geo._geodetic_speedups',
                              sources=['speedups/geodeticmodule.c'],
                              extra_compile_args=['-Wall', '-O2'])

include_dirs = [numpy.get_include()]


setup(
    name='openquake.hazardlib',
    version=version,
    description="hazardlib is a library for performing seismic hazard analysis",
    long_description=__doc__,
    url=url,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'numpy',
        'scipy',
        'shapely'
    ],
    ext_modules=[geodetic_speedups, geoutils_speedups],
    include_dirs=include_dirs,
    scripts=['openquake/hazardlib/tests/gsim/check_gsim.py'],
    maintainer='GEM',
    maintainer_email='info@openquake.org',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
    ),
    keywords="seismic hazard",
    license="GNU AGPL v3",
    platforms=["any"],
    namespace_packages=['openquake'],

    zip_safe=False,

)
