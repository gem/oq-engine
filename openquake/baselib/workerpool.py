import os
import sys
import signal
import multiprocessing
from openquake.baselib import zeromq as z, parallel as p


def starmap(frontend_url, backend_url, func, iterargs):
    """
    starmap a function over an iterator of arguments by using a zmq socket.

    :param frontend_url:
    :param backend_url: url with a range of ports
    :param func:
    :param iterargs:
    """
    with z.Socket(backend_url, z.zmq.PULL) as receiver, \
         z.Socket(frontend_url, z.zmq.PUSH, 'connect') as sender:
        n = 0
        for args in iterargs:
            args[-1].backurl = receiver.true_end_point
            sender.send_pyobj((func, args))
            n += 1
        yield n
        for _ in range(n):
            # receive n responses for the n requests sent
            yield receiver.zsocket.recv_pyobj()


class WorkerPool(object):
    """
    A pool of workers accepting the command 'stop' and 'kill' and reading
    tasks to perform from the stream_url.

    :param ctrl_url: zmq address of the control socket
    :param stream_url: zmq address of the task streamer
    :param num_workers: a string with the number of workers (or 'default')
    """
    def __init__(self, ctrl_url, stream_url, num_workers='default'):
        self.ctrl_url = ctrl_url
        self.stream_url = stream_url
        self.num_workers = (multiprocessing.cpu_count()
                            if num_workers == 'default' else int(num_workers))
        self.pid = os.getpid()

    def worker(self, sock):
        for cmd_ in sock:
            cmd, args = cmd_[0], cmd_[1:]
            backurl = args[-1].backurl  # attached to the monitor
            with z.Socket(backurl, z.zmq.PUSH, 'connect') as s:
                s.push(p.safely_call(cmd, args))

    def start(self):
        # start workers
        self.workers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.stream_url, z.zmq.PULL, 'connect')
            proc = multiprocessing.Process(target=self.worker, args=(sock,))
            proc.start()
            sock.pid = proc.pid
            self.workers.append(sock)
        # print pid
        sys.stdout.write('%d\n' % self.pid)
        sys.stdout.flush()
        # start control loop accepting the commands stop and kill
        ctrlsock = z.Socket(self.ctrl_url, z.zmq.REP)
        for cmd in ctrlsock:
            assert cmd in ('stop', 'kill'), cmd
            msg = getattr(self, cmd)()
            ctrlsock.send(msg)

    def stop(self):
        for sock in self.workers:
            os.kill(sock.pid, signal.SIGINT)
        return 'WorkerPool %s stopped' % self.ctrl_url

    def kill(self):
        for sock in self.workers:
            os.kill(sock.pid, signal.SIGTERM)
        return 'WorkerPool %s killed' % self.ctrl_url


if __name__ == '__main__':
    ctrl_url, stream_url, num_workers = sys.argv[1:]
    WorkerPool(ctrl_url, stream_url, num_workers).start()
