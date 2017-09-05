import os
import zmq

context = zmq.Context()


def bind(end_point, socket_type):
    """
    Bind to a zmq URL; raise a proper error if the URL is invalid; return
    a zmq socket.
    """
    sock = context.socket(socket_type)
    try:
        sock.bind(end_point)
    except zmq.error.ZMQError as exc:
        sock.close()
        raise exc.__class__('%s: %s' % (exc, end_point))
    return sock


def connect(end_point, socket_type):
    """
    Connect to a zmq URL; raise a proper error if the URL is invalid; return
    a zmq socket.
    """
    sock = context.socket(socket_type)
    try:
        sock.connect(end_point)
    except zmq.error.ZMQError as exc:
        sock.close()
        raise exc.__class__('%s: %s' % (exc, end_point))
    return sock


class Socket(object):
    """
    A Socket class to be used with code like the following::

     # server
     sock = Socket('tcp://127.0.0.1:9000', zmq.REP)
     for cmd, *args in sock:
         sock.rep(cmd(*args))

     # client
     Socket('tcp://127.0.0.1:9000', zmq.REQ).req(cmd, *args)
    """
    def __init__(self, end_point, socket_type):
        assert socket_type in (zmq.REP, zmq.REQ, zmq.PULL, zmq.PUSH)
        self.end_point = end_point
        self.socket_type = socket_type

    def __iter__(self):
        assert self.socket_type in (zmq.REP, zmq.PULL)
        self.zsocket = bind(self.end_point, self.socket_type)
        with self.zsocket:
            while True:
                try:
                    args = self.zsocket.recv_pyobj()
                except (KeyboardInterrupt, zmq.error.ZMQError):
                    # sending SIGTERM raises ZMQError
                    break
                if args[0] == 'stop':
                    if self.socket_type == zmq.REP:
                        self.rep((None, None, None))
                    break
                else:
                    yield args

    def rep(self, obj):
        """
        Reply to a request with the given object
        """
        assert self.socket_type == zmq.REP
        self.zsocket.send_pyobj(obj)

    def req(self, *args):
        """
        Make a request to a remote server with the given arguments and
        returns the reply.
        """
        assert self.socket_type == zmq.REQ
        zsocket = connect(self.end_point, zmq.REQ)
        with zsocket:
            zsocket.send_pyobj(args)
            return zsocket.recv_pyobj()

    def push(self, *args):
        """
        Make a push to a remote server with the given argument.
        """
        assert self.socket_type == zmq.PUSH
        zsocket = connect(self.end_point, zmq.PUSH)
        with zsocket:
            zsocket.send_pyobj(args)


if __name__ == '__main__':
    print('started echo server, pid=%d' % os.getpid())
    sock = Socket('tcp://127.0.0.1:9000', zmq.PUSH)
    for args in sock:  # server for testing purposes
        sock.rep(args)
