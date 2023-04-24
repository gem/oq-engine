# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import time
import shutil
import socket
import getpass
import tempfile
import functools
import subprocess
from datetime import datetime
import psutil
from openquake.baselib import (
    zeromq as z, general, performance, parallel, config, sap, InvalidFile)
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"


def init_workers():
    """Used to initialize the process pool"""
    setproctitle('oq-zworker')


def ssh_args(zworkers):
    """
    :yields: triples (hostIP, num_cores, [ssh remote python command])
    """
    remote_python = zworkers.remote_python or sys.executable
    remote_user = zworkers.remote_user or getpass.getuser()
    if zworkers.host_cores.strip():
        for hostcores in zworkers.host_cores.split(','):
            host, cores = hostcores.split()
            if host == '127.0.0.1':  # localhost
                yield host, cores, [sys.executable]
            else:
                yield host, cores, [
                    'ssh', '-f', '-T', remote_user + '@' + host, remote_python]


class WorkerMaster(object):
    """
    :param ctrl_port: port on which the worker pools listen
    :param host_cores: names of the remote hosts and number of cores to use
    :param remote_python: path of the Python executable on the remote hosts
    """
    def __init__(self, zworkers=config.zworkers, receiver_ports=None):
        self.zworkers = zworkers
        # NB: receiver_ports is not used but needed for compliance
        self.ctrl_port = int(zworkers.ctrl_port)
        self.host_cores = (
            [hc.split() for hc in zworkers.host_cores.split(',')]
            if zworkers.host_cores else [])
        for host, cores in self.host_cores:
            if int(cores) < -1:
                raise InvalidFile('openquake.cfg: found %s %s' %
                                  (host, cores))
        self.remote_python = zworkers.remote_python or sys.executable
        self.remote_user = zworkers.remote_user or getpass.getuser()
        self.popens = []

    def start(self):
        """
        Start multiple workerpools on remote servers via ssh and/or a single
        workerpool on localhost.
        """
        starting = []
        for host, cores, args in ssh_args(self.zworkers):
            if general.socket_ready((host, self.ctrl_port)):
                print('%s:%s already running' % (host, self.ctrl_port))
                continue
            ctrl_url = 'tcp://0.0.0.0:%s' % self.ctrl_port
            args += ['-m', 'openquake.baselib.workerpool', ctrl_url,
                     '-n', cores]
            if host != '127.0.0.1':
                print('%s: if it hangs, check the ssh keys' % ' '.join(args))
            self.popens.append(subprocess.Popen(args))
            starting.append(host)
        return 'starting %s' % starting

    def stop(self):
        """
        Send a "stop" command to all worker pools
        """
        stopped = []
        for host, _ in self.host_cores:
            if not general.socket_ready((host, self.ctrl_port)):
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            with z.Socket(ctrl_url, z.zmq.REQ, 'connect') as sock:
                sock.send('stop')
                stopped.append(host)
        for popen in self.popens:
            popen.terminate()
            # since we are not consuming any output from the spawned process
            # we must call wait() after terminate() to have Popen()
            # fully deallocate the process file descriptors, otherwise
            # zombies will arise
            popen.wait()
        self.popens = []
        return 'stopped %s' % stopped

    def kill(self):
        """
        Send a "killall" command to all worker pools to cleanup everything
        in case of hard out of memory situations
        """
        killed = []
        for host, cores, args in ssh_args(self.zworkers):
            args = args[:-1] + ['killall', '-r', 'oq-zworker|multiprocessing']
            print(' '.join(args))
            subprocess.run(args)
            killed.append(host)
        return 'killed %s' % killed

    def status(self):
        """
        :returns: a list [(host, running, total), ...]
        """
        executing = []
        for host, _cores in self.host_cores:
            if not general.socket_ready((host, self.ctrl_port)):
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            with z.Socket(ctrl_url, z.zmq.REQ, 'connect') as sock:
                running = len(sock.send('get_executing').split())
                total = sock.send('get_num_workers')
                executing.append((host, running, total))
        return executing

    def wait(self, seconds=120):
        """
        Wait until all workers are active
        """
        num_hosts = len(self.zworkers.host_cores.split(','))
        for _ in range(seconds):
            time.sleep(1)
            status = self.status()
            if len(status) == num_hosts and all(
                    total for host, running, total in status):
                break
        else:
            raise TimeoutError(status)
        return status

    def restart(self):
        """
        Stop and start again
        """
        for host, _ in self.host_cores:
            if not general.socket_ready((host, self.ctrl_port)):
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            with z.Socket(ctrl_url, z.zmq.REQ, 'connect', timeout=120) as sock:
                sock.send('restart')
        return 'restarted'

    def debug(self):
        """
        Start the workers, run a debug job, print some info and stop
        """
        self.start()
        try:
            mon = performance.Monitor('zmq-debug')
            mon.inject = True
            mon.config = config  # forget this and it will hang silently
            rec_host = config.dbserver.receiver_host or '127.0.0.1'
            receiver = 'tcp://%s:%s' % (
                rec_host, config.dbserver.receiver_ports)
            ntasks = len(self.host_cores) * 2
            task_no = 0
            with z.Socket(receiver, z.zmq.PULL, 'bind') as pull:
                mon.backurl = 'tcp://%s:%s' % (rec_host, pull.port)
                for host, _ in self.host_cores:
                    url = 'tcp://%s:%d' % (host, self.ctrl_port)
                    print('Sending to', url)
                    with z.Socket(url, z.zmq.REQ, 'connect') as sock:
                        for i in range(2):
                            msg = 'executing task #%d' % task_no
                            sock.send((debug_task, (msg,), task_no, mon))
                            task_no += 1
                results = list(get_results(pull, ntasks))
                print(f'{results=}')
        finally:
            self.stop()
        return 'debugged'


