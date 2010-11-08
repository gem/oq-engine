"""
Top-level managers for hazard computation.
"""

import os

from opengem import hazard
from opengem import java
from opengem import job
from opengem.job import mixins
from opengem.hazard import job
from opengem import kvs
from opengem import settings
from opengem.logs import LOG

JAVA_CLASSES = {
    'CommandLineCalculator' : "org.gem.engine.CommandLineCalculator",
    'KVS' : "org.gem.engine.hazard.memcached.Cache",
    'JsonSerializer' : "org.gem.JsonSerializer",
    "EventSetGen" : "org.gem.calc.StochasticEventSetGenerator",
    "Random" : "java.util.Random",
    "GEM1ERF" : "org.gem.engine.hazard.GEM1ERF",
}

def jclass(class_key):
    jpype = java.jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


class MonteCarloMixin:

    def preload(fn):
        """A decorator for preload steps that must run on the Jobber"""
        def preloader(self, *args, **kwargs):
            assert(self.base_path)
            # Slurp related files here...
            # TODO(JMC): No reason to give java the whole config file
            # Just the ERF LT file should do it...
            #erf_logic_tree_file = guarantee_file(self.base_path, 
            #            self.params['ERF_LOGIC_TREE_FILE'])
            
            self.store_source_model(self.config_file)
            self.store_gmpe_map(self.config_file)
            fn(self, *args, **kwargs)
        
        return preloader
        
        raise Exception("Can only handle Monte Carlo Hazard mode right now.")

    def store_source_model(self, config_file):
        """Generates an Earthquake Rupture Forecast, using the source zones and
        logic trees specified in the job config file. Note that this has to be
        done using the file itself, since it has nested references to other files.
    
        job_file should be an absolute path.
        """
        
        jpype = java.jvm()
        
        engine = jclass("CommandLineCalculator")(config_file)
        key = kvs.generate_product_key(self.id, hazard.SOURCE_MODEL_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        engine.sampleAndSaveERFTree(cache, key)
    
    
    def store_gmpe_map(self, config_file):
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file.
        
        In the future, this file *could* be passed as a string, since it does 
        not have any included references."""
        jpype = java.jvm()  
        
        engine = jclass("CommandLineCalculator")(config_file)
        key = kvs.generate_product_key(self.id, hazard.GMPE_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        engine.sampleAndSaveGMPETree(cache, key)
            
    
    @preload
    def execute(self):
        # Chop up subregions
        # For each subregion, take a subset of the source model
        # 
        # Spawn task for subregion, sending in source-subset and 
        # GMPE subset
        pass
        
    def generate_erf(self):
        erfclass = jclass("GEM1ERF")
        
        key = kvs.generate_product_key(self.id, hazard.SOURCE_MODEL_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        sources = jclass("JsonSerializer").getSourceListFromCache(cache, key)
        
        return erfclass.getGEM1ERF(sources)
    
    def load_ruptures(self):
        
        erf = self.generate_erf()
        
        seed = 0 # TODO(JMC): Real seed please
        rn = jclass("Random")(seed)
        event_set_gen = jclass("EventSetGen")
        self.ruptures = event_set_gen.getStochasticEventSetFromPoissonianERF(
                            erf, rn)

    def compute_hazard_curve(self, site_id):
        """Actual hazard curve calculation, runs on the workers."""
        jpype = java.jvm()
        self.load_ruptures()
        
        


job.HazJobMixin.register("Monte Carlo", MonteCarloMixin)

def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)


# engine = HazardEngineClass(cache, my_job.key)
# engine.doCalculation()