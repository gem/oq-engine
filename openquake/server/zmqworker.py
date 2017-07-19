from openquake.baselib.parallel import safely_call


def worker(begin_addr, end_addr):
    """
    A worker receiving commands, executing them and sending back replies
    """
    context = zmq.Context()
    receiver = context.socket(zmq.PULL)
    receiver.connect(begin_addr)
    sender = context.socket(zmq.PUSH)
    sender.connect(end_addr)
    while True:
        try:
            func, args = receiver.recv_pyobj()
        except KeyboardInterrupt:
            break
        if func == 'stop':
            break
        triple = safely_call(func, args)
        sender.send_pyobj(triple)
    receiver.close()
    sender.close()

if __name__ == '__main__':
    import sys
    import zmq  # imported only if used
    worker(*sys.argv[1:])
