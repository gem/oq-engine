import os
import sys
import time
import signal
import shutil
import logging
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


class TimeoutError(RuntimeError):
    pass


def _streamer():
    # streamer for zmq workers running on the master node
    port = int(config.zworkers.ctrl_port)
    task_input_url = 'tcp://127.0.0.1:%d' % (port + 2)
    task_output_url = 'tcp://%s:%s' % (config.dbserver.listen, port + 1)
    try:
        z.zmq.proxy(z.bind(task_input_url, z.zmq.PULL),
                    z.bind(task_output_url, z.zmq.PUSH))
    except (KeyboardInterrupt, z.zmq.ContextTerminated):
        pass  # killed cleanly by SIGINT/SIGTERM


def check_status(**kw):
    """
    :returns: a non-empty error string if the streamer or worker pools are down
    """
    c = config.zworkers.copy()
    c.update(kw)
    hostport = config.dbserver.listen, int(c['ctrl_port']) + 1
    errors = []
    if not general.socket_ready(hostport):
        errors.append('The task streamer on %s:%s is down' % hostport)
    for host, status in WorkerMaster(**c).status():
        if status != 'running':
            errors.append('The workerpool on %s is down' % host)
    return '\n'.join(errors)


class WorkerMaster(object):
    """
    :param ctrl_port: port on which the worker pools listen
    :param host_cores: names of the remote hosts and number of cores to use
    :param remote_python: path of the Python executable on the remote hosts
    """
    def __init__(self, ctrl_port=config.zworkers.ctrl_port, host_cores=None,
                 remote_python=None, receiver_ports=None):
        # NB: receiver_ports is not used but needed for compliance
        self.ctrl_port = int(ctrl_port)
        self.host_cores = ([hc.split() for hc in host_cores.split(',')]
                           if host_cores else [])
        for host, cores in self.host_cores:
            if int(cores) < -1:
                raise InvalidFile('openquake.cfg: found %s %s' %
                                  (host, cores))
        self.remote_python = remote_python or sys.executable
        self.popens = []

    def wait(self, seconds=30):
        """
        Wait until all workerpools start
        """
        for _ in range(seconds):
            time.sleep(1)
            status = self.status()
            if all(st == 'running' for host, st in status):
                break
        else:
            raise TimeoutError(status)
        return status

    def status(self, host=None):
        """
        :returns: a list of pairs (hostname, 'running'|'not-running')
        """
        if host is None:
            host_cores = self.host_cores
        else:
            host_cores = [hc for hc in self.host_cores if hc[0] == host]
        lst = []
        for host, _ in host_cores:
            ready = general.socket_ready((host, self.ctrl_port))
            lst.append((host, 'running' if ready else 'not-running'))
        return lst

    def start(self):
        """
        Start multiple workerpools, possibly on remote servers via ssh,
        assuming there is an active streamer.
        """
        starting = []
        for host, cores in self.host_cores:
            if self.status(host)[0][1] == 'running':
                print('%s:%s already running' % (host, self.ctrl_port))
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            if host == '127.0.0.1':  # localhost
                args = [sys.executable]
            else:
                args = ['ssh', host, self.remote_python]
            args += ['-m', 'openquake.baselib.workerpool', ctrl_url,
                     '-n', cores]
            if host != '127.0.0.1':
                logging.warning(
                    '%s: if it hangs, check the ssh keys', ' '.join(args))
            self.popens.append(subprocess.Popen(args))
            starting.append(host)
        return 'starting %s' % starting

    def stop(self):
        """
        Send a "stop" command to all worker pools
        """
        stopped = []
        for host, _ in self.host_cores:
            if self.status(host)[0][1] == 'not-running':
                print('%s not running' % host)
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
        Send a "kill" command to all worker pools
        """
        killed = []
        for host, _ in self.host_cores:
            if self.status(host)[0][1] == 'not-running':
                print('%s not running' % host)
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            with z.Socket(ctrl_url, z.zmq.REQ, 'connect') as sock:
                sock.send('kill')
                killed.append(host)
        for popen in self.popens:
            popen.kill()
        self.popens = []
        return 'killed %s' % killed

    def inspect(self):
        executing = []
        for host, _ in self.host_cores:
            if self.status(host)[0][1] == 'not-running':
                print('%s not running' % host)
                continue
            ctrl_url = 'tcp://%s:%s' % (host, self.ctrl_port)
            with z.Socket(ctrl_url, z.zmq.REQ, 'connect') as sock:
                tasks = sock.send('get_executing')
                executing.append((host, tasks))
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


@sap.Script
def workerpool(worker_url='tcp://0.0.0.0:1909', num_workers=-1):
    # start a workerpool without a streamer
    WorkerPool(worker_url, num_workers).start()


workerpool.arg('worker_url', 'ZMQ address (tcp:///w.x.y.z:port) of the worker')
workerpool.opt('num_workers', 'number of cores to use', type=int)

if __name__ == '__main__':
    workerpool.callfunc()
