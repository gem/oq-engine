# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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

import os
import re
import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 9):
    sys.exit('Sorry, Python < 3.9 is not supported')


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


def get_readme():
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'README.md'), encoding='utf-8') as readme:
        return readme.read()


version = get_version()
readme = get_readme()

url = "https://github.com/gem/oq-engine"

PY_MODULES = ['openquake.commands.__main__']

install_requires = [
    'setuptools',
    'h5py >=2.10',
    'numpy >=1.20',
    'numba >=0.58',
    'scipy >=1.3',
    'pandas >=0.25',
    'pyzmq >=19.0',
    'psutil >=2.0',
    'shapely >=1.7',
    'docutils >=0.11',
    'decorator >=4.3',
    'django >=4.2, <5',
    'matplotlib',
    'requests >=2.20',
    'toml >=0.10.2',
    'pyproj >=1.9',
    'alpha_shapes >= 1.1.0'
]

# NOTE: to build documentation, see doc/requirements.txt
extras_require = {
    'dev':  [
        'pytest >=4.5',
        'flake8 >=3.5',
        'pdbpp',
        'ipython',
        'silx',
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
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Environment :: Console',
        'Environment :: Web Environment',
    ],
    packages=find_packages(exclude=["qa_tests", "qa_tests.*",
                                    "tools",
                                    "*.*.tests", "*.*.tests.*",
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
    entry_points={
        'console_scripts': ['oq = openquake.commands.__main__:oq'],
    },
    test_loader='openquake.baselib.runtests:TestLoader',
    test_suite='openquake.risklib,openquake.commonlib,openquake.calculators',
    zip_safe=False,
    )
