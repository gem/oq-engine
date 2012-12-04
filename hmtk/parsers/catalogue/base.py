"""
Module :mod:`hmtk.parsers.catalogue.base` defines an abstract base class
for :class:`CatalogueParser <BaseCatalogueParser>`.
"""
import abc
import os.path

class BaseCatalogueParser(object):
    """
    A base class for a Catalogue Parser
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_file):
        """ 
        """
        self.input_file = input_file
        if not os.path.exists(self.input_file):
            raise IOError('File not found')

    @abc.abstractmethod
    def read_file(self):
        """
        Return an instance of the class :class:`Catalogue`
        """
