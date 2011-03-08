# Copyright (c) 2011, GEM Foundation.
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

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
A smoketest suite running framework.

Usage Examples:

    # to run a single suite
    python smoketest.py examplesuitename

    # to run a suite not from the OpenGemModel
    python run_tests.py git@github.com:gem/otherrepo.git/othersuite
"""

import os
import sys
import unittest

import git
from git import Git, Repo

from openquake import logs
from openquake import flags
from openquake import job

from openquake.hazard import job as hazjob
from openquake.hazard import opensha
from openquake.risk import job as riskjob
from openquake.risk.job import probabilistic
FLAGS = flags.FLAGS

CHECKOUT_DIR = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../OpenGemModel'))

REPO_URL = "git@github.com:gem/OpenGemModel.git"

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)  
    logs.init_logs()
    
    # Make sure there's a checkout and it's up to date (of OpenGemModel)
    if not os.path.exists(CHECKOUT_DIR):
        repo = Repo.clone_from(REPO_URL, CHECKOUT_DIR)
    job_path = os.path.join(CHECKOUT_DIR, "tests", sys.argv[1], "config.gem")
    job.run_job(job_path)