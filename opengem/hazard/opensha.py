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
    "HazardCalculator" : "org.gem.calc.HazardCalculator",
    "Properties" : "java.util.Properties",
    "CalculatorConfigHelper" : "org.gem.engine.CalculatorConfigHelper",
    "Configuration" : "org.apache.commons.configuration.Configuration",
    "ConfigurationConverter" : "org.apache.commons.configuration.ConfigurationConverter"
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
            self.store_config_file(self.config_file)
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

    def store_config_file(self, config_file):
        """Store configuration file to cache"""
        jpype = java.jvm()  

        engine = jclass("CommandLineCalculator")(config_file)
        # what key to use????
        key = kvs.generate_product_key(self.id, hazard.GMPE_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        jclass("JsonSerializer").serializeConfigurationFile(cache, key,
                    engine.getConfigurationProperties())
    
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

    def generate_gmpe_map(self):
        key = kvs.generate_product_key(self.id, hazard.GMPE_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        
        return jclass("JsonSerializer").getGmpeMapFromCache(cache,key);

    def generate_configuration_properties(self):
        # what key to use????
        key = kvs.generate_product_key(self.id, hazard.GMPE_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
      
        return jclass("JsonSerializer").getConfigurationPropertiesFromCache(cache,key)

    def set_gmpe_params(gmpe_map,properties):
        gmpeLogicTreeData = jClass("org.gem.engine.GmpeLogicTreeData")
        configItems = jClass("org.gem.engine.CalculatorConfigHelper.ConfigItems")
        component = configItems.COMPONENT
        intensityMeasureType = configItems.INTENSITY_MEASURE_TYPE
        period = configItems.PERIOD
        damping = configItems.DAMPING
        truncType = configItems.GMPE_TRUNCATION_TYPE
        truncLevel = configItems.TRUNCATION_LEVEL
        stdType = configItems.STANDARD_DEVIATION_TYPE
        vs30 = REFERENCE_VS30_VALUE
        for trt in gmpe_map.keySet():
            gmpe = gmpe_map.get(trt)
            gmpeLogicTreeData.setGmpeParams(component, intensityMeasureType, period, damping,
                    truncType, truncLevel, stdType, vs30, gmpe)
            gmpe_map.put(trt,gmpe)
    
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

        erf = self.generate_erf()
        gmpe_map = self.generate_gmpe_map()
        configuration_properties = generate_configuration_properties(self)
        set_gmpe_params(gmpe_map,configuration_properties)
        configuration_helper = jclass("CalculatorConfigHelper")
        configuration = jclass("ConfigurationConverter").getConfiguration(configuration_properties)

        ## here the site list should be the one appropriate for each worker. Where do I get it?
        ## this method returns a map relating sites with hazard curves (described as DiscretizedFuncAPI)

        integration_distance_key = jClass("org.gem.engine.CalculatorConfigHelper.ConfigItems").MAXIMUM_DISTANCE
        site_lits = configuration_helper.makeImlDoubleList(configuration)
        integration_distance = configuration_properties.getProperty(integration_distance_key)
        hazardCurves = jclass("HazardCalculator").getHazardCurves(site_list, 
            erf, gmpe_map, ch_iml, integration_distance)
        


job.HazJobMixin.register("Monte Carlo", MonteCarloMixin)

def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)


# engine = HazardEngineClass(cache, my_job.key)
# engine.doCalculation()