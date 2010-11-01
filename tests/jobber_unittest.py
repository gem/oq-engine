# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""These are the unit tests for the jobber module. At the moment, they contain
only tests for the basic underlying technologies (celery, memcached).
A test that asserts that a given computation result can reproduced is still
missing.
"""

import json
import os
import random
import time
import unittest

from opengem import logs
from opengem import kvs

import tests.tasks as test_tasks

logger = logs.LOG

TASK_NAME_SIMPLE = ["one", "two", "three", "four"]

WAIT_TIME_STEP_FOR_TASK_SECS = 0.5
MAX_WAIT_LOOPS = 10

class JobberTestCase(unittest.TestCase):
    def setUp(self):
        self.memcache_client = kvs.get_client(binary=False)
        self.memcache_client.flush_all()

    def tearDown(self):
        pass

    def test_basic_asynchronous_processing_keep_order(self):

        # spawn four tasks that simply return a string with their name
        # result list will have them in the same order they are spawned
        results = []
        for curr_task_name in TASK_NAME_SIMPLE:
            results.append(test_tasks.simple_task_return_name.delay(
                curr_task_name))

        self.assertEqual(TASK_NAME_SIMPLE, 
                         [result.get() for result in results])

    def test_basic_asynchronous_processing_using_memcache(self):

        # spawn four tasks that simply return a string with their name
        # tasks write their results to memcached
        results = []
        for curr_task_name in TASK_NAME_SIMPLE:
            results.append(
                test_tasks.simple_task_return_name_to_memcache.apply_async(
                    args=[curr_task_name]))

        wait_for_celery_tasks(results)

        result_values = self.memcache_client.get_multi(TASK_NAME_SIMPLE)
        self.assertEqual(sorted(TASK_NAME_SIMPLE), 
                         sorted(result_values.values()))

    def test_async_memcache_serialize_list_and_dict(self):

        # spawn four tasks that return lists and dicts
        # tasks write their results to memcached
        # check if lists and dicts are serialized/deserialized correctly
        results = []
        for curr_task_name in TASK_NAME_SIMPLE:
            results.append(
                test_tasks.simple_task_list_dict_to_memcache.apply_async(
                    args=[curr_task_name]))

        wait_for_celery_tasks(results)

        expected_keys = []
        for name in TASK_NAME_SIMPLE:
            expected_keys.extend(["list.%s" % name, "dict.%s" % name])

        result_values = self.memcache_client.get_multi(expected_keys)

        expected_dict = {}
        for curr_key in sorted(expected_keys):
            if curr_key.startswith('list.'):
                expected_dict[curr_key] = [curr_key[5:], curr_key[5:]]
            elif curr_key.startswith('dict.'):
                expected_dict[curr_key] = {curr_key[5:]: curr_key[5:]}

        self.assertEqual(expected_dict, result_values)

    def test_async_memcache_serialize_json(self):

        # spawn four tasks that return json serializations of dicts
        # tasks write their results to memcached
        # check if objects are serialized/deserialized to/from json correctly
        results = []
        for curr_task_name in TASK_NAME_SIMPLE:
            results.append(
                test_tasks.simple_task_json_to_memcache.apply_async(
                    args=[curr_task_name]))

        wait_for_celery_tasks(results)

        result_values = self.memcache_client.get_multi(TASK_NAME_SIMPLE)

        expected_dict = {}
        for curr_key in TASK_NAME_SIMPLE:
            expected_dict[curr_key] = {
                "list.%s" % curr_key: [curr_key, curr_key], 
                "dict.%s" % curr_key: {curr_key: curr_key}}

        decoder = json.JSONDecoder()
        result_dict = {}
        for k, v in result_values.items():
            result_dict[k] = decoder.decode(v)

        self.assertEqual(expected_dict, result_dict)

def wait_for_celery_tasks(celery_results, 
                          max_wait_loops=MAX_WAIT_LOOPS, 
                          wait_time=WAIT_TIME_STEP_FOR_TASK_SECS):
    """celery_results is a list of celery task result objects.
    This function waits until all tasks have finished.
    """

    # if a celery task has not yet finished, wait for a second
    # then check again
    counter = 0
    while (False in [result.ready() for result in celery_results]):
        counter += 1

        if counter > max_wait_loops:
            raise RuntimeError, "wait too long for celery worker threads"

        time.sleep(wait_time)
    
