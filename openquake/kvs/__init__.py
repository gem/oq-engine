# -*- coding: utf-8 -*-

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
This module contains generic functions to access
the underlying kvs systems.
"""

import json
import logging

import numpy

from openquake.kvs import tokens
from openquake.kvs.redis import Redis


DEFAULT_LENGTH_RANDOM_ID = 8
INTERNAL_ID_SEPARATOR = ':'
MAX_LENGTH_RANDOM_ID = 36
SITES_KEY_TOKEN = "sites"


def flush():
    """Flush (delete) all the values stored in the underlying kvs system."""
    get_client().flushall()


def get_keys(regexp):
    """Get all KVS keys that match a given regexp pattern."""
    return get_client().keys(regexp)


def mget(keys):
    """
    Retrieve multiple keys from the KVS.

    :param keys: keys to retrieve
    :type keys: list
    :returns: one value for each key in the list
    """
    return get_client().mget(keys)


def mget_decoded(keys):
    """
    Retrieve multiple JSON values from the KVS

    :param keys: keys to retrieve (the corresponding value must be a
        JSON string)
    :type keys: list
    :returns: one value for each key in the list
    """
    decoder = json.JSONDecoder()

    return [decoder.decode(value) for value in get_client().mget(keys)]


def get_pattern(regexp):
    """Get all the values whose keys satisfy the given regexp.

    Return an empty list if there are no keys satisfying the given regxep.
    """

    values = []

    keys = get_client().keys(regexp)

    if keys:
        values = get_client().mget(keys)

    return values


def get_pattern_decoded(regexp):
    """Get and decode (from json format) all the values whose keys
    satisfy the given regexp."""

    decoded_values = []
    decoder = json.JSONDecoder()

    for value in get_pattern(regexp):
        decoded_values.append(decoder.decode(value))

    return decoded_values


def get(key):
    """Get value from kvs for external decoding"""
    return get_client().get(key)


def get_client(**kwargs):
    """possible kwargs:
        db: database identifier
    """
    return Redis(**kwargs)


def get_value_json_decoded(key):
    """ Get value from kvs and json decode """
    try:
        value = get_client().get(key)
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


def set(key, encoded_value):  # pylint: disable=W0622
    """ Set value in kvs, for objects that have their own encoding method. """

    get_client().set(key, encoded_value)
    return True


def _prefix_id_generator(prefix):
    """Generator for IDs with a specific prefix (prefix + sequence number)."""

    counter = 0
    while(True):
        counter += 1
        yield INTERNAL_ID_SEPARATOR.join((str(prefix), str(counter)))

# generator instance used to generate IDs for blocks
BLOCK_ID_GENERATOR = _prefix_id_generator("BLOCK")


def generate_block_id():
    """Generate a unique id for a block."""
    return BLOCK_ID_GENERATOR.next()


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


def cache_gc(job_id, logger=None):
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
    if logger is None:
        logger = logging.getLogger('oq.kvs')

    if client.sismember(tokens.CURRENT_JOBS, job_id):
        # matches a current job
        # do the garbage collection
        keys = client.keys('*%s*' % tokens.generate_job_key(job_id))

        if len(keys) > 0:

            success = client.delete(*keys)
            # delete should return True
            if not success:
                msg = 'Redis failed to delete data for job %s' % job_id
                logger.error(msg)
                raise RuntimeError(msg)

        # finally, remove the job key from CURRENT_JOBS
        client.srem(tokens.CURRENT_JOBS, job_id)

        msg = 'KVS garbage collection removed %s keys for job %s'
        msg %= (len(keys), job_id)
        logger.info(msg)

        return len(keys)
    else:
        # does not match a current job
        msg = 'KVS garbage collection was called with an invalid job key: ' \
            '%s is not recognized as a current job.' % job_id
        logger.error(msg)
        return None
