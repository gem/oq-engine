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
        self.zsocket = bind(self.end_point, zmq.REP)
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

    def request(self, *args):
        """
        Make a request to a remote server with the given arguments and
        returns the reply.
        """
        zsocket = connect(self.end_point, zmq.REQ)
        with zsocket:
            zsocket.send_pyobj(args)
            return zsocket.recv_pyobj()

if __name__ == '__main__':
    print('started echo server, pid=%d' % os.getpid())
    sock = ReplySocket('tcp://127.0.0.1:9000')
    for args in sock:  # echo server for testing purposes
        sock.reply(args)
