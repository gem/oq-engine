# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import pylibmc
import random
import time
import unittest

import tests.tasks as test_tasks

TASK_NAME_SIMPLE = ["one", "two", "three", "four"]

JOBBER_CONFIG_FILE = 'basic-job.yml'

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

WAIT_TIME_STEP_FOR_TASK_SECS = 1
MAX_WAIT_LOOPS = 10

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class JobberTestCase(unittest.TestCase):
    def setUp(self):
        self.memcache_client = pylibmc.Client(["%s:%d" % (MEMCACHED_HOST,
            MEMCACHED_PORT)], binary=False)
        self.memcache_client.delete_multi(TASK_NAME_SIMPLE)

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

        # if a task has not yet finished, wait for a second
        # then check again
        counter = 0
        while (False in [result.ready() for result in results]):
            counter += 1

            if counter > MAX_WAIT_LOOPS:
                raise RuntimeError, "wait too long for celery worker threads"

            time.sleep(WAIT_TIME_STEP_FOR_TASK_SECS)

        result_values = self.memcache_client.get_multi(TASK_NAME_SIMPLE)
        self.assertEqual(sorted(TASK_NAME_SIMPLE), 
                         sorted(result_values.values()))

    #def test_parses_job_config(self):
        ## Load config file
        #config_path = os.path.join(data_dir, JOBBER_CONFIG_FILE)
        
