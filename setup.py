# Copyright (c) 2010-2012, GEM Foundation.
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

Copyright (C) 2010-2012 GEM Foundation.
"""

import os

from distutils.core import setup


version = '0.4'
url = 'http://github.com/gem/nrml'


def _package_data():
    cur_dir = os.getcwd()

    nrml_dir = os.path.join(os.path.dirname(__file__), 'nrml')
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
    name='NRML',
    version=version,
    author='The OpenQuake Team',
    author_email='devops@openquake.org',
    maintainer='Lars Butler',
    maintainer_email='lars@openquake.org',
    url=url,
    description="Natural hazards' Risk Markup Language",
    long_description=__doc__,
    platforms=['any'],
    packages=['nrml'],
    package_data={'nrml': package_data},
)
