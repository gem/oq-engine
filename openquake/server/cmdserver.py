#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import logging
import urllib
import urllib2
import traceback
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import Client, Listener

from openquake.baselib.hdf5 import Hdf5Dataset
from openquake.commonlib.parallel import safely_call
from openquake.commonlib.datastore import read
from openquake.engine import engine
from openquake.engine.utils import config

PORT = int(config.get('cmdserver', 'port'))
ADDRESS = ('', PORT)
AUTHKEY = config.get('cmdserver', 'authkey')
DEFAULT_LOG_LEVEL = 'progress'

# recommended setting for development
# with processes it works only once and then the db connection is closed
executor = ThreadPoolExecutor(max_workers=1)
executor.future = {}  # job_id -> future

# global commands

exit = sys.exit
info = logging.info


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


def run_calc(
        job, callback_url=None, log_file=None, hazard_calculation_id=None):
    """
    Run a calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute. This function never fails; errors are trapped
    but not logged since the engine already logs them.

    :param job:
        the job object
    :param callback_url:
        the URL to call at the end of the calculation
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


def update_calculation(callback_url=None, **query):
    """
    Update the log by POSTing `query` data to `callback_url`.
    """
    if callback_url is None:
        return
    # post to an external service
    url = urllib2.urlopen(callback_url, data=urllib.urlencode(query))
    url.close()


def submit_job(job_ini, user_name,
               callback_url=None, hazard_job_id=None, logfile=None):
    """
    Create a job object from the given job.ini file in the job directory
    and submit it to the job queue. Returns the job ID.
    """
    job = engine.job_from_file(job_ini, user_name, 'info', '', hazard_job_id)
    fut = executor.submit(run_calc, job, callback_url, logfile, hazard_job_id)
    executor.future[job.id] = fut
    return job.id


class CmdServer(object):
    """
    A server receiving and executing commands. Errors are trapped and
    we send back to the client pairs (result, exctype) for each command
    received. `exctype` is None if there is no exception, otherwise it
    is an exception class and `result` is an error string containing the
    traceback.
    """
    def __init__(self, address, authkey):
        self.address = address
        self.authkey = authkey

    def loop(self):
        dstore = {}
        listener = Listener(self.address, authkey=self.authkey)
        print('Listening on %s...' % str(self.address))
        try:
            while True:
                conn = listener.accept()
                try:
                    cmd = conn.recv()
                    name = cmd[0]
                    if name.startswith('.'):  # method
                        args = cmd[1:-1]
                        calc_id = cmd[-1]
                        try:
                            self.datastore = dstore[calc_id]
                        except KeyError:
                            ds = read(calc_id, 'r+')
                            self.datastore = dstore[calc_id] = ds
                        call = getattr(self, name[1:])
                    else:  # global function
                        args = cmd[1:]
                        call = globals()[name]
                    res, etype, _ = safely_call(call, args)
                    conn.send((res, etype))
                finally:
                    conn.close()
        finally:
            listener.close()
            for ds in dstore.values():
                ds.close()

    def save(self, key, array):
        """
        :param key: datastore key
        :param array: an array to save for the given key
        """
        self.datastore[key] = array
        self.datastore.flush()

    def extend(self, key, array):
        """
        :param key: datastore key
        :param array: an array extending the dataset with the given key
        """
        Hdf5Dataset(self.datastore.hdf5[key]).extend(array)
        self.datastore.flush()

    def start(self, *cmd):
        """
        Send a command to the CmdServer.

        :param cmd: a tuple with the name of the command and the arguments
        """
        c = Client(self.address, authkey=self.authkey)
        try:
            c.send(cmd)
            res, etype = c.recv()
        finally:
            c.close()
        if etype:
            raise etype(res)
        return res

    def stop(self):
        """
        Send a command stopping the server cleanly
        """
        self.start('exit', 0)


cmd = CmdServer(ADDRESS, AUTHKEY)

if __name__ == '__main__':
    cmd.loop()
