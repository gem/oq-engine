# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from distutils.core import setup

scripts = ["bin/%s" % x for x in os.listdir('bin')]
scripts.append('celeryconfig.py')

libs = []
if os.path.exists('lib'):
    for x in os.listdir('lib'):
        if x[-4:] == '.jar':
            libs.append("lib/%s" % x)

dist = []
if os.path.exists('dist'):
    for x in os.listdir('dist'):
        if x[-4:] == '.jar':
            dist.append("dist/%s" % x)
        
with os.popen("which gfortran") as gf:
    if not gf:
        raise EnvironmentError("You need to install gfortran")

setup(name='openquake',
      version='0.11',
      description='OpenQuake Platform',
      author='gem-core',
      author_email='openquake-dev@googlegroups.com',
      url='http://www.openquake.org/',
      packages=['openquake','openquake.hazard',
                'openquake.job','openquake.kvs',
                'openquake.output','openquake.parser',
                'openquake.risk', 'openquake.risk.job'],
      data_files=[('/etc/openquake', ['celeryconfig.py']),
                  ('lib', libs),('dist', dist)],
      scripts=scripts,
      install_requires=["pyyaml", "shapely", "python-gflags",
                        "lxml", "sphinx", "guppy", "libLAS",
                        "numpy", "scipy", "celery", "nose", "django"])
