# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import logs

from eventlet import event
from eventlet import tpool

# TODO (ac): Think about a better name to use
class AttributeConstraint(object):
    """ A constraint that can be used to filter input elements.
    
    The constructor requires a dictionary as argument. Items in this dictionary
    have to match the corresponding ones in the checked site attribute object.
    
    """

    def __init__(self, attribute):
        self.attribute = attribute

    def match(self, compared_attribute):
        for k, v in self.attribute.items():
            if not ( k in compared_attribute and compared_attribute[k] == v ):
                return False
        return True


class FileProducer(object):

    def __init__(self, path):
        logs.general_log.debug('Found data at %s', path)
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
            if constraint.match(next[0]):
                yield next
  
    def _parse(self):
        """Parse one logical item from the file.

        Should return a (cell, data) tuple.
        
        """

        raise NotImplementedError
