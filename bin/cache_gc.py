#!/usr/bin/env python
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


"""
This tool is used for performing garbage collection on OpenQuake KVS cache
data.

  -h | --help   : prints this help string
  -j | --job J  : clear KVS cache data for the given job ID
  -l | --list   : list currently cached jobs
"""

import getopt
import sys

import oqpath
oqpath.set_oq_path()

from openquake import job
from openquake import kvs
from openquake.utils import config


SHORT_ARGS = 'hlj:'
LONG_ARGS = ['help', 'job=', 'list']
# map short args to long args
S2L = dict(h='help', j='job', l='list')


def main(cl_args):
    """
    :param cl_args: command line arguments
    :type cl_cargs: list of strings
    """
    try:
        opts, _ = getopt.getopt(cl_args, SHORT_ARGS, LONG_ARGS)
    except getopt.GetoptError, e:
        # Invalid arg specified; print the error and help, then exit
        print e
        show_help()

    # strip dashes
    opts = [(strip_dashes(opt), val) for opt, val in opts]

    # convert everything to long args
    opts = [(S2L.get(opt, opt), val) for opt, val in opts]

    # process the args in the order they were given
    # some arguments may be ignored
    for opt, val in opts:
        if opt == 'help':
            show_help()
        elif opt == 'list':
            list_cached_jobs()
            break
        elif opt == 'job':
            clear_job_data(val)
            break
        else:
            print "Unknown option: %s" % opt
            show_help()


def strip_dashes(arg):
    """
    Remove leading dashes, return last portion of string remaining.
    """
    return arg.split('-')[-1]


def _get_current_job_ids():
    """
    Get a list of the current jobs from the KVS and parse out the numeric job
    IDs.

    :returns: list of ints
    """
    jobs = [int(x) for x in kvs.current_jobs()]

    return sorted(jobs)


def list_cached_jobs():
    """
    List the jobs which are currently cached in the KVS.

    Invoked by the -l or --list command line arg.
    """
    job_ids = _get_current_job_ids()

    if len(job_ids) > 0:
        # print the jobs
        print 'Currently cached jobs:'
        for job in job_ids:
            print job

    else:
        # there are no jobs
        print 'There are currently no jobs cached.'


def clear_job_data(job_id):
    """
    Clear KVS cache data for the given job. This is done by searching in the
    KVS for keys matching a job key (derived from the job_id) and deleting each
    result.

    Invoked by the -j or --job command line arg.

    :param job_id: job ID as an integer
    """

    try:
        job_id = int(job_id)
    except ValueError:
        print 'Job ID should be an integer.'
        print 'Use the --list option to show current jobs.'
        raise

    logs.init_logs(level='info', log_type=config.get("logging", "backend"))

    logger = job.Job.get_logger_for(job_id)
    logger.info('Attempting to clear cache data...')

    result = kvs.cache_gc(job_id)

    if result is None:
        logger.info('Job not found.')
    else:
        logger.info('Removed %s keys.', result)


def show_help():
    """
    Display help documentation for this utility and exit.
    """
    print __doc__
    sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])
