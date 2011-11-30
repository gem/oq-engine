# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""Common code for the hazard calculators."""

import functools
import numpy

from openquake import java
from openquake import kvs
from openquake import logs

from openquake.input import logictree
from openquake.utils import list_to_jdouble_array

from openquake.job.mixins import Mixin


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
    'IA': numpy.log,
    'RSD': numpy.log,
}


def get_iml_list(imls, intensity_measure_type):
    """Build the appropriate Arbitrary Discretized Func from the IMLs,
    based on the IMT"""

    return list_to_jdouble_array(
        map(IML_SCALING[intensity_measure_type], imls))


def preload(fn):
    """A decorator for preload steps that must run on the Jobber node"""

    @functools.wraps(fn)
    def preloader(self, *args, **kwargs):  # pylint: disable=C0111
        source_model_lt = self.params.get('SOURCE_MODEL_LOGIC_TREE_FILE_PATH')
        gmpe_lt = self.params.get('GMPE_LOGIC_TREE_FILE_PATH')
        basepath = self.params.get('BASE_PATH')
        self.calc = logictree.LogicTreeProcessor(basepath, source_model_lt,
                                                 gmpe_lt)
        return fn(self, *args, **kwargs)
    return preloader


@java.unpack_exception
def generate_erf(job_id, cache):
    """ Generate the Earthquake Rupture Forecast from the source model data
    stored in the KVS.

    :param int job_id: id of the job
    :param cache: jpype instance of `org.gem.engine.hazard.redis.Cache`
    :returns: jpype instance of
        `org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF`
    """
    src_key = kvs.tokens.source_model_key(job_id)
    job_key = kvs.tokens.generate_job_key(job_id)

    sources = java.jclass("JsonSerializer").getSourceListFromCache(
        cache, src_key)

    erf = java.jclass("GEM1ERF")(sources)

    calc = java.jclass("LogicTreeProcessor")(cache, job_key)
    calc.setGEM1ERFParams(erf)

    return erf


def generate_gmpe_map(job_id, cache):
    """ Generate the GMPE map from the GMPE data stored in the KVS.

    :param int job_id: id of the job
    :param cache: jpype instance of `org.gem.engine.hazard.redis.Cache`
    :returns: jpype instace of
        `HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>`
    """
    gmpe_key = kvs.tokens.gmpe_key(job_id)

    gmpe_map = java.jclass(
        "JsonSerializer").getGmpeMapFromCache(cache, gmpe_key)
    return gmpe_map


def store_source_model(job_id, seed, params, calc):
    """Generate source model from the source model logic tree and store it in
    the KVS.

    :param int job_id: numeric ID of the job
    :param int seed: seed for random logic tree sampling
    :param dict params: the config parameters as (dict)
    :param calc: logic tree processor
    :type calc: :class:`openquake.input.logictree.LogicTreeProcessor` instance
    """
    LOG.info("Storing source model from job config")
    key = kvs.tokens.source_model_key(job_id)
    mfd_bin_width = float(params.get('WIDTH_OF_MFD_BIN'))
    calc.sample_and_save_source_model_logictree(kvs, key, seed, mfd_bin_width)


def store_gmpe_map(job_id, seed, calc):
    """Generate a hash map of GMPEs (keyed by Tectonic Region Type) and store
    it in the KVS.

    :param int job_id: numeric ID of the job
    :param int seed: seed for random logic tree sampling
    :param calc: logic tree processor
    :type calc: :class:`openquake.input.logictree.LogicTreeProcessor` instance
    """
    LOG.info("Storing GMPE map from job config")
    key = kvs.tokens.gmpe_key(job_id)
    calc.sample_and_save_gmpe_logictree(kvs, key, seed)


def set_gmpe_params(gmpe_map, params):
    """Push parameters from the config file into the GMPE objects.

    :param gmpe_map: jpype instance of
        `HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>`
    :param dict params: job config params
    """
    jpype = java.jvm()

    jd_float = lambda x: jpype.JDouble(float(x))

    component = params.get('COMPONENT')
    imt = params.get('INTENSITY_MEASURE_TYPE')
    # PERIOD is not used in UHS calculations.
    period = (jd_float(params.get('PERIOD'))
              if params.get('PERIOD') is not None else None)
    damping = jd_float(params.get('DAMPING'))
    gmpe_trunc_type = params.get('GMPE_TRUNCATION_TYPE')
    trunc_level = jd_float(params.get('TRUNCATION_LEVEL'))
    stddev_type = params.get('STANDARD_DEVIATION_TYPE')

    j_set_gmpe_params = java.jclass("GmpeLogicTreeData").setGmpeParams
    for tect_region in gmpe_map.keySet():
        gmpe = gmpe_map.get(tect_region)
        # There are two overloads for this method; one with 'period'...
        if period is not None:
            j_set_gmpe_params(
                component, imt, period, damping,
                gmpe_trunc_type, trunc_level, stddev_type,
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
        # ... and one without.
        else:
            j_set_gmpe_params(
                component, imt, damping,
                gmpe_trunc_type, trunc_level, stddev_type,
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
        gmpe_map.put(tect_region, gmpe)


class BasePSHAMixin(Mixin):
    """Contains common functionality for PSHA Mixins."""

    def store_source_model(self, seed):
        """Generates a source model from the source model logic tree."""
        store_source_model(self.job_id, seed, self.params, self.calc)

    def store_gmpe_map(self, seed):
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file."""
        store_gmpe_map(self.job_id, seed, self.calc)

    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        return generate_erf(self.job_id, self.cache)

    def set_gmpe_params(self, gmpe_map):
        """Push parameters from configuration file into the GMPE objects"""
        set_gmpe_params(gmpe_map, self.params)

    def generate_gmpe_map(self):
        """Generate the GMPE map from the stored GMPE logic tree."""
        gmpe_map = generate_gmpe_map(self.job_id, self.cache)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map

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
