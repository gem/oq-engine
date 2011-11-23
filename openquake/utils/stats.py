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
Utility functions related to keeping job progress information and statistics.
"""

from functools import wraps
import redis

from openquake.utils import config


def _redis():
    """Return a connection to the redis store."""
    host = config.get("kvs", "host")
    port = config.get("kvs", "port")
    port = int(port) if port else 6379
    stats_db = config.get("kvs", "stats_db")
    stats_db = int(stats_db) if stats_db else 15
    args = {"host": host, "port": port, "db": stats_db}
    return redis.Redis(**args)


def key_name(job_id, func, area="h", counter_type="i"):
    """Return the redis key name for the given job/function."""
    return "oqs:%s:%s:%s:%s" % (job_id, area, counter_type, func)


def progress_indicator(func):
    """Count successful/failed invocations of the wrapped function."""

    def find_job_id(*args, **kwargs):
        """Find and return the job_id."""
        if len(args) > 0:
            return args[0]
        else:
            return kwargs.get("job_id", -1)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """The actual decorator."""
        # The first argument is always the job_id
        job_id = find_job_id(*args, **kwargs)
        key = key_name(job_id, func.__name__)
        conn = _redis()
        try:
            result = func(*args, **kwargs)
            conn.incr(key)
            return result
        except:
            # Count failure
            conn.incr(key + ":f")
            raise

    return wrapper


def set_total(job_id, key, value):
    """Set a total value for the given key."""
    key = key_name(job_id, key, counter_type="t")
    conn = _redis()
    conn.set(key, value)


def incr_counter(job_id, key):
    """Increment the counter for the given key."""
    key = key_name(job_id, key)
    conn = _redis()
    conn.incr(key)


def delete_job_counters(job):
    """Delete the progress indication counters for the given job."""
    conn = _redis()
    keys = conn.keys("oqs:%s*" % job)
    if keys:
        conn.delete(*keys)
