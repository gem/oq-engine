# oq-commonlib: The Common Library
# Copyright (C) 2013 GEM Foundation
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
oq-commonlib FIXME: needs a description.

Comments, suggestions and criticisms from the community are always
very welcome.

Copyright (C) 2014 GEM Foundation.
"""
import os
import re
import sys
from setuptools import setup, find_packages


def get_version():
    version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
    version = None

    package_init = 'openquake/commonlib/__init__.py'
    for line in open(package_init, 'r'):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            version = version_match.group(1)
            break
    else:
        sys.exit('__version__ variable not found in %s' % package_init)

    return version
version = get_version()

url = "http://github.com/gem/oq-commonlib"
cd = os.path.dirname(os.path.join(__file__))

setup(
    name='openquake.commonlib',
    version=version,
    description="oq-commonlib is FIXME",
    long_description=__doc__,
    url=url,
    packages=find_packages(exclude=[
        'tests', 'tests.*', 'qa_tests', 'qa_tests.*']),
    install_requires=[
        'numpy',
        'scipy'
    ],
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
    keywords="seismic common",
    license="GNU AGPL v3",
    platforms=["any"],
    namespace_packages=['openquake'],

    zip_safe=False,
)
