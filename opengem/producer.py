# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

# TODO Does still make sense to have this code linked to eventlet?
class FileProducer(object):

    # required attributes for metadata parsing
    REQUIRED_ATTRIBUTES = ()

    # optional attributes for metadata parsing
    OPTIONAL_ATTRIBUTES = ()

    def __init__(self, path):
        logs.general_log.debug('Found data at %s', path)
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

    def filter(self, region_constraint, attribute_constraint=None):
        """Filters the elements readed by this producer.
        
        region_constraint has to be of type shapes.RegionConstraint and
        specifies the region to which the elements of this producer
        should be contained.
        
        attribute_constraint has to be of type producer.AttributeConstraint
        and specifies additional attributes to use in the filtring process.

        """
        for next in iter(self):
            if (attribute_constraint is not None and
                    region_constraint.match(next[0]) and
                    attribute_constraint.match(next[1])) or \
               (attribute_constraint is None and
                    region_constraint.match(next[0])):
                
                yield next

# TODO (ac): Document this stuff
    def _set_meta(self, element):
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

        Should return a (cell, data) tuple.
        
        """

        raise NotImplementedError
