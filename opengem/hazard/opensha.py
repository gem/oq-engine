"""
Top-level managers for hazard computation.
"""

import os

from opengem import hazard
from opengem import java
from opengem import job
from opengem.job import mixins
from opengem import kvs
from opengem import settings
from opengem.logs import LOG

JAVA_CLASSES = {
    'InputModelData' : "org.gem.engine.InputModelData",
    'KVS' : "org.gem.engine.hazard.memcached.Cache",
    'JsonSerializer' : "org.gem.JsonSerializer",
}

def jclass(class_key):
    jpype = java.jvm()
    return jpype.JClass(JAVA_CLASSES[class_key])


class HazardJobMixin(mixins.Mixin):
    mixins = []


class MonteCarloMixin:

    def preload(fn):
        """A decorator for preload steps that must run on the Jobber"""
        def preloader(self, *args, **kwargs):
            assert(self.base_path)
            # Slurp related files here...
            erf_logic_tree_file = guarantee_file(self.base_path, 
                        self.params['ERF_LOGIC_TREE_FILE'])
            self.store_source_model(erf_logic_tree_file, 
                            self.params['WIDTH_OF_MFD_BIN'])
            fn(*args, **kwargs)
        
        return preloader
        
        raise Exception("Can only handle Monte Carlo Hazard mode right now.")

    def store_source_model(self, tree_file, delta_mfd):
        """Generates an Earthquake Rupture Forecast, using the source zones and
        logic trees specified in the job config file. Note that this has to be
        done using the file itself, since it has nested references to other files.
    
        job_file should be an absolute path.
        """
        engine = jclass("InputModelData")(tree_file, delta_mfd)
        source_model = engine.sampleSourceModelLogicTree()
        key = kvs.generate_product_key(self.id, hazard.ERF_KEY_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        jclass("JsonSerializer").serializeSourceList(cache, key, source_model)
    
    @preload
    def execute(self):
        pass

    def compute_hazard_curve(self):
        """Actual hazard curve calculation, runs on the workers."""
        pass


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)


# engine = HazardEngineClass(cache, my_job.key)
# engine.doCalculation()