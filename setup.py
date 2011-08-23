# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import os

import openquake

from setuptools import setup

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

setup(
    name='openquake',
    version='.'.join(str(x) for x in openquake.__version__[:3]),
    description='OpenQuake Platform',
    author='gem-core',
    author_email='openquake-dev@googlegroups.com',
    url='http://www.openquake.org/',
    packages=[
        'openquake', 'openquake.hazard',
        'openquake.job', 'openquake.kvs',
        'openquake.output', 'openquake.parser',
        'openquake.risk', 'openquake.risk.job'],
    data_files=[
        ('/etc/openquake', ['celeryconfig.py']),
        ('lib', libs),
        ('dist', dist)],
    scripts=scripts,
    install_requires=[
        "shapely", "python-gflags", "lxml", "sphinx", "guppy", "numpy",
        "scipy", "celery", "nose", "django"])
