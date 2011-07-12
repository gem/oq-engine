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
import uuid
import openquake.kvs.tokens

from openquake import logs
from openquake.kvs.redis import Redis


LOG = logs.LOG

DEFAULT_LENGTH_RANDOM_ID = 8
INTERNAL_ID_SEPARATOR = ':'
MAX_LENGTH_RANDOM_ID = 36
KVS_KEY_SEPARATOR = '!'
SITES_KEY_TOKEN = "sites"


def flush():
    """Flush (delete) all the values stored in the underlying kvs system."""
    get_client(binary=False).flushall()


def get_keys(regexp):
    """Get all KVS keys that match a given regexp pattern."""
    return get_client(binary=False).keys(regexp)


def mget(regexp):
    """Get all the values whose keys satisfy the given regexp.

    Return an empty list if there are no keys satisfying the given regxep.
    """

    values = []

    keys = get_client(binary=False).keys(regexp)

    if keys:
        values = get_client(binary=False).mget(keys)

    return values


def mget_decoded(regexp):
    """Get and decode (from json format) all the values whose keys
    satisfy the given regexp."""

    decoded_values = []
    decoder = json.JSONDecoder()

    for value in mget(regexp):
        decoded_values.append(decoder.decode(value))

    return decoded_values


def get(key):
    """Get value from kvs for external decoding"""
    return get_client(binary=False).get(key)


def get_client(**kwargs):
    """possible kwargs:
        binary
    """
    return Redis(**kwargs)


def generate_key(key_list):
    """ Create a kvs key """
    key_list = [str(x).replace(" ", "") for x in key_list]
    return KVS_KEY_SEPARATOR.join(key_list)


def generate_job_key(job_id):
    """ Return a job key """
    return generate_key(("JOB", str(job_id)))


def generate_sites_key(job_id, block_id):
    """ Return sites key """

    sites_key_token = 'sites'
    return generate_product_key(job_id, sites_key_token, block_id)


def generate_product_key(job_id, product, block_id="", site=""):
    """construct kvs key from several part IDs"""
    return generate_key([job_id, product, block_id, site])


def generate_random_id(length=DEFAULT_LENGTH_RANDOM_ID):
    """This function returns a random ID by using the uuid4 method. In order
    to have reasonably short IDs, the ID returned from uuid4() is truncated.
    This is not optimized for being collision-free. See documentation of uuid:
    http://docs.python.org/library/uuid.html
    http://en.wikipedia.org/wiki/Universally_unique_identifier
    """
    if length > MAX_LENGTH_RANDOM_ID:
        length = MAX_LENGTH_RANDOM_ID
    return str(uuid.uuid4())[0:length]


def get_value_json_decoded(key):
    """ Get value from kvs and json decode """
    try:
        value = get_client(binary=False).get(key)
        decoder = json.JSONDecoder()
        return decoder.decode(value)
    except (TypeError, ValueError), e:
        print "Key was %s" % key
        print e
        print "Raw JSON was: %s" % value
        return None


def set_value_json_encoded(key, value):
    """ Encode value and set in kvs """
    encoder = json.JSONEncoder()

    try:
        encoded_value = encoder.encode(value)
        get_client(binary=False).set(key, encoded_value)
    except (TypeError, ValueError):
        raise ValueError("cannot encode value %s to JSON" % value)

    return True


def set(key, encoded_value):  # pylint: disable=W0622
    """ Set value in kvs, for objects that have their own encoding method. """

    get_client(binary=False).set(key, encoded_value)
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


def cache_gc(job_key):
    """
    Garbage collection for the KVS. This works by simply removing all keys
    which contain the input job key.

    The job key must be a member of the 'CURRENT_JOBS' set. If it isn't, this
    function will do nothing and simply return None.

    :param job_key: specially formatted job key;
        see :py:function:`openquake.kvs.tokens.alloc_job_key` for more info

    :returns: the number of deleted keys (int), or None if the job doesn't
        exist in CURRENT_JOBS
    """
    client = get_client()

    if client.sismember(openquake.kvs.tokens.CURRENT_JOBS, job_key):
        # matches a current job
        # do the garbage collection
        keys = client.keys('*%s*' % job_key)

        if len(keys) > 0:

            success = client.delete(*keys)
            # delete should return True
            if not success:
                msg = 'Redis failed to delete data for job %s' % job_key
                LOG.error(msg)
                raise RuntimeError(msg)

        # finally, remove the job key from CURRENT_JOBS
        client.srem(openquake.kvs.tokens.CURRENT_JOBS, job_key)

        return len(keys)
    else:
        # does not match a current job
        msg = 'KVS garbage collection was called with an invalid job key: ' \
            '%s is not recognized as a current job.'
        LOG.error(msg)
        return None
