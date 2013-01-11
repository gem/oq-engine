"""
Module :mod:'hmtk.seismicity.completeness.base' defines an abstract base class
for :class:'CataloguCompleteness <BaseCatalogueCompleteness>
"""
import abc

class BaseCatalogueCompleteness(object):
    '''
    Abstract base class for implementation of the completeness algorithms
    '''
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def completeness(self, catalogue, config):
        '''
        :param catalogue:
            Earthquake catalogue as instance of 
            :class: hmtk.seismicity.catalogue.Catalogue
        
        :param dict config:
            Configuration parameters of the algorithm
        '''
        return


