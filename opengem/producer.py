# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Basic parser classes, these emit a series of objects
while iteratively parsing an underlying file.

TODO(jmc): merge this with the base output class, to
produce a base codec class that can serialize and deserialize
the same format.
"""

from opengem import logs

from eventlet import event
from eventlet import tpool

class FileProducer(object):
    """
    FileProducer is an interface for iteratively parsing
    a file, and returning a sequence of objects.
    
    TODO(jmc): fold the attributes filter in here somewhere.
    TODO(jmc): do we really need to be using eventlet here?
    """
    def __init__(self, path):
        
        logs.LOG.debug('Found data at %s', path)
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
        """
        Constrain the objects returned by a defined filter.
        This is typically based on either attributes, or location.
        See the RegionFilter and ExposurePortfolioConstraint for examples.
        """
        for next_item in iter(self):
            if constraint.match(next_item[0]):
                yield next_item
  
    def _parse(self):
        """Parse one logical item from the file.

        Should return a (cell, data) tuple.
        
        """

        raise NotImplementedError

