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
