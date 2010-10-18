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
    ["opengem/utils/%s" % x for x in os.listdir('opengem/utils')])
libs = []
for x in os.listdir('lib'):
    if x[-4:] == '.jar':
        libs.append("lib/%s" % x)

setup(name='opengem',
      version='0.1.0',
      description='OpenGEM Platform',
      author='gem-core',
      author_email='opengem-dev@googlegroups.com',
      url='http://www.opengem.org/',
      packages=['opengem','opengem.hazard','opengem.risk',
                'opengem.output','opengem.parser', 'opengem.seismicsources'],
      data_files=[('/etc/opengem', ['celeryconfig.py']),
                  ('lib', libs),],
      scripts=scripts,
      requires=['lxml','shapely',"gflags",'pylibmc(==0.9.2)'],
     )
