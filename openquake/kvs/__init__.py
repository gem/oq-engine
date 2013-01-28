# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
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
This module contains generic functions to access
the underlying kvs systems.
"""

import json
import numpy
import redis
from openquake import logs
from openquake.kvs import tokens
from openquake.utils import config
from openquake.utils import stats


LOG = logs.LOG

DEFAULT_LENGTH_RANDOM_ID = 8
INTERNAL_ID_SEPARATOR = ':'
MAX_LENGTH_RANDOM_ID = 36
SITES_KEY_TOKEN = "sites"


# Module-private kvs connection pool, to be used by get_client().
__KVS_CONN_POOL = None


# pylint: disable=W0603
def get_client(**kwargs):
    """
    Return a redis kvs client connection for general OpenQuake engine
    calculation usage..

    PLEASE NOTE: The 'db' argument is automatically read from the openquake.cfg
    and set. If specified in ``kwargs``, it will be overridden with the setting
    in openquake.cfg.
    """
    global __KVS_CONN_POOL
    if __KVS_CONN_POOL is None:
        cfg = config.get_section("kvs")
        # get the default db from the openquake.cfg:
        db = int(config.get('kvs', 'redis_db'))
        __KVS_CONN_POOL = redis.ConnectionPool(
            max_connections=1, host=cfg["host"], port=int(cfg["port"]), db=db)
    kwargs.update({"connection_pool": __KVS_CONN_POOL})
    return redis.Redis(**kwargs)


def get_value_json_decoded(key):
    """ Get value from kvs and json decode """
    try:
        value = get_client().get(key)
        if not value:
            return value
        decoder = json.JSONDecoder()
        return decoder.decode(value)
    except (TypeError, ValueError), e:
        print "Key was %s" % key
        print e
        print "Raw JSON was: %s" % value
        return None


def get_list_json_decoded(key):
    """
    Get from the KVS a list of items.

    :param key: the KVS key
    :type key: string

    The items stored under key are expected to be JSON encoded, and are decoded
    before being returned.
    """

    return [json.loads(x) for x in get_client().lrange(key, 0, -1)]


class NumpyAwareJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that knows how to encode 1-dimensional numpy arrays
    """
    # pylint: disable=E0202
    def default(self, obj):
        if isinstance(obj, numpy.ndarray) and obj.ndim == 1:
            return [x for x in obj]

        return json.JSONEncoder.default(self, obj)


def set_value_json_encoded(key, value):
    """ Encode value and set in kvs """
    encoder = NumpyAwareJSONEncoder()

    try:
        encoded_value = encoder.encode(value)
        get_client().set(key, encoded_value)
    except (TypeError, ValueError):
        raise ValueError("cannot encode value %s of type %s to JSON"
                         % (value, type(value)))

    return True


def mark_job_as_current(job_id):
    """
    Add a job to the set of current jobs, to be later garbage collected.

    :param job_id: the job id
    :type job_id: int
    """
    client = get_client()

    # Add this key to set of current jobs.
    # This set can be queried to perform garbage collection.
    client.sadd(tokens.CURRENT_JOBS, job_id)


def current_jobs():
    """
    Get all current job keys, sorted in ascending order.

    :returns: list of job keys (as strings), or an empty list if there are no
        current jobs
    """
    client = get_client()
    return sorted([int(x) for x in client.smembers(tokens.CURRENT_JOBS)])


def cache_gc(job_id):
    """
    Garbage collection for the KVS. This works by simply removing all keys
    which contain the input job key.

    The job key must be a member of the 'CURRENT_JOBS' set. If it isn't, this
    function will do nothing and simply return None.

    :param job_id: the id of the job
    :type job_id: int

    :returns: the number of deleted keys (int), or None if the job doesn't
        exist in CURRENT_JOBS
    """
    client = get_client()

    if client.sismember(tokens.CURRENT_JOBS, job_id):
        # matches a current job
        # do the garbage collection
        keys = client.keys('*%s*' % tokens.generate_job_key(job_id))

        num_deleted = 0

        if len(keys) > 0:

            success = client.delete(*keys)
            # delete should return True
            if not success:
                msg = 'Redis failed to delete data for job %s' % job_id
                LOG.error(msg)
                raise RuntimeError(msg)

        # finally, remove the job key from CURRENT_JOBS
        client.srem(tokens.CURRENT_JOBS, job_id)

        msg = 'KVS garbage collection removed %s keys for job %s'
        msg %= (len(keys), job_id)
        LOG.debug(msg)

        num_deleted += len(keys)

        # clear stats counters too:
        num_deleted += stats.delete_job_counters(job_id)

        return num_deleted
    else:
        # does not match a current job
        msg = 'KVS garbage collection was called with an invalid job key: ' \
            '%s is not recognized as a current job.' % job_id
        LOG.error(msg)
        return None


def cache_connections():
    """True if kvs connections should be cached."""
    return config.flag_set("kvs", "cache_connections")
