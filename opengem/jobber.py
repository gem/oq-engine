# -*- coding: utf-8 -*-
"""
Main jobber module.
"""

import math
import os

from opengem import job
from opengem import flags
from opengem import logs
from opengem import kvs
from opengem import shapes

from opengem.parser import exposure

FLAGS = flags.FLAGS
LOGGER = logs.LOG

# TODO (ac): This class is not covered by unit tests...
class Jobber(object):
    """The Jobber class is responsible to evaluate the configuration settings
    and to execute the computations in parallel tasks (using the celery
    framework and the message queue RabbitMQ).
    """

    def __init__(self, incoming_job, partition):
        self.memcache_client = None
        self.partition = partition
        self.job = incoming_job
        
        self._init()

    def run(self):
        """Core method of Jobber. It splits the requested computation
        in blocks and executes these as parallel tasks.
        """

        LOGGER.debug("running jobber, job_id = %s" % self.job.id)

        for block_id in self._partition():
            self.job.block_id = block_id
            self.job.launch()

        LOGGER.debug("Jobber run ended")


    def _init(self):
        """ Initialize memcached_client. This should move into a Singleton """
        
        # TODO(fab): find out why this works only with binary=False
        self.memcache_client = kvs.get_client(binary=False)