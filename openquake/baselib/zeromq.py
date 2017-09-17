import os
import zmq

context = zmq.Context()

# from integer socket_type to string
SOCKTYPE = {zmq.REQ: 'REQ', zmq.REP: 'REP',
            zmq.PUSH: 'PUSH', zmq.PULL: 'PULL',
            zmq.ROUTER: 'ROUTER', zmq.DEALER: 'DEALER'}


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

    It also support zmq.PULL/zmq.PUSH sockets, which are asynchronous.

    :param end_point: zmq end point string
    :param socket_type: zmq socket type (integer)
    :param mode: default 'bind', accepts also 'connect'
    :param timeout: default 1000 ms, used when polling the underlying socket
    """
    def __init__(self, end_point, socket_type, mode='bind', timeout=1000):
        assert socket_type in (zmq.REP, zmq.REQ, zmq.PULL, zmq.PUSH)
        assert mode in ('bind', 'connect'), mode
        self.end_point = end_point
        self.socket_type = socket_type
        self.mode = mode
        self.timeout = timeout
        self.running = False

    def check_type(self, method, *socket_types):
        """
        Check that the socket is of the expected type
        """
        if self.socket_type not in socket_types:
            expected = '|'.join(SOCKTYPE[st] for st in socket_types)
            raise ValueError(
                'Socket.%s: the current socket is of type %s, expected %s' %
                (method, SOCKTYPE[self.socket_type], expected))

    def __iter__(self):
        """
        Iterate on the socket and yield the received arguments. Exits if

        1. the flag .running is set to False
        2. the message 'stop' is sent
        3. SIGINT is sent
        4. SIGTERM is sent
        """
        self.check_type('__iter__', zmq.REP, zmq.PULL)
        if self.mode == 'bind':
            self.zsocket = bind(self.end_point, self.socket_type)
        else:  # connect
            self.zsocket = connect(self.end_point, self.socket_type)
        self.running = True
        with self.zsocket:
            while self.running:
                try:
                    if self.zsocket.poll(self.timeout):
                        args = self.zsocket.recv_pyobj()
                    else:
                        continue
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
        self.check_type('rep', zmq.REP)
        self.zsocket.send_pyobj(obj)

    def req(self, *args):
        """
        Make a request to a remote server with the given arguments and
        return the reply.
        """
        self.check_type('req', zmq.REQ)
        zsocket = connect(self.end_point, zmq.REQ)
        with zsocket:
            zsocket.send_pyobj(args)
            return zsocket.recv_pyobj()

    def push(self, *args):
        """
        Make a push to a remote server with the given arguments
        """
        self.check_type('push', zmq.PUSH)
        zsocket = connect(self.end_point, zmq.PUSH)
        with zsocket:
            zsocket.send_pyobj(args)


if __name__ == '__main__':
    print('started echo server, pid=%d' % os.getpid())
    sock = Socket('tcp://127.0.0.1:9000', zmq.REP)
    for args in sock:  # server for testing purposes
        sock.rep(args)
