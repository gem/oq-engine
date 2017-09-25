import os
import sys
import signal
import logging
import multiprocessing
from openquake.baselib import zeromq as z, parallel as p


def starmap(frontend_url, backend_url, func, allargs):
    """
    starmap a function over an iterator of arguments by using a zmq socket
    """
    backurl, receiver = z.bind_to_random_port(backend_url, z.zmq.PULL)
    sender = z.connect(frontend_url, z.zmq.PUSH)
    with sender:
        n = 0
        for args in allargs:
            args[-1].backurl = backurl
            sender.send_pyobj((func, args))
            n += 1
        yield n
    with receiver:
        for _ in range(n):
            yield receiver.recv_pyobj()


class WorkerPool(object):
    """
    """
    def __init__(self, backend, num_workers=None):
        self.backend = backend
        self.num_workers = num_workers or multiprocessing.cpu_count()
        self.pid = os.getpid()

    def worker(self, sock):
        for cmd_ in sock:
            cmd, args = cmd_[0], cmd_[1:]
            with z.Socket(args[-1].backurl, z.zmq.PUSH) as s:
                s.push(p.safely_call(cmd, args))

    def start(self):
        # start workers
        self.workers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.backend, z.zmq.PULL, 'connect')
            proc = multiprocessing.Process(target=self.worker, args=(sock,))
            proc.start()
            sock.pid = proc.pid
            self.workers.append(sock)
        logging.warn('WorkerPool started with %s on %s, pid=%d',
                     sys.executable, self.backend, self.pid)
        # start control socket

    def stop(self):
        for sock in self.workers:
            os.kill(sock.pid, signal.SIGTERM)
        logging.warn('WorkerPool stopped')


if __name__ == '__main__':
    kind, frontend, backend, num_workers = sys.argv[1:]
    if kind == 'master':
        # start frontend->backend proxy
        try:
            z.zmq.proxy(z.bind(frontend, z.zmq.PULL),
                        z.bind(backend, z.zmq.PUSH))
        except (KeyboardInterrupt, z.zmq.ZMQError):
            pass
    elif kind == 'workerpool':
        WorkerPool(backend, num_workers).start()
    else:
        raise ValueError('Unknown pool kind: %s' % kind)
