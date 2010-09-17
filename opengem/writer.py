# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import tpool

class FileWriter(object):
    def __init__(self, path):
        self.finished = event.Event()
        self.path = path
        self.init_file()

    def init_file(self):
        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, 'w'))

    def write(self, cell, value):
        raise NotImplementedError

    def close(self):
        self.file.close()
        self.finished.send(True)

    def serialize(self, iterable):
        for key, val in iterable.items():
            self.write(key, val)
        self.close()