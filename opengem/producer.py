# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import tpool

class FileProducer(object):
    def __init__(self, path):
        self.finished = event.Event()
        self.path = path

        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, 'r'))

    def __iter__(self):
        try:
            for rv in self._parse():
                yield rv
        except Exception, e:
            self.finished.send_exception(e)
            raise
        
        self.finished.send(True)

    def filter(self, constraint):
        for next in iter(self):
            if constraint.match(next):
                yield next
  
    def _parse(self):
        """Parse one logical item from the file.

        Should return a (cell, data) tuple.
        
        """
        raise NotImplemented
