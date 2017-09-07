import os
import zmq

context = zmq.Context()


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

if __name__ == '__main__':
    print('started echo server, pid=%d' % os.getpid())
    sock = ReplySocket('tcp://127.0.0.1:9000')
    for args in sock:  # echo server for testing purposes
        sock.reply(args)
