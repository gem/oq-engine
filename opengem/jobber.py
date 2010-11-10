# -*- coding: utf-8 -*-
"""
Main jobber module
"""


from opengem import job
from opengem import flags
from opengem import logs
from opengem import kvs

FLAGS = flags.FLAGS

LOGGER = logs.LOG

class Jobber(object):
    """The Jobber class is responsible to evaluate the configuration settings
    and to execute the computations in parallel tasks (using the celery
    framework and the message queue RabbitMQ).
    """

    def __init__(self, job, partition):
        self.memcache_client = None
        self.partition = partition
        self.job = job
        
        self._init()
        self.block_id_generator = kvs.block_id_generator()

    def run(self):
        """Core method of Jobber. It splits the requested computation
        in blocks and executes these as parallel tasks.
        """

        job_id = self.job.id
        LOGGER.debug("running jobber, job_id = %s" % job_id)

        if self.partition is True:
            self._partition(job_id)
        else:
            self.job.block_id = self.block_id.generator.next()
            self.job.launch()

        LOGGER.debug("Jobber run ended")

    def _partition(self, job_id):
        """
         _partition() has to:
          - get the full set of sites
          - select a subset of these sites
          - write the subset of sites to memcache, prepare a computation block
        """
        pass

    def _init(self):
        """ Initialize memcached_client. This should move into a Singleton """
        
        # TODO(fab): find out why this works only with binary=False
        self.memcache_client = kvs.get_client(binary=False)
        self.memcache_client.flush_all()
