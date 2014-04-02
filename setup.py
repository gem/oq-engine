# NRML: Natural hazards' Risk Markup Language
# Copyright (c) 2010-2014, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

"""
Natural hazards' Risk Markup Language (NRML) is a collection XML schema
definitions for modelling inputs and outputs for seismic hazard and risk
analysis.

NRML also includes a library of parsers and serializers for reading from and
writing to NRML XML artifacts.

NRML was created as part of the Global Earthquake Model
(http://www.globalquakemodel.org/) initiative and is meant to be the canonical
exchange format definition for the OpenQuake Engine (http://www.openquake.org/)
and related software.

Copyright (c) 2010-2014, GEM Foundation.
"""

import os
import sys
import re
from setuptools import setup, find_packages

for line in open('openquake/nrmllib/__init__.py'):
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    version = re.search(VSRE, line, re.M)
    if version:
        break
else:
    sys.exit('variable __version__ not found in openquake/nrmllib/__init__.py')
version = version.group(1)

url = 'http://github.com/gem/oq-nrmllib'


def _package_data():
    cur_dir = os.getcwd()

    nrml_dir = os.path.join(os.path.dirname(__file__), 'openquake/nrmllib')
    os.chdir(nrml_dir)

    try:
        # Gets all .xsd and .xsl files in the 'nrml/schema' dir:
        package_data = [
            os.path.join(root, '*.xs*') for root, _, _ in os.walk('schema')
        ]
    finally:
        os.chdir(cur_dir)

    return package_data

package_data = _package_data()

setup(
    name='openquake.nrmllib',
    version=version,
    maintainer='The OpenQuake Team',
    maintainer_email='devops@openquake.org',
    url=url,
    description="Natural hazards' Risk Markup Language",
    long_description=__doc__,
    platforms=['any'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'openquake.nrmllib': package_data},
    requires=['lxml'],  # Shows up when running `python setup.py --requires`
    provides=['nrml (0.4)'],
    install_requires=['lxml'],
    license='GNU AGPL v3',
    keywords='seismic hazard risk',
    classifiers=(
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Financial and Insurance Industry',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
    ),
    namespace_packages=['openquake'],

    zip_safe=False,

)
