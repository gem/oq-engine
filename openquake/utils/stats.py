# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


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

# Please note: counters apply to certain computation areas. At this point
# these are as follows.
#   "g" : general
#   "h" : hazard
#   "r" : risk

# Also, we distinguish the following types of statistics counters:
#   "d" : debug counter, turned off in production via openquake.cfg
#   "i" : incremental counter
#   "t" : counts totals

# Last but not least: some counters are only used by specific calculators,
# e.g.
#   "hcls": classical hazard (openshalite based)
#   "nhzrd": nhlib-based hazard
#   "nrisk": nhlib-based risk

STATS_KEYS = {
    # Predefined calculator statistics keys for the kvs.
    "hcls_realizations": ("h", "cls:realizations", "t"),
    # Current realization
    "hcls_crealization": ("h", "cls:crealization", "i"),
    # The total number of sites
    "hcls_sites": ("h", "cls:sites", "t"),
    # The block size used
    "block_size": ("g", "gen:block_size", "t"),
    # The total number of blocks
    "blocks": ("g", "gen:blocks", "t"),
    # The current block
    "cblock": ("g", "gen:cblock", "i"),
    "compute_uhs_task": ("h", "compute_uhs_task", "i"),

    # The total amount of work for a nhlib-based hazard calculation
    "nhzrd_total": ("h", "nhzrd:total", "t"),
    # The number of completed hazard work items
    "nhzrd_done": ("h", "nhzrd:done", "i"),
    # The number of failed hazard work items
    "nhzrd_failed": ("h", "nhzrd:failed", "i"),

    # The total amount of work for a nhlib-based risk calculation
    "nrisk_total": ("r", "nrisk:total", "t"),
    # The number of completed risk work items
    "nrisk_done": ("r", "nrisk:done", "i"),
    # The number of failed risk work items
    "nrisk_failed": ("r", "nrisk:failed", "i"),
}


# Predefined key template, order of substitution variables:
#   job_id, computation area, key fragment, counter_type.
_KEY_TEMPLATE = "oqs/%s/%s/%s/%s"


def kvs_op(dop, *kvs_args):
    """Apply the kvs operation using the predefined key.

    :param string dop: the kvs operation desired
    :param tuple kvs_args: the positional arguments for the desired kvs
        operation
    :returns: whatever is retured by the kvs operation
    """
    conn = _redis()
    op = getattr(conn, dop)
    return op(*kvs_args)


def failure_counters(job_id, area=None):
    """Return a list of 2-tuples with failure keys/counters for the given area.

    :param int job_id: identifier of the job in question
    :param str area: computation area, one of:
        "g" : general
        "h" : hazard
        "r" : risk
    :returns: a potentially empty list of 2-tuples with failure keys/counters
        for the given area.
    """
    assert area is None or area in ("g", "h", "r"), "Invalid area."

    if area:
        pattern = "oqs/%s/%s/*-failures*" % (job_id, area)
    else:
        pattern = "oqs/%s/*-failures*" % job_id

    result = keys = kvs_op("keys", pattern)
    if keys:
        result = zip(keys, [int(c) for c in kvs_op("mget", keys)])
    return result


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
    :returns: `None` or counter value
    """
    key = key_name(job_id, *STATS_KEYS[skey])
    if not key:
        return
    value = kvs_op("get", key)
    if cast2int:
        return int(value) if value else 0
    else:
        return value


def _redis():
    """Return a connection to the redis store."""
    host = config.get("kvs", "host")
    port = config.get("kvs", "port")
    port = int(port) if port else 6379
    stats_db = config.get("kvs", "stats_db")
    stats_db = int(stats_db) if stats_db else 15
    args = {"host": host, "port": port, "db": stats_db}
    return redis.Redis(**args)


def key_name(job_id, area, key_fragment, counter_type):
    """Return `None` or the full predefined statistics key.

    `None` is returned for unknown predefined statistics keys and for debug
    statistics counters if these have been turned off.

    :param int job_id: identifier of the job in question
    :param str area: computation area, one of:
        "g" : general
        "h" : hazard
        "r" : risk
    :param string key_fragment: a part of the predefined statistics key
    :param str counter_type: counter type, one of:
        "d" : debug counter, turned off in production via openquake.cfg
        "i" : incremental counter
        "t" : counts totals
    :returns: `None` or the full predefined statistics key
    """
    if counter_type == "d" and not debug_stats_enabled():
        return None
    return _KEY_TEMPLATE % (job_id, area, key_fragment, counter_type)


# al-maisan, Mon, 20 Aug 2012 15:43:11 +0200
# PLEASE NOTE: the decorator below is deprecated and should not be used for
# new code in the nhlib-integration branch. Please use the 'count_progress'
# decorator instead.
class progress_indicator(object):   # pylint: disable=C0103
    """Count successful/failed invocations of the wrapped function."""

    def __init__(self, area):
        """Captures the computation area parameter."""
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
        """The actual decorator."""
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


class count_progress(object):   # pylint: disable=C0103
    """Count successful/failed invocations of the wrapped function.

    Please note: for this to work the wrapped function must have the `job_id`
    and the collection with the work items passed via the first and the second
    parameter respectively.
    This is a simple convention that saves us from sifting through all the
    called function's parameters and finding the desired data (which would be
    unnecessarily complex *and* error-prone).
    """

    def __init__(self, area):
        """Captures the computation area parameter."""
        self.area = area
        self.__name__ = "count_progress"

    @staticmethod
    def get_task_data(*args, **kwargs):
        """Return the job_id and the number of work items."""
        return args[0], len(args[1])

    def __call__(self, func):
        """The actual decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Call the wrapped function and step the done/failed counters in
               case of success/failure."""
            job_id, num_items = self.get_task_data(*args, **kwargs)
            conn = _redis()
            try:
                result = func(*args, **kwargs)
                key = "nhzrd_done" if self.area == "h" else "nrisk_done"
                key = key_name(job_id, self.area, key, "i")
                conn.incr(key, num_items)
                return result
            except:
                # Count failure
                key = "nhzrd_failed" if self.area == "h" else "nrisk_failed"
                key = key_name(job_id, self.area, key, "i")
                conn.incr(key, num_items)
                raise

        return wrapper


def set_total(job_id, area, key_fragment, value):
    """Set a total value for the given key.

    :param int job_id: identifier of the job in question
    :param str area: computation area, one of:
        "g" : general
        "h" : hazard
        "r" : risk
    :param string key_fragment: a part of the predefined statistics key
    :param valye: the value that should be set.
    """
    key = key_name(job_id, area, key_fragment, "t")
    kvs_op("set", key, value)


def incr_counter(job_id, area, key_fragment):
    """Increment the counter for the given key.

    :param int job_id: identifier of the job in question
    :param str area: computation area, one of:
        "g" : general
        "h" : hazard
        "r" : risk
    :param string key_fragment: a part of the predefined statistics key
    """
    key = key_name(job_id, area, key_fragment, "i")
    kvs_op("incr", key)


def get_counter(job_id, area, key_fragment, counter_type):
    """Get the value for the given key.

    :param int job_id: identifier of the job in question
    :param str area: computation area, one of:
        "g" : general
        "h" : hazard
        "r" : risk
    :param string key_fragment: a part of the predefined statistics key
    :param str counter_type: counter type, one of:
        "d" : debug counter, turned off in production via openquake.cfg
        "i" : incremental counter
        "t" : counts totals
    :returns: `None` or the statistics key value
    """
    key = key_name(job_id, area, key_fragment, counter_type)
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
