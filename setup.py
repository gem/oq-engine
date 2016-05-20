# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2016 GEM Foundation
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


def get_version():
    version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
    version = None

    package_init = 'openquake/risklib/__init__.py'
    for line in open(package_init, 'r'):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            version = version_match.group(1)
            break
    else:
        sys.exit('__version__ variable not found in %s' % package_init)

    return version
version = get_version()

url = "http://github.com/gem/oq-risklib"

cd = os.path.dirname(os.path.join(__file__))

setup(
    name='openquake.risklib',
    version=version,
    description="oq-risklib is a library for performing seismic risk analysis",
    long_description=open(os.path.join(cd, 'README.md')).read(),
    url=url,
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'decorator',
        'psutil >= 0.4.1',
    ],
    author='GEM Foundation',
    author_email='devops@openquake.org',
    maintainer='GEM Foundation',
    maintainer_email='devops@openquake.org',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
    ),
    keywords="seismic risk",
    license="AGPL3",
    platforms=["any"],
    package_data={"openquake.risklib": [
        "README.md", "LICENSE"]},
    entry_points={
        'console_scripts': [
            'oq-lite = openquake.commonlib.commands.__main__:oq_lite']},
    namespace_packages=['openquake'],
    include_package_data=True,
    test_loader='openquake.baselib.runtests:TestLoader',
    test_suite='openquake.risklib,openquake.commonlib,openquake.calculators',
    zip_safe=False,
)
