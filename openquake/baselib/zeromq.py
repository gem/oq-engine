import multiprocessing
import threading
import zmq
from openquake.baselib.python3compat import pickle
from openquake.baselib.parallel import safely_call

REQ = zmq.REQ
REP = zmq.REP
PUSH = zmq.PUSH
PULL = zmq.PULL
ROUTER = zmq.ROUTER
DEALER = zmq.DEALER
PUB = zmq.PUB
SUB = zmq.SUB
POLLIN = zmq.POLLIN
POLLOUT = zmq.POLLOUT


class Context(zmq.Context):
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


class Process(multiprocessing.Process):
    """
    Process with a zmq socket
    """
    def __init__(self, func, *args, **kw):
        def newfunc(*args, **kw):
            # the only reason it is not .instance() is that there may be a
            # stale Context instance already initialized, from the docs
            with Context() as c:
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
        args = (Context.instance(), ) + args
        super(Thread, self).__init__(target=newfunc, args=args, kwargs=kw)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, etype, exc, tb):
        self.join()


def proxy(context, frontend_url, backend_url):
    """
    A zmq proxy routing messages from the frontend to the backend and back
    """
    with context.bind(frontend_url, ROUTER) as frontend, \
            context.bind(backend_url, DEALER) as backend:
        zmq.proxy(frontend, backend)


def worker(context, backend_url, func=None):
    """
    A worker reading tuples and returning results to the backend via a zmq
    socket.

    :param context: zmq context
    :param backend_url: URL where to connect
    :param func: if None, expects message to be pairs (cmd, args) else args
    """
    socket = context.connect(backend_url, DEALER)
    while True:
        ident, pik = socket.recv_multipart()
        if func is None:  # retrieve the cmd from the message
            cmd, args = pickle.loads(pik)
        else:  # use the provided func as cmd
            cmd, args = func, pickle.loads(pik)
        if cmd == 'stop':
            break
        res = safely_call(cmd, args)
        socket.send_multipart([ident, pickle.dumps(res)])


def starmap(context, frontend_url, func, allargs):
    """
    starmap a function over an iterator of arguments by using a zmq socket
    """
    with context.connect(frontend_url, DEALER) as socket:
        n = 0
        for args in allargs:
            socket.send_pyobj((func, args))
            n += 1
        yield n
        while n:
            if socket.poll(1000):
                yield socket.recv_pyobj()
                n -= 1


if __name__ == '__main__':  # run worker
    import sys
    with Context.instance() as c:
        worker(c, sys.argv[1])
