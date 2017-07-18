import os
import sys
import time
import signal
import logging
import subprocess
import collections
from multiprocessing.connection import Listener, Client, wait
from openquake.baselib.parallel import safely_call

local_cores = ('localhost', os.cpu_count())


class WorkerProxy(object):
    def __init__(self, workerid, address, authkey, pid, free=True):
        self.workerid = workerid
        self.address = address
        self.authkey = authkey
        self.pid = pid
        self._conn = None
        self.free = free

    @property
    def conn(self):
        if self._conn is None:
            self._conn = Client(self.address, authkey=self.authkey)
        return self._conn


class Worker(object):
    def __init__(self, workerid, address, authkey):
        self.address = address
        self.authkey = authkey
        self.workerid = int(workerid)

    def loop(self):
        listener = Listener(self.address, backlog=5, authkey=self.authkey)
        logging.warn('Worker started with %s, listening on %s:%d...',
                     sys.executable, *self.address)
        try:
            while True:
                try:
                    conn = listener.accept()
                except KeyboardInterrupt:
                    break
                except:
                    # unauthenticated connection, for instance by a port
                    # scanner such as the one in manage.py
                    continue
                cmd = conn.recv()  # a tuple (func, arg1, ... argN)
                logging.debug('Got ' + str(cmd))
                if cmd == 'stop':
                    conn.send((None, None, None))
                    conn.close()
                    break
                func, args = cmd
                res, etype, mon = safely_call(func, args)
                mon.workerid = self.workerid
                conn.send((res, etype, mon))
                conn.close()
        finally:
            listener.close()


class MultiProcessPool(object):
    def __init__(self, host_cores=[local_cores], port=5090, authkey=b'secret'):
        self.host_cores = host_cores
        self.port = port
        self.authkey = authkey

    def enter(self):
        this = os.path.abspath(__file__)
        self.proxies = collections.defaultdict(list)
        # create the workers and connect to them
        workerid = 0  # unique worker ID for the current calculation
        self.proxy = []
        for host, cores in self.host_cores:
            for core in range(cores):
                port = self.port + core
                if host == 'localhost':
                    args = [sys.executable, this, str(workerid),
                            host, str(port), self.authkey]
                else:
                    args = ['ssh'] + args
                proc = subprocess.Popen(args)
                proxy = WorkerProxy(workerid, (host, self.port),
                                    self.authkey, proc.pid)
                self.proxies[host].append(proxy)
                self.proxy.append(proxy)
                workerid += 1

    def exit(self):
        for host, proxies in self.proxies.items():
            for proxy in proxies:
                proxy.conn.close()
            if host == 'localhost':
                for proxy in proxies:
                    os.kill(proxy.pid, signal.SIGTERM)
            else:
                subprocess.run(
                    ['ssh', host, 'kill'] + [str(p.pid) for p in proxies])

    def sendall(self, func, iterargs):
        self.enter()
        time.sleep(1)
        try:
            while True:
                for proxy in self.proxy:
                    if proxy.free:
                        try:
                            args = next(iterargs)
                        except StopIteration:
                            return
                        proxy.conn.send((func, args))
                        proxy.free = False
                # wait on the busy connections
                for conn in wait(proxy.conn for proxy in self.proxy
                                 if not proxy.free):
                    res, etype, mon = conn.recv()
                    conn.close()
                    proxy = self.proxy[mon.workerid]
                    proxy._conn = None
                    proxy.conn  # re-open
                    proxy.free = True
                    yield res, etype, mon
        finally:
            self.exit()


if __name__ == '__main__':
    wid, host, port, authkey = sys.argv[1:]
    Worker(int(wid), (host, int(port)), authkey.encode('utf-8')).loop()
