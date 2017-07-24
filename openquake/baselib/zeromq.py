import multiprocessing
import threading
import pickle
import zmq
from openquake.baselib.parallel import safely_call

REQ = zmq.REQ
REP = zmq.REP
PUSH = zmq.PUSH
PULL = zmq.PULL
ROUTER = zmq.ROUTER
DEALER = zmq.DEALER
POLLIN = zmq.POLLIN
POLLOUT = zmq.POLLOUT

_context = None  # global context


class _Context(zmq.Context):
    """
    A zmq Context subclass with methods .bind and .connect
    """
    def bind(self, end_point, socket_type, **kw):
        identity = kw.pop('identity') if 'identity' in kw else None
        socket = self.socket(socket_type, **kw)
        if identity:
            socket.identity = identity
        try:
            socket.bind(end_point)
        except Exception as exc:  # invalid end_point
            socket.close()
            raise exc.__class__('%s: %s' % (exc, end_point))
        return socket

    def connect(self, end_point, socket_type, **kw):
        identity = kw.pop('identity') if 'identity' in kw else None
        socket = self.socket(socket_type, **kw)
        if identity:
            socket.identity = identity
        try:
            socket.connect(end_point)
        except Exception as exc:  # invalid end_point
            socket.close()
            raise exc.__class__('%s: %s' % (exc, end_point))
        return socket


def context():
    """
    Returns the global context. If the context is closed, recreate it.
    """
    global _context
    if _context is None or _context.closed:
        _context = _Context()
    return _context


class Process(multiprocessing.Process):
    """
    Process with a zmq socket
    """
    def __init__(self, func, *args, **kw):
        def newfunc(*args, **kw):
            with context() as c:
                func(c, *args, **kw)
        super(Process, self).__init__(target=newfunc, args=args, kwargs=kw)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, etype, exc, tb):
        self.join()


class Thread(threading.Thread):
    """
    Thread with a zmq socket
    """
    def __init__(self, func, *args, **kw):
        def newfunc(*args, **kw):
            try:
                func(*args, **kw)
            except zmq.ContextTerminated:  # CTRL-C was given
                pass
        args = (context(), ) + args
        super(Thread, self).__init__(target=newfunc, args=args, kwargs=kw)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, etype, exc, tb):
        self.join()


@classmethod
def startmany(cls, func, iterargs):
    """
    :param cls: Thread or Process
    :param func: a callable func(*args)
    :param iterargs: an iterator over argument tuples
    :returns: a list of started Thread/Process instances
    """
    procs = [cls(func, *args) for args in iterargs]
    for proc in procs:
        proc.start()
    return procs


def poller(socket, polling_type):
    """
    A zmq Poller associated to the given socket and poller type
    """
    poll = zmq.Poller()
    poll.register(socket, polling_type)
    return poll


def proxy(context, frontend_url, backend_url):
    """
    A zmq proxy routing messages from the frontend to the backend and back
    """
    with context.bind(frontend_url, ROUTER) as frontend, \
            context.bind(backend_url, DEALER) as backend:
        zmq.proxy(frontend, backend)


def worker(context, backend_url):
    """
    A worker reading messages of the form (cmd, args) and returning
    results to the backend via a zmq socket
    """
    with context.connect(backend_url, DEALER) as socket:
        while True:
            ident, pik = socket.recv_multipart()
            cmd, args = pickle.loads(pik)
            if cmd == 'stop':
                break
            res = safely_call(cmd, args)
            socket.send_multipart([ident, pickle.dumps(res)])


def starmap(context, frontend_url, func, allargs):
    """
    starmap a function over an iterator of arguments by using a zmq socket
    """
    with context.connect(frontend_url, DEALER) as socket:
        poll = poller(socket, POLLIN)
        n = len(allargs)
        for args in allargs:
            socket.send_pyobj((func, args))
        while n:
            if poll.poll(1000):
                yield socket.recv_pyobj()
                n -= 1


if __name__ == '__main__':  # run worker
    import sys
    with context() as c:
        worker(c, sys.argv[1])
