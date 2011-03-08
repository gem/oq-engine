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



#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""Runs a classical PSHA hazard computation

Expects to compute:
    hazard curves in NRML
    ground motion fields in GeoTIFF

"""

import sys

import openquake.hazard.job

from openquake import flags
from openquake import logs

from openquake import job
from openquake.job import mixins

FLAGS = flags.FLAGS

flags.DEFINE_string('config_file', 'openquake-config.gem', 'OpenQuake configuration file')

if __name__ == '__main__':
    args = FLAGS(sys.argv)
    logs.init_logs()

    engine = job.Job.from_file(FLAGS.config_file)

    with mixins.Mixin(engine, openquake.hazard.job.HazJobMixin, key="hazard"):
        engine.execute()
