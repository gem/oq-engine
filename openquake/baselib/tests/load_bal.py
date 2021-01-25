# ROUTER-REQ example: load balancing
import time
from threading import Thread
from openquake.baselib.zeromq import zmq, Socket

NBR_WORKERS = 2


def worker_thread(i):
    with Socket("tcp://localhost:5671", zmq.REQ, 'connect') as sock:
        sock.send_ident()
        got = []
        for recv in sock:
            if recv == "END":
                print("worker-%d: %s, %ds" % (i, got, sum(got)))
                break
            else:
                time.sleep(recv)
                got.append(recv)
            sock.send_ident()


if __name__ == '__main__':
    for w in range(NBR_WORKERS):
        Thread(target=worker_thread, args=(w,)).start()
    with Socket("tcp://*:5671", zmq.ROUTER, 'bind') as router:
        for dt in [3, 1, 3, 1, 3, 1]:
            router.send(dt)
        for _ in range(NBR_WORKERS):
            router.send('END')
