# -*- coding: utf-8 -*-
"""
Main jobber module.
"""



#     dd                                             tt                dd
#     dd   eee  pp pp   rr rr    eee    cccc   aa aa tt      eee       dd
# dddddd ee   e ppp  pp rrr  r ee   e cc      aa aaa tttt  ee   e  dddddd
#dd   dd eeeee  pppppp  rr     eeeee  cc     aa  aaa tt    eeeee  dd   dd
# dddddd  eeeee pp      rr      eeeee  ccccc  aaa aa  tttt  eeeee  dddddd
#               pp

import math
import os

from opengem import job
from opengem import logs

LOGGER = logs.LOG

# TODO (ac): This class is not covered by unit tests...
class Jobber(object):
    """The Jobber class is responsible to evaluate the configuration settings
    and to execute the computations in parallel tasks (using the celery
    framework and the message queue RabbitMQ).
    """

    @staticmethod
    def run(job):
        """Core method of Jobber. It splits the requested computation
        in blocks and executes these as parallel tasks.
        """

        LOGGER.debug("running jobber, job_id = %s" % job.job_id)
        job.launch()
        LOGGER.debug("Jobber run ended")
