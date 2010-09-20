# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import tpool

# TODO Does still make sense to use eventlet here?
class FileWriter(object):
    """Base class for objects that are capable of writing results."""
    
    def __init__(self, path):
        self.finished = event.Event()
        self.path = path
        self._init_file()

    def _init_file(self):
        """Initializes the file."""

        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, "w"))

    def write(self, point, value):
        """Writes a single value.
        
        Subclasses have to implement this method with their own
        writing logic.
        
        """

        raise NotImplementedError

    def close(self):
        """Closes the file."""
        
        self.file.close()
        self.finished.send(True)

    def serialize(self, iterable):
        """Writes all the elements passed and closes the stream."""
        
        for key, val in iterable.items():
            self.write(key, val)

        self.close()
