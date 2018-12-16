import os
import sys
import signal
import subprocess
import multiprocessing
from openquake.baselib import zeromq as z, general, parallel
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"


def _streamer(host, task_in_port, task_out_port):
    # streamer for zmq workers
    try:
        z.zmq.proxy(z.bind('tcp://%s:%s' % (host, task_in_port), z.zmq.PULL),
                    z.bind('tcp://%s:%s' % (host, task_out_port), z.zmq.PUSH))
    except (KeyboardInterrupt, z.zmq.ZMQError):
        pass  # killed cleanly by SIGINT/SIGTERM


class WorkerMaster(object):
    """
    :param master_host: hostname or IP of the master node
    :param task_in_port: port where to send the tasks
    :param task_out_port: port from where to read the tasks
    :param ctrl_port: port on which the worker pools listen
    :param host_cores: names of the remote hosts and number of cores to use
    :param remote_python: path of the Python executable on the remote hosts
    """
    def __init__(self, master_host, task_in_port, task_out_port, ctrl_port,
                 host_cores, remote_python=None, receiver_ports=None):
        # receiver_ports is not used
        self.master_host = master_host
        self.task_in_port = task_in_port
        self.task_out_port = task_out_port
        self.task_in_url = 'tcp://%s:%s' % (master_host, task_in_port)
        self.task_out_url = 'tcp://%s:%s' % (master_host, task_out_port)
        self.ctrl_port = int(ctrl_port)
        self.host_cores = [hc.split() for hc in host_cores.split(',')]
        self.remote_python = remote_python or sys.executable
        self.pids = []

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

    def start(self, streamer=False):
        """
        Start multiple workerpools, possibly on remote servers via ssh,
        and possibly a streamer, depending on the `streamercls`.

        :param streamer:
            if True, starts a streamer with multiprocessing.Process
        """
        if streamer and not general.socket_ready(self.task_in_url):  # started
            self.streamer = multiprocessing.Process(
                target=_streamer,
                args=(self.master_host, self.task_in_port, self.task_out_port))
            self.streamer.start()
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
            args += ['-m', 'openquake.baselib.workerpool',
                     ctrl_url, self.task_out_url, cores]
            starting.append(' '.join(args))
            po = subprocess.Popen(args)
            self.pids.append(po.pid)
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
        if hasattr(self, 'streamer'):
            self.streamer.terminate()
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
        if hasattr(self, 'streamer'):
            self.streamer.terminate()
        return 'killed %s' % killed

    def restart(self):
        """
        Stop and start again
        """
        self.stop()
        self.start()
        return 'restarted'


class WorkerPool(object):
    """
    A pool of workers accepting the command 'stop' and 'kill' and reading
    tasks to perform from the task_out_port.

    :param ctrl_url: zmq address of the control socket
    :param task_out_port: zmq address of the task streamer
    :param num_workers: a string with the number of workers (or '-1')
    """
    def __init__(self, ctrl_url, task_out_port, num_workers='-1'):
        self.ctrl_url = ctrl_url
        self.task_out_port = task_out_port
        self.num_workers = (multiprocessing.cpu_count()
                            if num_workers == '-1' else int(num_workers))
        self.pid = os.getpid()

    def worker(self, sock):
        """
        :param sock: a zeromq.Socket of kind PULL receiving (cmd, args)
        """
        setproctitle('oq-zworker')
        with sock:
            for cmd, args, mon in sock:
                parallel.safely_call(cmd, args, mon)

    def start(self):
        """
        Start worker processes and a control loop
        """
        setproctitle('oq-zworkerpool %s' % self.ctrl_url[6:])  # strip tcp://
        # start workers
        self.workers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.task_out_port, z.zmq.PULL, 'connect')
            proc = multiprocessing.Process(target=self.worker, args=(sock,))
            proc.start()
            sock.pid = proc.pid
            self.workers.append(sock)

        # start control loop accepting the commands stop and kill
        with z.Socket(self.ctrl_url, z.zmq.REP, 'bind') as ctrlsock:
            for cmd in ctrlsock:
                if cmd in ('stop', 'kill'):
                    msg = getattr(self, cmd)()
                    ctrlsock.send(msg)
                    break
                elif cmd == 'getpid':
                    ctrlsock.send(self.pid)
                elif cmd == 'get_num_workers':
                    ctrlsock.send(self.num_workers)

    def stop(self):
        """
        Send a SIGTERM to all worker processes
        """
        for sock in self.workers:
            os.kill(sock.pid, signal.SIGTERM)
        return 'WorkerPool %s stopped' % self.ctrl_url

    def kill(self):
        """
        Send a SIGKILL to all worker processes
        """
        for sock in self.workers:
            os.kill(sock.pid, signal.SIGKILL)
        return 'WorkerPool %s killed' % self.ctrl_url


if __name__ == '__main__':
    # start a workerpool without a streamer
    ctrl_url, task_out_port, num_workers = sys.argv[1:]
    WorkerPool(ctrl_url, task_out_port, num_workers).start()
