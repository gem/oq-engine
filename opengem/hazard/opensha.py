"""
Top-level managers for hazard computation.
"""

import os

import numpy

from opengem import hazard
from opengem import java
from opengem import job
from opengem import shapes
from opengem.job import mixins
from opengem.hazard import job
from opengem import kvs
from opengem import settings
from opengem.logs import LOG
from opengem.output import geotiff

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
    "ConfigurationConverter" : "org.apache.commons.configuration.ConfigurationConverter",
    "ArbitrarilyDiscretizedFunc" : "org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc",
    "ArrayList" : "java.util.ArrayList",
    "GmpeLogicTreeData" : "org.gem.engine.GmpeLogicTreeData",
    "AttenuationRelationship" : "org.opensha.sha.imr.AttenuationRelationship",
    "EqkRupForecastAPI" : "org.opensha.sha.earthquake.EqkRupForecastAPI",
    "DoubleParameter" : "org.opensha.commons.param.DoubleParameter",
    "StringParameter" : "org.opensha.commons.param.StringParameter",
    "ParameterAPI" : "org.opensha.commons.param.ParameterAPI",
    "DiscretizedFuncAPI" : "org.opensha.commons.data.function.DiscretizedFuncAPI",
    "ProbabilityMassFunctionCalc" : "org.gem.calc.ProbabilityMassFunctionCalc",
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
            
            # self.store_source_model(self.config_file)
            # self.store_gmpe_map(self.config_file)
            return fn(self, *args, **kwargs)
        
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
        LOG.debug("Storing source model at %s" % (key))
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        engine.sampleAndSaveERFTree(cache, key)
    
    def _get_command_line_calc(self):
        jpype = java.jvm()
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        return jclass("CommandLineCalculator")(cache, self.key)
    
    
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
        
        # TODO(JMC): Switch on calculation mode, (unless that's already been
        # determined by the mixin
        # results = {}
        histories = float(self.params['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = float(self.params['NUMBER_OF_HAZARD_CURVE_CALCULATIONS'])
        for i in range(0, histories):
            for j in range(0, realizations):
                print "Building GMF for %s/%s" % (i,j)
                self.store_source_model(self.config_file)
                self.store_gmpe_map(self.config_file)
                # TODO(JMC): Don't use the seed again each time
                # TODO(JMC): Get real site list from boundary
                
                site_list = [shapes.Site(40.0, 40.0),]
                gmfs = self.compute_ground_motion_fields(site_list)
                rupture_ids = ["%s" % x for x in range(0, gmfs.keySet().size())]
                site_ids = ["%s" % x for x in range(0, len(site_list))]
                gmf_id = "%s!%s" % (i, j)
                key = "%s!GMF!%s" % (self.key, gmf_id)
                cache = jclass("KVS")(
                    settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
                jclass("CommandLineCalculator").gmfToMemcache(
                    cache, key, gmf_id, rupture_ids, site_ids, gmfs)
        
            # TODO(JMC): Wait here for the results to be computed
            # if self.params['OUTPUT_GMF_FILES']
            for j in range(0, realizations):
                gmf_id = "%s!%s" % (i, j)
                gmf_key = "%s!GMF!%s" % (self.key, gmf_id)
                print gmf_key
                print kvs.get_client().get(gmf_key)
                gmf = kvs.get_value_json_decoded(gmf_key)
                print gmf
                if gmf:
                    self.write_gmf_file(gmf)
                # results['history%s' % i]['realization%s' %j] = gmf_json
        # print "Fully populated results is %s" % results
        # return results
    
    def write_gmf_file(self, gmfs):
        for gmf in gmfs:
            for rupture in gmfs[gmf]:
                # TODO(JMC): Fix rupture and gmf ids into name
                path = os.path.join(self.base_path, 
                        self.params['OUTPUT_DIR'], "gmfab.tiff") # % gmf.keys()[0].replace("!", ""))
        
                # TODO(JMC): Make this valid region
                switzerland = shapes.Region.from_coordinates(
                    [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
                image_grid = switzerland.grid
                gwriter = geotiff.GeoTiffFile(path, image_grid)
                for site_key in gmfs[gmf][rupture]:
                    site = gmfs[gmf][rupture][site_key]
                    gwriter.write((site['lon'], site['lat']), int(site['mag']*-254/10))
                gwriter.close()
        
        
    def generate_erf(self):
        jpype = java.jvm()
        erfclass = jclass("GEM1ERF")
        
        key = kvs.generate_product_key(self.id, hazard.SOURCE_MODEL_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        sources = jclass("JsonSerializer").getSourceListFromCache(cache, key)
        timespan = self.params['INVESTIGATION_TIME']
        return erfclass.getGEM1ERF(sources, jpype.JDouble(float(timespan)))

    def generate_gmpe_map(self):
        key = kvs.generate_product_key(self.id, hazard.GMPE_TOKEN)
        cache = jclass("KVS")(settings.MEMCACHED_HOST, settings.MEMCACHED_PORT)
        
        gmpe_map = jclass("JsonSerializer").getGmpeMapFromCache(cache,key)
        LOG.debug("gmpe_map: %s" % gmpe_map.__class__)
        return gmpe_map

    def set_gmpe_params(self, gmpe_map):
        jpype = java.jvm()
        
        for tect_region in gmpe_map.keySet():
            gmpe = gmpe_map.get(tect_region)
            gmpeLogicTreeData = self._get_command_line_calc().createGmpeLogicTreeData()
            gmpeLogicTreeData.setGmpeParams(self.params['COMPONENT'], 
                self.params['INTENSITY_MEASURE_TYPE'], 
                jpype.JDouble(float(self.params['PERIOD'])), 
                jpype.JDouble(float(self.params['DAMPING'])), 
                self.params['GMPE_TRUNCATION_TYPE'], 
                jpype.JDouble(float(self.params['TRUNCATION_LEVEL'])), 
                self.params['STANDARD_DEVIATION_TYPE'], 
                jpype.JDouble(float(self.params['REFERENCE_VS30_VALUE'])), 
                jpype.JObject(gmpe, jclass("AttenuationRelationship")))
            gmpe_map.put(tect_region,gmpe)
    
    # def load_ruptures(self):
    #     
    #     erf = self.generate_erf()
    #     
    #     seed = 0 # TODO(JMC): Real seed please
    #     rn = jclass("Random")(seed)
    #     event_set_gen = jclass("EventSetGen")
    #     self.ruptures = event_set_gen.getStochasticEventSetFromPoissonianERF(
    #                         erf, rn)
    
    def get_IML_list(self):
        """Build the appropriate Arbitrary Discretized Func from the IMLs,
        based on the IMT"""
        jpype = java.jvm()
        
        iml_vals = {'PGA' : numpy.log,
                    'MMI' : lambda iml: iml,
                    'PGV' : numpy.log,
                    'PGD' : numpy.log,
                    'SA' : numpy.log,
                     }
        
        iml_list = jclass("ArrayList")()
        for val in self.params['INTENSITY_MEASURE_LEVELS'].split(","):
            iml_list.add(
                iml_vals[self.params['INTENSITY_MEASURE_TYPE']](
                float(val)))
        return iml_list

    def parameterize_sites(self, site_list):
        jpype = java.jvm()
        jsite_list = jclass("ArrayList")()
        for x in site_list:
            site = x.to_java()
            
            vs30 = jclass("DoubleParameter")(jpype.JString("Vs30"))
            vs30.setValue(float(self.params['REFERENCE_VS30_VALUE']))
            depth25 = jclass("DoubleParameter")("Depth 2.5 km/sec")
            depth25.setValue(float(self.params['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM']))
            sadigh = jclass("StringParameter")("Sadigh Site Type")
            sadigh.setValue(self.params['SADIGH_SITE_TYPE'])
            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            jsite_list.add(site)
        return jsite_list

    def compute_hazard_curve(self, site_list):
        """Actual hazard curve calculation, runs on the workers.
        Takes a list of Site objects."""
        jpype = java.jvm()

        erf = self.generate_erf()
        gmpe_map = self.generate_gmpe_map()
        self.set_gmpe_params(gmpe_map)

        ## here the site list should be the one appropriate for each worker. Where do I get it?
        ch_iml = self.get_IML_list()
        integration_distance = jpype.JDouble(float(self.params['MAXIMUM_DISTANCE']))
        jsite_list = self.parameterize_sites(site_list)
        LOG.debug("jsite_list: %s" % jsite_list)
        # TODO(JMC): There's Java code for this already, sets each site to have
        # The same default parameters
        
        # hazard curves are returned as Map<Site, DiscretizedFuncAPI>
        hazardCurves = jclass("HazardCalculator").getHazardCurves(
            jsite_list, #
            erf,
            gmpe_map,
            ch_iml,
            integration_distance)

        # from hazard curves, probability mass functions are calculated
        # pmf = jclass("DiscretizedFuncAPI")
        pmf_calculator = jclass("ProbabilityMassFunctionCalc")
        for site in hazardCurves.keySet():
            pmf = pmf_calculator.getPMF(hazardCurves.get(site))
            hazardCurves.put(site,pmf)
           

    def compute_ground_motion_fields(self, site_list):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        erf = self.generate_erf()
        gmpe_map = self.generate_gmpe_map()
        self.set_gmpe_params(gmpe_map)

        jsite_list = self.parameterize_sites(site_list)

        seed = 0 # TODO(JMC): Real seed please
        rn = jclass("Random")(seed)
    
        ground_motion_fields = jclass("HazardCalculator").getGroundMotionFields(
            jsite_list, erf, gmpe_map, rn, jpype.JBoolean(False))
        return ground_motion_fields


job.HazJobMixin.register("Monte Carlo", MonteCarloMixin)


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)
