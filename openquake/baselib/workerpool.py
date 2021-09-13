# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2021, GEM Foundation
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
import signal
import shutil
import getpass
import tempfile
import subprocess
import multiprocessing
import psutil
from openquake.baselib import (
    zeromq as z, general, parallel, config, sap, InvalidFile)
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"


def _streamer():
    # streamer for zmq workers running on the master node
    port = int(config.zworkers.ctrl_port)
    task_input_url = 'tcp://0.0.0.0:%d' % (port + 2)
    task_output_url = 'tcp://%s:%s' % (config.dbserver.listen, port + 1)
    try:
        z.zmq.proxy(z.bind(task_input_url, z.zmq.PULL),
                    z.bind(task_output_url, z.zmq.PUSH))
    except (KeyboardInterrupt, z.zmq.ContextTerminated):
        pass  # killed cleanly by SIGINT/SIGTERM


class WorkerMaster(object):
    """
    :param ctrl_port: port on which the worker pools listen
    :param host_cores: names of the remote hosts and number of cores to use
    :param remote_python: path of the Python executable on the remote hosts
    """
    def __init__(self, ctrl_port=config.zworkers.ctrl_port,
                 host_cores=config.zworkers.host_cores,
                 remote_user=config.zworkers.remote_user,
                 remote_python=config.zworkers.remote_python,
                 receiver_ports=None):
        # NB: receiver_ports is not used but needed for compliance
        self.ctrl_port = int(ctrl_port)
        self.host_cores = ([hc.split() for hc in host_cores.split(',')]
                           if host_cores else [])
        for host, cores in self.host_cores:
            if int(cores) < -1:
                raise InvalidFile('openquake.cfg: found %s %s' %
                                  (host, cores))
        self.remote_python = remote_python or sys.executable
        self.remote_user = remote_user or getpass.getuser()
        self.popens = []

    def start(self):
        """
        Start multiple workerpools, possibly on remote servers via ssh,
        assuming there is an active streamer.
        """
        starting = []
        for host, cores in self.host_cores:
            if general.socket_ready((host, self.ctrl_port)):
                print('%s:%s already running' % (host, self.ctrl_port))
                continue
            ctrl_url = 'tcp://0.0.0.0:%s' % self.ctrl_port
            if host == '127.0.0.1':  # localhost
                args = [sys.executable]
            else:
                args = ['ssh', '-f', '-T', f'{self.remote_user}@{host}',
                        self.remote_python]
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
        for host, _ in self.host_cores:
            args = ['ssh', '-f', '-T', f'{self.remote_user}@{host}',
                    'killall', '-u', 'openquake']
            if host != '127.0.0.1':
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

    def restart(self):
        """
        Stop and start again
        """
        self.stop()
        self.start()
        return 'restarted'


def worker(sock, executing):
    """
    :param sock: a zeromq.Socket of kind PULL
    :param executing: a path inside /tmp/calc_XXX
    """
    setproctitle('oq-zworker')
    with sock:
        for cmd, args, taskno, mon in sock:
            fname = os.path.join(executing, '%s-%s' % (mon.calc_id, taskno))
            # NB: very hackish way of keeping track of the running tasks,
            # used in get_executing, could litter the file system
            open(fname, 'w').close()
            parallel.safely_call(cmd, args, taskno, mon)
            os.remove(fname)


class WorkerPool(object):
    """
    A pool of workers accepting the command 'stop' and 'kill' and reading
    tasks to perform from the task_server_url.

    :param ctrl_url: zmq address of the control socket
    :param num_workers: the number of workers (or -1)
    """
    def __init__(self, ctrl_url, num_workers=-1):
        self.ctrl_url = ctrl_url
        self.task_server_url = 'tcp://%s:%s' % (
            config.dbserver.host, int(config.zworkers.ctrl_port) + 1)
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
        # start workers
        self.workers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.task_server_url, z.zmq.PULL, 'connect')
            sock.proc = multiprocessing.Process(
                target=worker, args=(sock, self.executing))
            sock.proc.start()
            self.workers.append(sock)

        # start control loop accepting the commands stop and kill
        with z.Socket(self.ctrl_url, z.zmq.REP, 'bind') as ctrlsock:
            for cmd in ctrlsock:
                if cmd in ('stop', 'kill'):
                    msg = getattr(self, cmd)()
                    ctrlsock.send(msg)
                    break
                elif cmd == 'getpid':
                    ctrlsock.send(self.proc.pid)
                elif cmd == 'get_num_workers':
                    ctrlsock.send(self.num_workers)
                elif cmd == 'get_executing':
                    ctrlsock.send(' '.join(sorted(os.listdir(self.executing))))
        shutil.rmtree(self.executing)

    def stop(self):
        """
        Send a SIGTERM to all worker processes
        """
        for sock in self.workers:
            os.kill(sock.proc.pid, signal.SIGTERM)
        for sock in self.workers:
            sock.proc.join()
        return 'WorkerPool %s stopped' % self.ctrl_url

    def kill(self):
        """
        Send a SIGKILL to all worker processes
        """
        for sock in self.workers:
            os.kill(sock.proc.pid, signal.SIGKILL)
        for sock in self.workers:
            sock.proc.join()
        return 'WorkerPool %s killed' % self.ctrl_url


def workerpool(worker_url='tcp://0.0.0.0:1909', *, num_workers: int = -1):
    # start a workerpool without a streamer
    WorkerPool(worker_url, num_workers).start()


workerpool.worker_url = dict(
    help='ZMQ address (tcp:///w.x.y.z:port) of the worker')
workerpool.num_workers = dict(help='number of cores to use')

if __name__ == '__main__':
    sap.run(workerpool)
