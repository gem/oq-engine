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
from openquake.job.mixins import Mixin
from openquake.kvs import tokens
from openquake.output import geotiff
from openquake.output import hazard as hazard_output
from openquake import logs

LOG = logs.LOG

# NOTE: this refers to how the values are stored in KVS. In the config
# file, values are stored untransformed (i.e., the list of IMLs is
# not stored as logarithms).
IML_SCALING = {'PGA' : numpy.log,  # pylint: disable=E1101
               'MMI' : lambda iml: iml,
               'PGV' : numpy.log, # pylint: disable=E1101
               'PGD' : numpy.log, # pylint: disable=E1101
               'SA' : numpy.log,  # pylint: disable=E1101
              }

HAZARD_CURVE_FILENAME_PREFIX = 'hazardcurve'

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
        
        iml_list = java.jclass("ArrayList")()
        for val in self.params['INTENSITY_MEASURE_LEVELS'].split(","):
            iml_list.add(
                IML_SCALING[self.params['INTENSITY_MEASURE_TYPE']](
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

        LOG.info('Going to run classical PSHA hazard for %s realizations '\
                 'and %s sites' % (realizations, total_sites))

        for realization in xrange(0, realizations):
            LOG.info('Calculating hazard curves for realization %s'
                     % realization)
            pending_tasks = []
            results_per_realization = []
            self.store_source_model(source_model_generator.getrandbits(32))
            self.store_gmpe_map(source_model_generator.getrandbits(32))
            
            for site_list in self.site_list_generator():
                pending_tasks.append(tasks.compute_hazard_curve.delay(
                        self.id, site_list, realization))

            for task in pending_tasks:
                task.wait()
                if task.status != 'SUCCESS': 
                    raise Exception(task.result)
                results_per_realization.extend(task.result)

            self.write_hazardcurve_file(results_per_realization)
            results.extend(results_per_realization)

        del results_per_realization

        # compute and serialize mean and quantile hazard curves
        pending_tasks_mean = []
        results_mean = []
        pending_tasks_quantile = []
        results_quantile = []

        LOG.info('Computing mean and quantile hazard curves')
        for site_list in self.site_list_generator():

            pending_tasks_quantile.append(tasks.compute_quantile_curves.delay(
                self.id, site_list))
            if self.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == 'true':
                pending_tasks_mean.append(tasks.compute_mean_curves.delay(
                    self.id, site_list))

        for task in pending_tasks_mean:
            task.wait()
            if task.status != 'SUCCESS': 
                raise Exception(task.result)
            results_mean.extend(task.result)

        for task in pending_tasks_quantile:
            task.wait()
            if task.status != 'SUCCESS': 
                raise Exception(task.result)
            results_quantile.extend(task.result)

        if self.params['COMPUTE_MEAN_HAZARD_CURVE'].lower() == 'true':
            LOG.info('Serializing mean hazard curves')
            self.write_hazardcurve_file(results_mean)
            del results_mean

        # collect hazard curve keys per quantile value
        quantile_values = {}
        while len(results_quantile) > 0:
            quantile_key = results_quantile.pop()
            curr_qv = tokens.quantile_value_from_hazard_curve_key(
                quantile_key)
            if curr_qv not in quantile_values:
                quantile_values[curr_qv] = []
            quantile_values[curr_qv].append(quantile_key)
                
        LOG.info('Serializing quantile hazard curves for %s quantile values' \
            % len(quantile_values))
        for key_list in quantile_values.values():
            self.write_hazardcurve_file(key_list)

        return results

    def write_hazardcurve_file(self, curve_keys):
        """Generate a NRML file with hazard curves for a collection of 
        hazard curves from KVS, identified through their KVS keys.
        
        curve_keys is a list of KVS keys of the hazard curves to be
        serialized.

        The hazard curve file can be written
        (1) for a set of hazard curves belonging to the same realization
            (= endBranchLabel) and a set of sites.
        (2) for a mean hazard curve at a set of sites
        (3) for a quantile hazard curve at a set of sites

        Mixing of these three cases is not allowed, i.e., all hazard curves
        from the set of curve_keys have to be either for the same realization,
        mean, or quantile.
        """

        # LOG.debug("KEYS (%s): %s" % (len(curve_keys), curve_keys))

        if _is_mean_hazard_curve_key(curve_keys[0]):
            hc_attrib_update = {'statistics': 'mean'}
            filename_part = 'mean'
            curve_mode = 'mean'

        elif _is_quantile_hazard_curve_key(curve_keys[0]):

            # get quantile value from KVS key
            quantile_value = tokens.quantile_value_from_hazard_curve_key(
                curve_keys[0])
            hc_attrib_update = {'statistics': 'quantile',
                                'quantileValue': quantile_value}
            filename_part = "quantile-%.2f" % quantile_value
            curve_mode = 'quantile'

        elif _is_realization_hazard_curve_key(curve_keys[0]):
            realization_reference_str = \
                tokens.realization_value_from_hazard_curve_key(curve_keys[0])
            hc_attrib_update = {'endBranchLabel': realization_reference_str}
            filename_part = realization_reference_str 
            curve_mode = 'realization'

        else:
            error_msg = "no valid hazard curve type found in KVS key"
            raise RuntimeError(error_msg)

        nrml_file = "hazardcurve-%s.xml" % filename_part

        nrml_path = os.path.join(self['BASE_PATH'], self['OUTPUT_DIR'], 
            nrml_file)
        iml_list = [float(param) 
                    for param
                    in self.params['INTENSITY_MEASURE_LEVELS'].split(",")]
        
        LOG.debug("Generating NRML hazard curve file for mode %s, "\
            "%s hazard curves: %s" % (curve_mode, len(curve_keys), nrml_file))
        LOG.debug("IML: %s" % iml_list)

        xmlwriter = hazard_output.HazardCurveXMLWriter(nrml_path)
        hc_data = []
        
        for hc_key in curve_keys:

            if curve_mode == 'mean' and not _is_mean_hazard_curve_key(hc_key):
                error_msg = "non-mean hazard curve key found in mean mode"
                raise RuntimeError(error_msg)
            
            elif curve_mode == 'quantile':
                if not _is_quantile_hazard_curve_key(hc_key):
                    error_msg = "non-quantile hazard curve key found in "\
                                "quantile mode"
                    raise RuntimeError(error_msg)

                elif tokens.quantile_value_from_hazard_curve_key(hc_key) != \
                    quantile_value:
                    error_msg = "quantile value must be the same for all "\
                                "hazard curves in an instance file"
                    raise ValueError(error_msg)

            elif curve_mode == 'realization':
                if not _is_realization_hazard_curve_key(hc_key):
                    error_msg = "non-realization hazard curve key found in "\
                                "realization mode"
                    raise RuntimeError(error_msg)
                elif tokens.realization_value_from_hazard_curve_key(
                    hc_key) != realization_reference_str:
                    error_msg = "realization value must be the same for all "\
                                "hazard curves in an instance file"
                    raise ValueError(error_msg)

            hc = kvs.get_value_json_decoded(hc_key)
            #LOG.debug("JSON HC: %s" % hc)
            
            site_obj = shapes.Site(float(hc['site_lon']), 
                                   float(hc['site_lat']))

            # extract hazard curve ordinate (PoE) from KVS
            # NOTE(fab): At the moment, the IMLs are stored along with the 
            # PoEs in KVS. However, we are using the IML list from config.
            # The IMLs from KVS are ignored. Note that IMLs from KVS are
            # in logarithmic form, but the ones from config are not.
            # The way of storing the HC data in KVS is not very
            # efficient, we should store the abscissae and ordinates
            # separately as lists and not make pairs of them
            curve_poe = []
            for curve_pair in hc['curve']:
                curve_poe.append(float(curve_pair['y']))

            hc_attrib = {'investigationTimeSpan': 
                            self.params['INVESTIGATION_TIME'],
                         'IML': iml_list,
                         'IMT': self.params['INTENSITY_MEASURE_TYPE'],
                         'poE': curve_poe}

            hc_attrib.update(hc_attrib_update)
            hc_data.append((site_obj, hc_attrib))

        xmlwriter.serialize(hc_data)
        return nrml_path

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
                    self.id, kvs.tokens.STOCHASTIC_SET_TOKEN, stochastic_set_id)
                print "Writing output for ses %s" % stochastic_set_key
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    results.extend(self.write_gmf_files(ses))
        return results
    
    def write_gmf_files(self, ses):
        """Generate a GeoTiff file and a NRML file for each GMF."""
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
                common_path = os.path.join(self.base_path, self['OUTPUT_DIR'],
                        "gmf-%s-%s" % (str(event_set.replace("!", "_")),
                                       str(rupture.replace("!", "_"))))
                tiff_path = "%s.tiff" % common_path
                nrml_path = "%s.xml" % common_path
                gwriter = geotiff.GMFGeoTiffFile(tiff_path, image_grid, 
                    init_value=0.0, normalize=True, iml_list=iml_list,
                    discrete=True)
                xmlwriter = hazard_output.GMFXMLWriter(nrml_path)
                gmf_data = {}
                for site_key in ses[event_set][rupture]:
                    site = ses[event_set][rupture][site_key]
                    site_obj = shapes.Site(site['lon'], site['lat'])
                    point = image_grid.point_at(site_obj)
                    gwriter.write((point.row, point.column), 
                        math.exp(float(site['mag'])))
                    gmf_data[site_obj] = \
                        {'groundMotion': math.exp(float(site['mag']))}

                gwriter.close()
                xmlwriter.serialize(gmf_data)
                files.append(tiff_path)
                files.append(gwriter.html_path)
                files.append(nrml_path)
        return files
        
 
    @preload
    def compute_ground_motion_fields(self, site_list, stochastic_set_id, seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.generate_product_key(
                    self.id, kvs.tokens.STOCHASTIC_SET_TOKEN, stochastic_set_id)
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

def _is_realization_hazard_curve_key(kvs_key):
    return (tokens.extract_product_type_from_kvs_key(kvs_key) == \
                tokens.HAZARD_CURVE_KEY_TOKEN)

def _is_mean_hazard_curve_key(kvs_key):
    return (tokens.extract_product_type_from_kvs_key(kvs_key) == \
                tokens.MEAN_HAZARD_CURVE_KEY_TOKEN)

def _is_quantile_hazard_curve_key(kvs_key):
    return (tokens.extract_product_type_from_kvs_key(kvs_key) == \
                tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN)

def hazard_curve_filename(filename_part):
    return "%s-%s.xml" % (HAZARD_CURVE_FILENAME_PREFIX, filename_part)

def realization_hc_filename(realization):
    return hazard_curve_filename(realization)

def mean_hc_filename():
    return hazard_curve_filename('mean')

def quantile_hc_filename(quantile_value):
    filename_part = "quantile-%.2f" % quantile_value
    return hazard_curve_filename(filename_part)

job.HazJobMixin.register("Event Based", EventBasedMixin, order=0)
job.HazJobMixin.register("Classical", ClassicalMixin, order=1)