def get_results(socket, n):
    for res in socket:
        if n == 0:
            return
        elif res.msg != 'TASK_ENDED':
            yield res.get()
            n -= 1


def debug_task(msg, mon):
    """
    Trivial task useful for debugging
    """
    print(socket.gethostname(), msg)
    # while True: pass
    return mon.task_no


def call(func, args, taskno, mon, executing):
    fname = os.path.join(executing, '%s-%s' % (mon.calc_id, taskno))
    # NB: very hackish way of keeping track of the running tasks,
    # used in get_executing, could litter the file system
    open(fname, 'w').close()
    parallel.safely_call(func, args, taskno, mon)
    os.remove(fname)


def errback(job_id, task_no, exc):
    from openquake.commonlib.logs import dbcmd
    dbcmd('log', job_id, datetime.utcnow(), 'ERROR',
          '%s/%s' % (job_id, task_no), str(exc))
    raise exc
    e = exc.__class__('in job %d, task %d' % (job_id, task_no))
    raise e.with_traceback(exc.__traceback__)


class WorkerPool(object):
    """
    A pool of workers accepting various commands.

    :param ctrl_url: zmq address of the control socket
    :param num_workers: the number of workers (or -1)
    """
    def __init__(self, ctrl_url, num_workers=-1):
        self.ctrl_url = ctrl_url
        if num_workers == -1:
            try:
                self.num_workers = len(psutil.Process().cpu_affinity())
            except AttributeError:  # missing cpu_affinity on macOS
                self.num_workers = psutil.cpu_count()
        else:
            self.num_workers = num_workers
        self.executing = tempfile.mkdtemp()
        self.pid = os.getpid()

    def start(self):
        """
        Start worker processes and a control loop
        """
        title = 'oq-zworkerpool %s' % self.ctrl_url[6:]  # strip tcp://
        print('Starting ' + title, file=sys.stderr)
        setproctitle(title)
        self.pool = general.mp.Pool(self.num_workers, init_workers)
        # start control loop accepting the commands stop and kill
        try:
            with z.Socket(self.ctrl_url, z.zmq.REP, 'bind') as ctrlsock:
                for cmd in ctrlsock:
                    if cmd == 'stop':
                        ctrlsock.send(self.stop())
                        break
                    elif cmd == 'restart':
                        self.stop()
                        self.pool = general.mp.Pool(self.num_workers)
                        ctrlsock.send('restarted')
                    elif cmd == 'getpid':
                        ctrlsock.send(self.proc.pid)
                    elif cmd == 'get_num_workers':
                        ctrlsock.send(self.num_workers)
                    elif cmd == 'get_executing':
                        executing = sorted(os.listdir(self.executing))
                        ctrlsock.send(' '.join(executing))
                    elif isinstance(cmd, tuple):
                        func, args, taskno, mon = cmd
                        eback = functools.partial(errback, mon.calc_id, taskno)
                        self.pool.apply_async(call, cmd + (self.executing,),
                                              error_callback=eback)
                        ctrlsock.send('submitted')
                    else:
                        ctrlsock.send('unknown command')
        finally:
            shutil.rmtree(self.executing)

    def stop(self):
        """
        Terminate the pool
        """
        self.pool.close()
        self.pool.terminate()
        self.pool.join()
        return 'WorkerPool %s stopped' % self.ctrl_url


def workerpool(worker_url='tcp://0.0.0.0:1909', *, num_workers: int = -1):
    """
    Start a workerpool on the given URL with the given number of workers.
    """
    # NB: unexpected errors will appear in the DbServer log
    wpool = WorkerPool(worker_url, num_workers)
    try:
        wpool.start()
    finally:
        wpool.stop()


workerpool.worker_url = dict(
    help='ZMQ address (tcp:///w.x.y.z:port) of the worker')
workerpool.num_workers = dict(help='number of cores to use')

if __name__ == '__main__':
    sap.run(workerpool)
