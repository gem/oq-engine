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
    if not os.path.exists(CHECKOUT_DIR):
        repo = Repo.clone_from(REPO_URL, CHECKOUT_DIR)
        # git = Git()
        # Make sure there's a checkout and it's up to date (of OpenGemModel)
    job_path = os.path.join(CHECKOUT_DIR, "tests", sys.argv[1], "config.gem")
    print job_path
    job.run_job(job_path)