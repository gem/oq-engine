import multiprocessing
import functools
import threading
import zmq
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
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

# NB: using a global context is probably good: http://250bpm.com/blog:23
context = _Context()


class ReplySocket(object):
    """
    A ReplySocket class to be used with code like the following:

     sock = ReplySocket('tcp://127.0.0.1:8000')
     for cmd, *args in sock:
         sock.reply(cmd(*args))
    """
    def __init__(self, end_point):
        self.end_point = end_point

    def __iter__(self):
        self.zsocket = context.socket(zmq.REP)
        self.zsocket.bind(self.end_point)
        with self.zsocket:
            while True:
                try:
                    args = self.zsocket.recv_pyobj()
                except (KeyboardInterrupt, zmq.error.ZMQError):
                    # sending SIGTERM raises ZMQError
                    break
                if args[0] == 'stop':
                    self.reply((None, None, None))
                    break
                else:
                    yield args

    def reply(self, obj):
        self.zsocket.send_pyobj(obj)


def request(end_point, *args):
    """
    Make a request to a remote server with the given arguments and
    returns the reply.
    """
    zsocket = context.socket(zmq.REQ)
    zsocket.connect(end_point)
    with zsocket:
        zsocket.send_pyobj(args)
        return zsocket.recv_pyobj()


class Process(multiprocessing.Process):
    """
    Process with a zmq socket
    """
    def __init__(self, func, *args, **kw):
        def newfunc(*args, **kw):
            # the only reason it is not .instance() is that there may be a
            # stale Context instance already initialized, from the docs
            with context:
                func(*args, **kw)
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
        super(Thread, self).__init__(target=newfunc, args=args, kwargs=kw)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, etype, exc, tb):
        self.join()


def proxy(frontend_url, backend_url):
    """
    A zmq proxy routing messages from the frontend to the backend and back
    """
    with context.bind(frontend_url, ROUTER) as frontend, \
            context.bind(backend_url, DEALER) as backend:
        zmq.proxy(frontend, backend)


def workerpool(backend_url, ncores=None, func=safely_call):
    """
    A worker reading tuples and returning results to the backend via a zmq
    socket.

    :param backend_url: URL where to connect
    :param ncores: number of cores to use (default all)
    :param func: function to call (default safely_call)
    """
    title = 'oq-worker'
    pool = multiprocessing.Pool(ncores, setproctitle, (title,))
    socket = context.connect(backend_url, DEALER)
    while True:
        ident, pik = socket.recv_multipart()
        args = pickle.loads(pik)
        if args[0] == 'stop':
            print('Terminating workerpool')
            pool.terminate()
            break
        pool.apply_async(func, args,
                         callback=functools.partial(sendback, socket, ident))


def sendback(socket, ident, res):
    socket.send_multipart([ident, pickle.dumps(res)])


def starmap(frontend_url, func, allargs):
    """
    starmap a function over an iterator of arguments by using a zmq socket
    """
    with context.connect(frontend_url, DEALER) as socket:
        n = 0
        for args in allargs:
            socket.send_pyobj((func, args))
            n += 1
        yield n
        for _ in range(n):
            yield socket.recv_pyobj()


if __name__ == '__main__':  # run workers
    import sys
    try:
        url, _ncores = sys.argv[1:]
        ncores = int(_ncores)
    except ValueError:  # _ncores is the string 'default'
        url = sys.argv[1]
        ncores = None
    with context:
        workerpool(url, ncores)
