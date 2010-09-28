# -*- coding: utf-8 -*-
"""
Celery tasks for jobber unit tests
"""

import json
import pylibmc
import random
import time

from celery.decorators import task

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

MAX_WAIT_TIME_SECS = 3

@task
def simple_task_return_name(name, **kwargs):

    # wait for random time interval between 0 and MAX_WAIT_TIME_SECS seconds,
    # to ensure that results are returned in arbitrary order
    logger = simple_task_return_name.get_logger(**kwargs)

    wait_time = _wait_a_bit()
    logger.info("processing %s, waited %s seconds" % (name, wait_time))
    return name

@task
def simple_task_return_name_to_memcache(name, **kwargs):

    logger = simple_task_return_name_to_memcache.get_logger(**kwargs)

    memcache_client = pylibmc.Client(["%s:%d" % (MEMCACHED_HOST, 
        MEMCACHED_PORT)], binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing %s, waited %s seconds" % (name, wait_time))

    memcache_client.set(name, name)
    logger.info("wrote to memcache key %s" % (name))

@task
def simple_task_list_dict_to_memcache(name, **kwargs):

    logger = simple_task_list_dict_to_memcache.get_logger(**kwargs)

    memcache_client = pylibmc.Client(["%s:%d" % (MEMCACHED_HOST, 
        MEMCACHED_PORT)], binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing list/dict.%s, waited %s seconds" % (name, wait_time))

    memcache_client.set("list.%s" % name, [name, name])
    memcache_client.set("dict.%s" % name, {name: name})
    logger.info("wrote to list/dict for memcache key %s" % (name))

@task
def simple_task_json_to_memcache(name, **kwargs):

    logger = simple_task_json_to_memcache.get_logger(**kwargs)

    memcache_client = pylibmc.Client(["%s:%d" % (MEMCACHED_HOST, 
        MEMCACHED_PORT)], binary=False)

    wait_time = _wait_a_bit()
    logger.info("processing json.%s, waited %s seconds" % (name, wait_time))

    test_dict = {"list.%s" % name: [name, name], 
                 "dict.%s" % name: {name: name}}
    test_dict_serialized = json.JSONEncoder().encode(test_dict)

    memcache_client.set(name, test_dict_serialized)
    logger.info("wrote to json for memcache key %s" % (name))

def _wait_a_bit():
    wait_time = random.randrange(MAX_WAIT_TIME_SECS)
    time.sleep(wait_time)
    return wait_time