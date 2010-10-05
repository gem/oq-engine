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

class AttributeConstraint(object):
    """A constraint that can be used to filter input elements based on some
    attributes.
    
    The constructor requires a dictionary as argument. Items in this dictionary
    have to match the corresponding ones in the checked site attributes object.
    
    """

    def __init__(self, attribute):
        self.attribute = attribute

    def match(self, compared_attribute):
        for k, v in self.attribute.items():
            if not ( k in compared_attribute and compared_attribute[k] == v ):
                return False
        
        return True

class FileProducer(object):
    """
    FileProducer is an interface for iteratively parsing
    a file, and returning a sequence of objects.
    
    TODO(jmc): fold the attributes filter in here somewhere.
    TODO(jmc): do we really need to be using eventlet here?
    """

    # required attributes for metadata parsing
    REQUIRED_ATTRIBUTES = ()

    # optional attributes for metadata parsing
    OPTIONAL_ATTRIBUTES = ()

    def __init__(self, path):
        logs.LOG.debug('Found data at %s', path)
        self.finished = event.Event()
        self.path = path

        # file i/o will tend to block, wrap it in a thread so it will
        # play nice with ohters
        self.file = tpool.Proxy(open(self.path, 'r'))

        # contains the metadata of the node currently parsed
        self._current_meta = {}

    def __iter__(self):
        try:
            for rv in self._parse():
                yield rv
        except Exception, e:
            self.finished.send_exception(e)
            raise

        self.finished.send(True)

    def filter(self, region_constraint=None, attribute_constraint=None):
        """Filters the elements readed by this producer.
        
        region_constraint has to be of type shapes.RegionConstraint and
        specifies the region to which the elements of this producer
        should be contained.
        
        attribute_constraint has to be of type producer.AttributeConstraint
        and specifies additional attributes to use in the filtring process.

        """
        for next_val in iter(self):
            if (attribute_constraint is not None and
                    (region_constraint is None 
                        or region_constraint.match(next_val[0])) and
                    attribute_constraint.match(next_val[1])) or \
               (attribute_constraint is None and
                    (region_constraint is None 
                        or region_constraint.match(next_val[0]))):
                
                yield next_val

    def _set_meta(self, element):
        """Sets the metadata of the node that is currently
        being processed."""
        
        for (required_attr, attr_type) in self.REQUIRED_ATTRIBUTES:
            attr_value = element.get(required_attr)
            
            if attr_value is not None:
                self._current_meta[required_attr] = attr_type(attr_value)
            else:
                error_str = "element %s: missing required " \
                        "attribute %s" % (element, required_attr)
                
                raise ValueError(error_str) 

        for (optional_attr, attr_type) in self.OPTIONAL_ATTRIBUTES:
            attr_value = element.get(optional_attr)
            
            if attr_value is not None:
                self._current_meta[optional_attr] = attr_type(attr_value)

    def _parse(self):
        """Parse one logical item from the file.

        Should return a (point, data) tuple.
        
        """

        raise NotImplementedError
