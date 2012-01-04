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


"""The 'Engine' is responsible for instantiating calculators and running jobs.
"""


import os

from openquake.logs import LOG
from openquake.job.mixins import Mixin


def launch(a_job):
    """Based on the behavior specified in the configuration, mix in the correct
    behavior for job and execute it.

    :param a_job:
        :class:`openquake.job.Job` instance.
    """
    a_job._record_initial_stats()  # move this to the job constructor

    output_dir = os.path.join(a_job.base_path, a_job['OUTPUT_DIR'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for (key, mixin) in Mixin.ordered_mixins():
        if not key.upper() in a_job.sections:
            continue

        with Mixin(a_job, mixin):
            # The mixin defines a preload decorator to handle the needed
            # data for the tasks and decorates _execute(). the mixin's
            # _execute() method calls the expected tasks.
            LOG.debug(
                "Job %s Launching %s for %s" % (a_job.job_id, mixin, key))
            a_job.execute()
