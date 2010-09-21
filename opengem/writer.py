# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs"""

from eventlet import event
from eventlet import tpool

class FileWriter(object):
    """Simple output half of the codec process,
    using non-blocking eventlet file i/o. (Probably overkill.)"""

    def __init__(self, path):
        self.finished = event.Event()
        self.path = path
        self.file = None
        self._init_file()

    def _init_file(self):
        """Get the file handle open for writing"""
        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, "w"))

    def write(self, point, value):
       """Write out an individual point (unimplemented)"""
       raise NotImplementedError

    def close(self):
        """Close and flush the file. Send finished messages."""
        self.file.close()
        self.finished.send(True)

    def serialize(self, iterable):
        """Wrapper for writing all items in an iterable object."""
        
        for key, val in iterable.items():
            self.write(key, val)

        self.close()
