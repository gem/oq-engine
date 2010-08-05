# vim: tabstop=4 shiftwidth=4 softtabstop=4


from eventlet import event
from eventlet import tpool

class FileWriter(object):
    def __init__(self, path):
        self.finished = event.Event()
        self.path = path

        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, 'r'))

    def write(self, cell, value):
        raise NotImplemented

    def close(self):
        self.file.close()
        self.finished.send(True)
