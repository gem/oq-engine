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
Main jobber module.

This needs to be written to daemonise, pull a job from the queue, execute it
and then move on to the next one.
"""



#     dd                                             tt                dd
#     dd   eee  pp pp   rr rr    eee    cccc   aa aa tt      eee       dd
# dddddd ee   e ppp  pp rrr  r ee   e cc      aa aaa tttt  ee   e  dddddd
#dd   dd eeeee  pppppp  rr     eeeee  cc     aa  aaa tt    eeeee  dd   dd
# dddddd  eeeee pp      rr      eeeee  ccccc  aaa aa  tttt  eeeee  dddddd
#               pp

from openquake import logs

LOGGER = logs.LOG

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
