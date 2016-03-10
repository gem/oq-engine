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


def run_calc(job, log_file=None, hazard_calculation_id=None):
    """
    Run a calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute. This function never fails; errors are trapped
    but not logged since the engine already logs them.

    :param job:
        the job object
    :param log_file:
        the name of the log file
    :param hazard_calculation_id:
        the previous calculation, if any
    """
    try:
        calc = engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, '',
                               hazard_calculation_id)
    except:  # catch the errors before task spawning
        # do not log the errors, since the engine already does that
        exctype, exc, tb = sys.exc_info()
        einfo = ''.join(traceback.format_tb(tb))
        einfo += '%s: %s' % (exctype.__name__, exc)
        raise
    calc.datastore.close()


def submit_job(job_ini, user_name, hazard_job_id=None, logfile=None):
    """
    Create a job object from the given job.ini file in the job directory
    and submit it to the job queue. Returns the job ID.
    """
    job = engine.job_from_file(job_ini, user_name, 'info', '', hazard_job_id)
    fut = executor.submit(run_calc, job, logfile, hazard_job_id)
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
        print('Listening on %s:%d...' % self.address)
        try:
            while True:
                try:
                    conn = listener.accept()
                except KeyboardInterrupt:
                    break
                except:
                    # unauthenticated connection, for instance by a port
                    # scanner such as the one in manage.py
                    continue
                try:
                    cmd = conn.recv()
                    name = cmd[0]
                    if name == '@stop':
                        conn.send((None, None))
                        break
                    elif name.startswith('.'):  # method
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
                    if etype:
                        logging.error(res)
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
        cl = Client(self.address, authkey=self.authkey)
        try:
            cl.send(cmd)
            res, etype = cl.recv()
        finally:
            cl.close()
        if etype:
            raise etype(res)
        return res

    def stop(self):
        """
        Send a command stopping the server cleanly
        """
        self.start('@stop')


cmd = CmdServer(ADDRESS, AUTHKEY)

if __name__ == '__main__':
    cmd.loop()
