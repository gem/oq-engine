# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
The following tasks are defined in the hazard engine:
    * generate_erf
    * compute_hazard_curve
    * compute_mgm_intensity
"""

import json
import numpy

from celery.task.sets import subtask

from openquake import java
from openquake import job
from openquake import kvs
from openquake import logs
from openquake.hazard import classical_psha
from openquake.java import jtask as task
from openquake.job import mixins
from openquake.logs import HAZARD_LOG
from openquake.utils import config
from openquake.utils.tasks import check_job_status

LOG = logs.LOG

# NOTE: this refers to how the values are stored in KVS. In the config
# file, values are stored untransformed (i.e., the list of IMLs is
# not stored as logarithms).
IML_SCALING = {
    'PGA': numpy.log,
    'MMI': lambda iml: iml,
    'PGV': numpy.log,
    'PGD': numpy.log,
    'SA': numpy.log,
}



def preload(fn):
    """A decorator for preload steps that must run on the Jobber node"""

    def preloader(self, *args, **kwargs):
        """Validate job"""
        self.cache = java.jclass("KVS")(
                config.get("kvs", "host"),
                int(config.get("kvs", "port")))
        self.calc = java.jclass("LogicTreeProcessor")(
                self.cache, self.key)
        return fn(self, *args, **kwargs)
    return preloader


@task
def generate_erf(job_id):
    """
    Stubbed ERF generator

    Takes a job_id, returns a job_id.

    Connects to the Java HazardEngine using hazardwrapper, waits for an ERF to
    be generated, and then writes it to KVS.
    """

    # TODO(JM): implement real ERF computation

    check_job_status(job_id)
    kvs.get_client().set(kvs.tokens.erf_key(job_id),
                         json.JSONEncoder().encode([job_id]))

    return job_id


@task
def compute_ground_motion_fields(job_id, site_list, history, realization,
                                 seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a site_list
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, HazJobMixin):
        hazengine.compute_ground_motion_fields(site_list, history, realization,
                                               seed)


@task
def compute_hazard_curve(job_id, site_list, realization, callback=None):
    """ Generate hazard curve for a given site list. """
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, HazJobMixin):
        keys = hazengine.compute_hazard_curve(site_list, realization)

        if callback:
            subtask(callback).delay(job_id, site_list)

        return keys


@task
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    check_job_status(job_id)
    kvs_client = kvs.get_client()

    mgm_key = kvs.tokens.mgm_key(job_id, block_id, site_id)
    mgm = kvs_client.get(mgm_key)

    if not mgm:
        # TODO(jm): implement hazardwrapper and make this work.
        # TODO(chris): uncomment below when hazardwapper is done

        # Synchronous execution.
        #result = hazardwrapper.apply(args=[job_id, block_id, site_id])
        #mgm = kvs_client.get(mgm_key)
        pass

    return json.JSONDecoder().decode(mgm)


@task
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing MEAN curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
        realizations)


@task
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing QUANTILE curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_quantile_hazard_curves(job_id, sites,
        realizations, quantiles)


class BasePSHAMixin(mixins.Mixin):
    """Contains common functionality for PSHA Mixins."""

    def store_source_model(self, seed):
        """Generates an Earthquake Rupture Forecast, using the source zones and
        logic trees specified in the job config file. Note that this has to be
        done currently using the file itself, since it has nested references to
        other files."""

        LOG.info("Storing source model from job config")
        key = kvs.tokens.source_model_key(self.job_id)
        print "source model key is", key
        jpype = java.jvm()
        try:
            self.calc.sampleAndSaveERFTree(self.cache, key, seed)
        except jpype.JavaException, ex:
            unwrap_validation_error(
                jpype, ex,
                self.params.get("SOURCE_MODEL_LOGIC_TREE_FILE"))

    def store_gmpe_map(self, seed):
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file."""
        key = kvs.tokens.gmpe_key(self.job_id)
        print "GMPE map key is", key
        jpype = java.jvm()
        try:
            self.calc.sampleAndSaveGMPETree(self.cache, key, seed)
        except jpype.JavaException, ex:
            unwrap_validation_error(
                jpype, ex, self.params.get("GMPE_LOGIC_TREE_FILE"))

    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        key = kvs.tokens.source_model_key(self.job_id)
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
        key = kvs.tokens.gmpe_key(self.job_id)
        gmpe_map = java.jclass(
            "JsonSerializer").getGmpeMapFromCache(self.cache, key)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map

    def get_iml_list(self):
        """Build the appropriate Arbitrary Discretized Func from the IMLs,
        based on the IMT"""

        iml_list = java.jclass("ArrayList")()
        for val in self.imls:
            iml_list.add(
                IML_SCALING[self.params['INTENSITY_MEASURE_TYPE']](
                val))
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

            depth1km = java.jclass("DoubleParameter")(jpype.JString(
                "Depth 1.0 km/sec"))
            depth1km.setValue(float(self.params['DEPTHTO1PT0KMPERSEC']))
            vs30_type = java.jclass("StringParameter")("Vs30 Type")
            # Enum values must be capitalized in the Java domain!
            vs30_type.setValue(self.params['VS30_TYPE'].capitalize())

            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            site.addParameter(depth1km)
            site.addParameter(vs30_type)
            jsite_list.add(site)
        return jsite_list


class HazJobMixin(mixins.Mixin):
    """ Proxy mixin for mixing in hazard job behaviour """
    mixins = {}


mixins.Mixin.register("Hazard", HazJobMixin, order=1)
