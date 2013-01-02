# oq-risklib: The Risk Library
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
oq-risklib needs a description.

Comments, suggestions and criticisms from the community are always
very welcome.

Copyright (C) 2012 GEM Foundation.
"""
from setuptools import setup, find_packages


version = "0.1.0"
url = "http://github.com/gem/oq-risklib"


setup(
    name='oq-risklib',
    version=version,
    description="oq-risklib is a library for performing seismic risk analysis",
    long_description=__doc__,
    url=url,
    packages=find_packages(exclude=['tests', 'tests.*']),
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
    keywords="seismic risk",
    license="GNU AGPL v3",
    platforms=["any"]
)
