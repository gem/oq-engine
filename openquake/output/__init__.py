"""
Constants and helper functions for the output generation.
Includes simple serializers for test harnesses."""

from openquake import writer

class SimpleOutput(writer.FileWriter):
    """Fake output class that writes to stdout."""
    
    def _init_file(self):
        pass
    
    def close(self):
        pass
    
    def write(self, cell, value):
        print "%s : %s" % (cell, value)
    
    def serialize(self, someiterable):
        """Dump all the values of a given iterable"""
        for somekey, somevalue in someiterable.items():
            print "%s : %s" % (somekey, somevalue)