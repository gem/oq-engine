"""
Top-level managers for hazard computation.
"""

import os

from opengem import java
from opengem import settings
from opengem import config
from opengem.logs import LOG

JAVA_CLASSES = {
    'HazardEngineClass' : "org.gem.engine.CommandLineCalculator",
    'KVS' : "org.gem.engine.hazard.memcached.Cache",
    'HazardUtil' : "org.gem.engine.hazard.Util",
}

def jclass(class_key):
    jpype = java.jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


class HazardJobMixin(object):

    def __init__(self, job_file):

    def preload(self, fn):
        def mc_preloader(self, *args, **kwargs):
            assert(self.base_path)
            # Slurp related files here...
            erf_logic_tree_file = guarantee_file(self.base_path, 
                        self.params['ERF_LOGIC_TREE_FILE'])
            self.store_source_model(erf_logic_tree_file)
            fn(*args, **kwargs)
        
        if self.params['CALCULATION_MODE'].upper() == 'MONTE CARLO':
            return mc_preloader
        
        raise Exception("Can only handle Monte Carlo Hazard mode right now.")

    def store_source_model(self, tree_file):
        """Generates an Earthquake Rupture Forecast, using the source zones and
        logic trees specified in the job config file. Note that this has to be
        done using the file itself, since it has nested references to other files.
    
        job_file should be an absolute path.
        """
        engine = jclass("HazardEngineClass")(tree_file)
        source_model = engine.sampleSourceModelLogicTree()
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        util = jclass("HazardUtil")()
        util.serializeSources(cache, source_model)


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)


# engine = HazardEngineClass(cache, my_job.key)
# engine.doCalculation()