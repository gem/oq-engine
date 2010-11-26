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

import glob
import os
import sys

from distutils.core import setup
from setuptools import find_packages

scripts = ["bin/%s" % x for x in os.listdir('bin')]
scripts.extend(
    ["openquake/utils/%s" % x for x in os.listdir('openquake/utils')])
libs = []
for x in os.listdir('lib'):
    if x[-4:] == '.jar':
        libs.append("lib/%s" % x)
        
with os.popen("which gfortran") as gf:
    if not gf:
        raise EnvironmentError("You need to install gfortran")

setup(name='openquake',
      version='0.1.0',
      description='OpenQuake Platform',
      author='gem-core',
      author_email='openquake-dev@googlegroups.com',
      url='http://www.openquake.org/',
      packages=['openquake','openquake.hazard',
                'openquake.job','openquake.kvs',
                'openquake.output','openquake.parser',
                'openquake.risk', 'openquake.risk.job',
                'openquake.seismicsources'],
      data_files=[('/etc/openquake', ['celeryconfig.py']),
                  ('lib', libs),],
      scripts=scripts,
      install_requires=["pyyaml", "shapely", "python-gflags", "pylibmc==0.9.2",
                        "lxml", "sphinx", "eventlet", "guppy", "libLAS",
                        "numpy", "scipy", "celery", "nose", "django",
                        "ordereddict"])
