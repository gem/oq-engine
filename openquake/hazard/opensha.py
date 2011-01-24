# -*- coding: utf-8 -*-
"""
Wrapper around the OpenSHA-lite java library.
"""

import math
import os
import random
import numpy

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import settings
from openquake import shapes

from openquake.hazard import job
from openquake.hazard import tasks
from openquake.kvs import tokens
from openquake.job.mixins import Mixin
from openquake.output import geotiff

LOG = logs.LOG

def preload(fn): # pylint: disable=E0213
    """A decorator for preload steps that must run on the Jobber node"""
    def preloader(self, *args, **kwargs):
        """Validate job"""
        self.cache = java.jclass("KVS")(
                settings.KVS_HOST, 
                settings.KVS_PORT)
        self.calc = java.jclass("LogicTreeProcessor")(
                self.cache, self.key)
        return fn(self, *args, **kwargs) # pylint: disable=E1102
    return preloader


class BasePSHAMixin(Mixin): 
    """Contains common functionality for PSHA Mixins."""

    def store_source_model(self, seed):
        """Generates an Earthquake Rupture Forecast, using the source zones and
        logic trees specified in the job config file. Note that this has to be
        done currently using the file itself, since it has nested references to
        other files."""
    
        LOG.info("Storing source model from job config")
        key = kvs.generate_product_key(self.id, kvs.tokens.SOURCE_MODEL_TOKEN)
        print "source model key is", key
        self.calc.sampleAndSaveERFTree(self.cache, key, seed)
    
    def store_gmpe_map(self, seed):    
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file."""
        key = kvs.generate_product_key(self.id, kvs.tokens.GMPE_TOKEN)
        print "GMPE map key is", key
        self.calc.sampleAndSaveGMPETree(self.cache, key, seed)

    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        key = kvs.generate_product_key(self.id, kvs.tokens.SOURCE_MODEL_TOKEN)
        sources = java.jclass("JsonSerializer").getSourceListFromCache(
                    self.cache, key)
        erf = java.jclass("GEM1ERF")(sources)
        self.calc.setGEM1ERFParams(erf)
        return erf

    def set_gmpe_params(self, gmpe_map):
        """Push parameters from configuration file into the GMPE objects"""
        jpype = java.jvm()
        gmpe_lt_data = self.calc.createGmpeLogicTreeData()
        for tect_region in gmpe_map.keySet():
            gmpe = gmpe_map.get(tect_region)
            gmpe_lt_data.setGmpeParams(self.params['COMPONENT'], 
                self.params['INTENSITY_MEASURE_TYPE'], 
                jpype.JDouble(float(self.params['PERIOD'])), 
                jpype.JDouble(float(self.params['DAMPING'])), 
                self.params['GMPE_TRUNCATION_TYPE'], 
                jpype.JDouble(float(self.params['TRUNCATION_LEVEL'])), 
                self.params['STANDARD_DEVIATION_TYPE'], 
                jpype.JDouble(float(self.params['REFERENCE_VS30_VALUE'])), 
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
            gmpe_map.put(tect_region, gmpe)


    def generate_gmpe_map(self):
        """Generate the GMPE map from the stored GMPE logic tree."""
        key = kvs.generate_product_key(self.id, kvs.tokens.GMPE_TOKEN)
        gmpe_map = java.jclass("JsonSerializer").getGmpeMapFromCache(
                                                    self.cache,key)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map
        
    def get_iml_list(self):
        """Build the appropriate Arbitrary Discretized Func from the IMLs,
        based on the IMT"""        
        iml_vals = {'PGA' : numpy.log,  # pylint: disable=E1101
                    'MMI' : lambda iml: iml,
                    'PGV' : numpy.log, # pylint: disable=E1101
                    'PGD' : numpy.log, # pylint: disable=E1101
                    'SA' : numpy.log,  # pylint: disable=E1101
                     }
        
        iml_list = java.jclass("ArrayList")()
        for val in self.params['INTENSITY_MEASURE_LEVELS'].split(","):
            iml_list.add(
                iml_vals[self.params['INTENSITY_MEASURE_TYPE']](
                float(val)))
        return iml_list

    def parameterize_sites(self, site_list):
        """Convert python Sites to Java Sites, and add default parameters."""
        # TODO(JMC): There's Java code for this already, sets each site to have
        # the same default parameters
       
        jpype = java.jvm()
        jsite_list = java.jclass("ArrayList")()
        for x in site_list:
            site = x.to_java()
            
            vs30 = java.jclass("DoubleParameter")(jpype.JString("Vs30"))
            vs30.setValue(float(self.params['REFERENCE_VS30_VALUE']))
            depth25 = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
            depth25.setValue(float(
                    self.params['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM']))
            sadigh = java.jclass("StringParameter")("Sadigh Site Type")
            sadigh.setValue(self.params['SADIGH_SITE_TYPE'])
            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            jsite_list.add(site)
        return jsite_list


class ClassicalMixin(BasePSHAMixin):
    """Classical PSHA method for performing Hazard calculations.
    
    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.

    Note that this Mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the Job configuration file."""

    @preload
    def execute(self):
       
        results = []
 
        source_model_generator = random.Random()
        source_model_generator.seed(
                self.params.get('SOURCE_MODEL_LT_RANDOM_SEED', None))

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.params.get('GMPE_LT_RANDOM_SEED', None))
        
        realizations = int(self.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])

        # tally and log the total number of sites
        # TODO (LB): with a large number of sites, this could get expensive
        # and we might want to change this
        total_sites = 0
        for site_list in self.site_list_generator():
            total_sites += len(site_list)

        LOG.info('Going to run classical PSHA hazard for \
%s realizations and %s sites'
                % (realizations, total_sites))

        for realization in range(0, realizations):
            LOG.info('Calculatiing hazard curves for realization %s'
                     % realization)
            pending_tasks = []
            self.store_source_model(source_model_generator.getrandbits(32))
            self.store_gmpe_map(source_model_generator.getrandbits(32))
            
            for site_list in self.site_list_generator():
                pending_tasks.append(tasks.compute_hazard_curve.delay(
                        self.id, site_list, realization,
                        callback=tasks.compute_mean_curves))

            for task in pending_tasks:
                task.wait()
                if task.status != 'SUCCESS': 
                    raise Exception(task.result)
                results.extend(task.result)
        return results

            
    @preload
    def compute_hazard_curve(self, site_list, realization):
        """ Compute hazard curves, write them to KVS as JSON,
        and return a list of the KVS keys for each curve. """
        jsite_list = self.parameterize_sites(site_list) 
        hazard_curves = java.jclass("HazardCalculator").getHazardCurvesAsJson(
            jsite_list,
            self.generate_erf(),
            self.generate_gmpe_map(),
            self.get_iml_list(),
            float(self.params['MAXIMUM_DISTANCE']))
        
        # write the curves to the KVS and return a list of the keys
        kvs_client = kvs.get_client()
        curve_keys = []
        for i in xrange(0, len(hazard_curves)):
            curve = hazard_curves[i]
            site = site_list[i]
            lon = site.longitude
            lat = site.latitude 
            curve_key = kvs.tokens.hazard_curve_key(self.id,
                                                    realization,
                                                    lon,
                                                    lat)
            kvs_client.set(curve_key, curve)
            curve_keys.append(curve_key)
        return curve_keys

class EventBasedMixin(BasePSHAMixin): # pylint: disable=W0232
    """Probabilistic Event Based method for performing Hazard calculations.

    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.
    
    Note that this Mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the Job configuration file."""
    

    @preload
    def execute(self):
        """Main hazard processing block.
        
        Loops through various random realizations, spawning tasks to compute
        GMFs."""
        results = []
        
        source_model_generator = random.Random()
        source_model_generator.seed(
                self.params.get('SOURCE_MODEL_LT_RANDOM_SEED', None))
        
        gmpe_generator = random.Random()
        gmpe_generator.seed(self.params.get('GMPE_LT_RANDOM_SEED', None))
        
        gmf_generator = random.Random()
        gmf_generator.seed(self.params.get('GMF_RANDOM_SEED', None))
        
        histories = int(self.params['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])
        LOG.info("Going to run hazard for %s histories of %s realizations each."
                % (histories, realizations))

        for i in range(0, histories):
            pending_tasks = []
            for j in range(0, realizations):
                self.store_source_model(source_model_generator.getrandbits(32))
                self.store_gmpe_map(gmpe_generator.getrandbits(32))
                for site_list in self.site_list_generator():
                    stochastic_set_id = "%s!%s" % (i, j)
                    # pylint: disable=E1101
                    pending_tasks.append(
                        tasks.compute_ground_motion_fields.delay(
                            self.id,
                            site_list,
                            stochastic_set_id, gmf_generator.getrandbits(32)))
        
            for task in pending_tasks:
                task.wait()
                if task.status != 'SUCCESS': 
                    raise Exception(task.result)
                    
            # if self.params['OUTPUT_GMF_FILES']
            for j in range(0, realizations):
                stochastic_set_id = "%s!%s" % (i, j)
                stochastic_set_key = kvs.generate_product_key(
                    self.id, tokens.STOCHASTIC_SET_TOKEN, stochastic_set_id)
                print "Writing output for ses %s" % stochastic_set_key
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    results.extend(self.write_gmf_files(ses))
        return results
    
    def write_gmf_files(self, ses):
        """Generate a GeoTiff file for each GMF."""
        image_grid = self.region.grid
        iml_list = [float(param) 
                    for param
                    in self.params['INTENSITY_MEASURE_LEVELS'].split(",")]

        LOG.debug("Generating GMF image, grid is %s col by %s rows" % (
                image_grid.columns, image_grid.rows))
        LOG.debug("IML: %s" % (iml_list))
        files = []
        for event_set in ses:
            for rupture in ses[event_set]:

                # NOTE(fab): we have to explicitly convert the JSON-decoded 
                # tokens from Unicode to string, otherwise the path will not
                # be accepted by the GeoTiffFile constructor
                path = os.path.join(self.base_path, self['OUTPUT_DIR'],
                        "gmf-%s-%s.tiff" % (str(event_set.replace("!", "_")),
                                            str(rupture.replace("!", "_"))))
                gwriter = geotiff.GMFGeoTiffFile(path, image_grid, 
                    init_value=0.0, normalize=True, iml_list=iml_list,
                    discrete=True)
                for site_key in ses[event_set][rupture]:
                    site = ses[event_set][rupture][site_key]
                    site_obj = shapes.Site(site['lon'], site['lat'])
                    point = image_grid.point_at(site_obj)
                    gwriter.write((point.row, point.column), 
                        math.exp(float(site['mag'])))

                gwriter.close()
                files.append(path)
                files.append(gwriter.html_path)
        return files
        
    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        key = kvs.generate_product_key(self.id, tokens.SOURCE_MODEL_TOKEN)
        sources = java.jclass("JsonSerializer").getSourceListFromCache(
                    self.cache, key)
        erf = java.jclass("GEM1ERF")(sources)
        self.calc.setGEM1ERFParams(erf)
        return erf

    def generate_gmpe_map(self):
        """Generate the GMPE map from the stored GMPE logic tree."""
        key = kvs.generate_product_key(self.id, tokens.GMPE_TOKEN)
        gmpe_map = java.jclass("JsonSerializer").getGmpeMapFromCache(
                                                    self.cache,key)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map

    def set_gmpe_params(self, gmpe_map):
        """Push parameters from configuration file into the GMPE objects"""
        jpype = java.jvm()
        gmpe_lt_data = self.calc.createGmpeLogicTreeData()
        for tect_region in gmpe_map.keySet():
            gmpe = gmpe_map.get(tect_region)
            gmpe_lt_data.setGmpeParams(self.params['COMPONENT'], 
                self.params['INTENSITY_MEASURE_TYPE'], 
                jpype.JDouble(float(self.params['PERIOD'])), 
                jpype.JDouble(float(self.params['DAMPING'])), 
                self.params['GMPE_TRUNCATION_TYPE'], 
                jpype.JDouble(float(self.params['TRUNCATION_LEVEL'])), 
                self.params['STANDARD_DEVIATION_TYPE'], 
                jpype.JDouble(float(self.params['REFERENCE_VS30_VALUE'])), 
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
            gmpe_map.put(tect_region, gmpe)
    
    # def load_ruptures(self):
    #     
    #     erf = self.generate_erf()
    #     
    #     seed = 0 # TODO(JMC): Real seed please
    #     rn = jclass("Random")(seed)
    #     event_set_gen = jclass("EventSetGen")
    #     self.ruptures = event_set_gen.getStochasticEventSetFromPoissonianERF(
    #                         erf, rn)
    
    def get_iml_list(self):
        """Build the appropriate Arbitrary Discretized Func from the IMLs,
        based on the IMT"""        
        iml_vals = {'PGA' : numpy.log,  # pylint: disable=E1101
                    'MMI' : lambda iml: iml,
                    'PGV' : numpy.log, # pylint: disable=E1101
                    'PGD' : numpy.log, # pylint: disable=E1101
                    'SA' : numpy.log,  # pylint: disable=E1101
                     }
        
        iml_list = java.jclass("ArrayList")()
        for val in self.params['INTENSITY_MEASURE_LEVELS'].split(","):
            iml_list.add(
                iml_vals[self.params['INTENSITY_MEASURE_TYPE']](
                float(val)))
        return iml_list

    def parameterize_sites(self, site_list):
        """Convert python Sites to Java Sites, and add default parameters."""
        # TODO(JMC): There's Java code for this already, sets each site to have
        # the same default parameters
        
        jpype = java.jvm()
        jsite_list = java.jclass("ArrayList")()
        for x in site_list:
            site = x.to_java()
            
            vs30 = java.jclass("DoubleParameter")(jpype.JString("Vs30"))
            vs30.setValue(float(self.params['REFERENCE_VS30_VALUE']))
            depth25 = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
            depth25.setValue(float(
                    self.params['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM']))
            sadigh = java.jclass("StringParameter")("Sadigh Site Type")
            sadigh.setValue(self.params['SADIGH_SITE_TYPE'])
            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            jsite_list.add(site)
        return jsite_list

    @preload
    def compute_hazard_curve(self, site_list):
        """Actual hazard curve calculation, runs on the workers.
        Takes a list of Site objects."""
        jsite_list = self.parameterize_sites(site_list)
        hazard_curves = java.jclass("HazardCalculator").getHazardCurves(
            jsite_list,
            self.generate_erf(),
            self.generate_gmpe_map(),
            self.get_iml_list(),
            float(self.params['MAXIMUM_DISTANCE']))

        pmf_calculator = java.jclass("ProbabilityMassFunctionCalc")
        for site in hazard_curves.keySet():
            pmf = pmf_calculator.getPMF(hazard_curves.get(site))
            hazard_curves.put(site, pmf)
        return hazard_curves

    @preload
    def compute_ground_motion_fields(self, site_list, stochastic_set_id, seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.generate_product_key(
                    self.id, tokens.STOCHASTIC_SET_TOKEN, stochastic_set_id)
        gmc = self.params['GROUND_MOTION_CORRELATION']
        correlate = (gmc == "true" and True or False)
        java.jclass("HazardCalculator").generateAndSaveGMFs(
                self.cache, key, stochastic_set_id, jsite_list,
                 self.generate_erf(), 
                self.generate_gmpe_map(), 
                java.jclass("Random")(seed), 
                jpype.JBoolean(correlate))


def gmf_id(history_idx, realization_idx, rupture_idx):
    """ Return a GMF id suitable for use as a KVS key """
    return "%s!%s!%s" % (history_idx, realization_idx, rupture_idx)


job.HazJobMixin.register("Event Based", EventBasedMixin, order=0)
job.HazJobMixin.register("Classical", ClassicalMixin, order=1)
