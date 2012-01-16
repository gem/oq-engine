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


# Predefined kvs keys for calculator progress/statistics counters.
# Calculators will maintain totals/incremental counter values of interest.
# These can be used to provide feedback to the user and/or terminate the
# job in case of failures. See e.g.
#   https://bugs.launchpad.net/openquake/+bug/907703
STATS_KEYS = {
    # Predefined calculator statistics keys for the kvs.
    # The areas are as follows:
    #   "g" : general
    #   "h" : hazard
    #   "r" : risk
    # The counter types are as follows:
    #   "d" : debug counter, turned off in production via openquake.cfg
    #   "i" : incremental counter
    #   "t" : totals counter
    # The total number of realizations
    "hcls_realizations": ("h", "cls:realizations", "t"),
    # Current realization
    "hcls_crealization": ("h", "cls:crealization", "i"),
    # The total number of sites
    "hcls_sites": ("h", "cls:sites", "t"),
    # The block size to use
    "block_size": ("g", "gen:block_size", "t"),
    # The total number of blocks
    "blocks": ("g", "gen:blocks", "t"),
    # The current block
    "cblock": ("g", "gen:cblock", "i"),
    # debug statistic: list of paths of hazard curves written to xml
    "hcls_xmlcurvewrites": ("h", "cls:debug:xmlcurvewrites", "d"),
    # debug statistic: list of paths of hazard maps written to xml
    "hcls_xmlmapwrites": ("h", "cls:debug:xmlmapwrites", "d"),
}


# Predefined key template, order of substitution variables:
#   job_id, area, fragment, counter_type.
_KEY_TEMPLATE = "oqs/%s/%s/%s/%s"


def kvs_op(dop, *kvs_args):
    """Apply the kvs operation using the predefined key.

    :param string dop: the kvs operation desired
    :param tuple kvs_args: the positional arguments for the desired kvs
        operation
    :param value: whatever is retured by the kvs operation
    """
    conn = _redis()
    op = getattr(conn, dop)
    return op(*kvs_args)


def pk_set(job_id, skey, value):
    """Set the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    :param value: the desired value
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    if not key:
        return
    kvs_op("set", key, value)


def pk_inc(job_id, skey):
    """Increment the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    if not key:
        return
    kvs_op("incr", key)


def pk_get(job_id, skey, cast2int=True):
    """Get the value for a predefined statistics key.

    :param int job_id: identifier of the job in question
    :param string skey: predefined statistics key
    :param bool cast2int: whether the values should be cast to integers
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    if not key:
        return
    return int(kvs_op("get", key)) if cast2int else kvs_op("get", key)


def _redis():
    """Return a connection to the redis store."""
    host = config.get("kvs", "host")
    port = config.get("kvs", "port")
    port = int(port) if port else 6379
    stats_db = config.get("kvs", "stats_db")
    stats_db = int(stats_db) if stats_db else 15
    args = {"host": host, "port": port, "db": stats_db}
    return redis.Redis(**args)


def key_name(job_id, area, fragment, counter_type):
    """Return the redis key name for the given job/function.

    The areas in use are 'h' (for hazard) and 'r' (for risk). The counter
    types in use are:
        "d" : debug counter, turned off in production via openquake.cfg
        "i" : incremental counter
        "t" : totals counter
    """
    if counter_type == "d" and not debug_stats_enabled():
        return None
    return _KEY_TEMPLATE % (job_id, area, fragment, counter_type)


class progress_indicator(object):   # pylint: disable=C0103
    """Count successful/failed invocations of the wrapped function."""

    def __init__(self, area):
        self.area = area
        self.__name__ = "progress_indicator"

    @staticmethod
    def find_job_id(*args, **kwargs):
        """Find and return the job_id."""
        if len(args) > 0:
            return args[0]
        else:
            return kwargs.get("job_id", -1)

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            """The actual decorator."""
            # The first argument is always the job_id
            job_id = self.find_job_id(*args, **kwargs)
            conn = _redis()
            try:
                result = func(*args, **kwargs)
                key = key_name(job_id, self.area, func.__name__, "i")
                conn.incr(key)
                return result
            except:
                # Count failure
                key = key_name(
                    job_id, self.area, func.__name__ + "-failures", "i")
                conn.incr(key)
                raise

        return wrapper


def set_total(job_id, area, fragment, value):
    """Set a total value for the given key."""
    key = key_name(job_id, area, fragment, "t")
    kvs_op("set", key, value)


def incr_counter(job_id, area, fragment):
    """Increment the counter for the given key."""
    key = key_name(job_id, area, fragment, "i")
    kvs_op("incr", key)


def get_counter(job_id, area, fragment, counter_type):
    """Get the value for the given key.

    The areas in use are 'h' (for hazard) and 'r' (for risk). The counter
    types in use are:
        "d" : debug counter, turned off in production via openquake.cfg
        "i" : incremental counter
        "t" : totals counter
    """
    key = key_name(job_id, area, fragment, counter_type)
    if not key:
        return
    value = kvs_op("get", key)
    return int(value) if value else value


def delete_job_counters(job_id):
    """Delete the progress indication counters for the given `job_id`."""
    conn = _redis()
    keys = conn.keys("oqs/%s*" % job_id)
    if keys:
        conn.delete(*keys)


def debug_stats_enabled():
    """True if debug statistics counters are enabled."""
    return config.flag_set("statistics", "debug")
