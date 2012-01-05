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


STATS_KEYS = {
    # Classical PSHA kvs statistics db keys, "t" and "i" mark a totals
    # and an incremental counter respectively.
    "hcls_realizations": ("classical:realizations", "h", "t"),
    "hcls_crealization": ("classical:crealization", "h", "i"),
    "hcls_sites": ("classical:sites", "h", "t"),
    "hcls_block_size": ("classical:block_size", "h", "t"),
    "hcls_blocks": ("classical:blocks", "h", "t"),
    "hcls_cblock": ("classical:cblock", "h", "i"),
}


def pk_set(job_id, skey, value):
    """Set the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    :param value: the desired value
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    conn = _redis()
    conn.set(key, value)


def pk_inc(job_id, skey):
    """Increment the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    conn = _redis()
    conn.incr(key)


def pk_get(job_id, skey):
    """Get the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    conn = _redis()
    return conn.get(key)


def _redis():
    """Return a connection to the redis store."""
    host = config.get("kvs", "host")
    port = config.get("kvs", "port")
    port = int(port) if port else 6379
    stats_db = config.get("kvs", "stats_db")
    stats_db = int(stats_db) if stats_db else 15
    args = {"host": host, "port": port, "db": stats_db}
    return redis.Redis(**args)


def key_name(job_id, fragment, area="h", counter_type="i"):
    """Return the redis key name for the given job/function.

    The areas in use are 'h' (for hazard) and 'r' (for risk).
    The counter types in use are 'i' (for incremental counters) and
    't' (for totals).
    """
    return "oqs:%s:%s:%s:%s" % (job_id, area, counter_type, fragment)


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


def get_counter(job_id, key, counter_type="i"):
    """Get the value for the given key.

    The counter types in use are 'i' (for incremental counters) and
    't' (for totals).
    """
    key = key_name(job_id, key, counter_type=counter_type)
    conn = _redis()
    value = conn.get(key)
    return int(value) if value else value


def delete_job_counters(job_id):
    """Delete the progress indication counters for the given `job_id`."""
    conn = _redis()
    keys = conn.keys("oqs:%s*" % job_id)
    if keys:
        conn.delete(*keys)
