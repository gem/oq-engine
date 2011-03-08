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



# -*- coding: utf-8 -*-
"""
Celery tasks for jobber unit tests
"""

import json
import random
import time

from celery.decorators import task

from openquake import kvs

MAX_WAIT_TIME_MILLISECS = 1200

@task
def simple_task_return_name(name, **kwargs):

    # wait for random time interval between 0 and MAX_WAIT_TIME_SECS seconds,
    # to ensure that results are returned in arbitrary order
    logger = simple_task_return_name.get_logger(**kwargs)

    wait_time = _wait_a_bit()
    logger.info("processing %s, waited %s milliseconds" % (name, wait_time))
    return name

@task
def simple_task_return_name_to_memcache(name, **kwargs):

    logger = simple_task_return_name_to_memcache.get_logger(**kwargs)

    memcache_client = kvs.get_client(binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing %s, waited %s milliseconds" % (name, wait_time))

    memcache_client.set(name, name)
    logger.info("wrote to memcache key %s" % (name))

@task
def simple_task_list_dict_to_memcache(name, **kwargs):

    logger = simple_task_list_dict_to_memcache.get_logger(**kwargs)

    memcache_client = kvs.get_client(binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing list/dict.%s, waited %s milliseconds" % (name, wait_time))

    memcache_client.set("list.%s" % name, [name, name])
    memcache_client.set("dict.%s" % name, {name: name})
    logger.info("wrote to list/dict for memcache key %s" % (name))

@task
def simple_task_json_to_memcache(name, **kwargs):

    logger = simple_task_json_to_memcache.get_logger(**kwargs)

    memcache_client = kvs.get_client(binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing json.%s, waited %s milliseconds" % (name, wait_time))

    test_dict = {"list.%s" % name: [name, name], 
                 "dict.%s" % name: {name: name}}
    test_dict_serialized = json.JSONEncoder().encode(test_dict)

    memcache_client.set(name, test_dict_serialized)
    logger.info("wrote to json for memcache key %s" % (name))

def _wait_a_bit():
    wait_time = random.randrange(0, MAX_WAIT_TIME_MILLISECS)
    time.sleep(wait_time/1000)
    return wait_time
