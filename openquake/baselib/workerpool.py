import os
import sys
import signal
import logging
import inspect
import subprocess
import traceback
import multiprocessing
from openquake.baselib import zeromq as z, general
from openquake.baselib.performance import Monitor
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"


def safely_call(func, args):
    """
    Call the given function with the given arguments safely, i.e.
    by trapping the exceptions. Return a pair (result, exc_type)
    where exc_type is None if no exceptions occur, otherwise it
    is the exception class and the result is a string containing
    error message and traceback.

    :param func: the function to call
    :param args: the arguments
    """
    with Monitor('total ' + func.__name__, measuremem=True) as child:
        if args and hasattr(args[0], 'unpickle'):
            # args is a list of Pickled objects
            args = [a.unpickle() for a in args]
        if args and isinstance(args[-1], Monitor):
            mon = args[-1]
            mon.children.append(child)  # child is a child of mon
            child.hdf5path = mon.hdf5path
        else:
            mon = child
        # FIXME check_mem_usage is disabled here because it's causing
        # dead locks in threads when log messages are raised.
        # Check is done anyway in other parts of the code (submit and iter);
        # further investigation is needed
        # check_mem_usage(mon)  # check if too much memory is used
        # FIXME: this approach does not work with the Threadmap
        mon._flush = False
        try:
            got = func(*args)
            if inspect.isgenerator(got):
                got = list(got)
            res = got, None, mon
        except:
            etype, exc, tb = sys.exc_info()
            tb_str = ''.join(traceback.format_tb(tb))
            res = ('\n%s%s: %s' % (tb_str, etype.__name__, exc),
                   etype, mon)
        finally:
            mon._flush = True
    return res


def streamer(host, task_in_port, task_out_port):
    """
    A streamer for zmq workers.

    :param host: name or IP of the controller node
    :param task_in_port: port where to send the tasks
    :param task_out_port: port from where to receive the tasks
    """
    try:
        z.zmq.proxy(z.bind('tcp://%s:%s' % (host, task_in_port), z.zmq.PULL),
                    z.bind('tcp://%s:%s' % (host, task_out_port), z.zmq.PUSH))
    except (KeyboardInterrupt, z.zmq.ZMQError):
        pass  # killed cleanly by SIGINT/SIGTERM


def _starmap(func, iterargs, host, task_in_port, receiver_ports):
    # called by parallel.Starmap.submit_all; should not be used directly
    receiver_url = 'tcp://%s:%s' % (host, receiver_ports)
    task_in_url = 'tcp://%s:%s' % (host, task_in_port)
    with z.Socket(receiver_url, z.zmq.PULL, 'bind') as receiver:
        logging.info('Receiver port for %s=%s', func.__name__, receiver.port)
        receiver_host = receiver.end_point.rsplit(':', 1)[0]
        backurl = '%s:%s' % (receiver_host, receiver.port)
        with z.Socket(task_in_url, z.zmq.PUSH, 'connect') as sender:
            n = 0
            for args in iterargs:
                args[-1].backurl = backurl  # args[-1] is a Monitor instance
                sender.send((func, args))
                n += 1
        yield n
        for _ in range(n):
            obj = receiver.zsocket.recv_pyobj()
            # receive n responses for the n requests sent
            yield obj


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
        self.task_in_port = task_in_port
        self.task_out_url = 'tcp://%s:%s' % (master_host, task_out_port)
        self.ctrl_port = int(ctrl_port)
        self.host_cores = [hc.split() for hc in host_cores.split(',')]
        self.remote_python = remote_python or sys.executable

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
        Start multiple workerpools, possibly on remote servers via ssh
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
            args += ['-m', 'openquake.baselib.workerpool',
                     ctrl_url, self.task_out_url, cores]
            starting.append(' '.join(args))
            subprocess.Popen(args)
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
        for cmd, args in sock:
            backurl = args[-1].backurl  # attached to the monitor
            with z.Socket(backurl, z.zmq.PUSH, 'connect') as s:
                s.send(safely_call(cmd, args))

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
        ctrlsock = z.Socket(self.ctrl_url, z.zmq.REP, 'bind')
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
    ctrl_url, task_out_port, num_workers = sys.argv[1:]
    WorkerPool(ctrl_url, task_out_port, num_workers).start()
