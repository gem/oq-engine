# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import sys
import logging
import traceback
import shutil
import urllib
import urllib2

from openquake.engine import engine

from openquake.server.settings import DEBUG

# all the logs are sent to the platform; one would need a different logger
# to discriminate between progress logs and debug logs written in the file
DEFAULT_LOG_LEVEL = 'debug' if DEBUG else 'progress'


# FIXME. Configure logging by using the configuration stored in settings
logger = logging.getLogger(__name__)


# Please note: the OpenQuake Engine server requires a celeryconfig.py
# file in the PYTHONPATH; when using binary packages, if a celeryconfig.py
# is not available the OpenQuake Engine default celeryconfig.py, located
# in /usr/share/openquake/engine, is used.
try:
    import celeryconfig
except ImportError:
    sys.path.append('/usr/share/openquake/engine')


class ProgressHandler(logging.Handler):
    """
    A logging handler to update the status of the job as seen
    from the platform.
    """
    def __init__(self, callback_url, job):
        logging.Handler.__init__(self)
        self.callback_url = callback_url
        self.job = job

    def emit(self, record):
        """
        Update the status field on icebox_calculation with the percentage
        """
        update_calculation(
            self.callback_url,
            status=record.getMessage(),
            description=self.job.description)


def safely_call(func, *args):
    """
    Call the given procedure with the given arguments safely, i.e.
    by trapping the exceptions and logging them.
    """
    try:
        func(*args)
    except Exception as e:
        logger.error(str(e), exc_info=True)


def run_calc(
        job, calc_dir, callback_url=None, dbname="platform", log_file=None,
        hazard_calculation_id=None):
    """
    Run a calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute. This function never fails; errors are trapped
    but not logged since the engine already logs them.

    :param job:
        the job object
    :param calc_dir:
        the directory with the input files
    :param callback_url:
        the URL to call at the end of the calculation
    :param dbname:
        the platform database name
    :param log_file:
        the name of the log file
    :param hazard_calculation_id:
        the previous calculation, if any
    """
    update_calculation(callback_url, status="started", engine_id=job.id)

    progress_handler = ProgressHandler(callback_url, job)
    logging.root.addHandler(progress_handler)
    try:
        calc = engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, '',
                               hazard_calculation_id)
    except:  # catch the errors before task spawning
        # do not log the errors, since the engine already does that
        exctype, exc, tb = sys.exc_info()
        einfo = ''.join(traceback.format_tb(tb))
        einfo += '%s: %s' % (exctype.__name__, exc)
        update_calculation(callback_url, status="failed", einfo=einfo)
        raise
    finally:
        logging.root.removeHandler(progress_handler)
    calc.datastore.close()
    shutil.rmtree(calc_dir)


def update_calculation(callback_url=None, **query):
    """
    Update the log by POSTing `query` data to `callback_url`.
    """
    if callback_url is None:
        return
    # post to an external service
    url = urllib2.urlopen(callback_url, data=urllib.urlencode(query))
    url.close()
