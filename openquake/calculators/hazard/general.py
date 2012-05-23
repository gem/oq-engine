# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Common code for the hazard calculators."""

import functools
import hashlib
import json
import math
import numpy
import StringIO

from scipy.interpolate import interp1d
from scipy.stats.mstats import mquantiles

from openquake import java
from openquake import kvs
from openquake import shapes
from openquake.calculators.base import Calculator
from openquake.db import models
from openquake.input import logictree
from openquake.java import list_to_jdouble_array
from openquake.job.config import ValidationException
from openquake.logs import LOG
from openquake.nrml import parsers as nrml_parsers
from openquake.utils import config


QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"


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

# Module-private kvs connection cache, to be used by create_java_cache().
__KVS_CONN_CACHE = {}


def create_java_cache(fn):
    """A decorator for creating java cache object"""

    @functools.wraps(fn)
    def decorated(self, *args, **kwargs):  # pylint: disable=C0111
        kvs_data = (config.get("kvs", "host"), int(config.get("kvs", "port")))

        if kvs.cache_connections():
            key = hashlib.md5(repr(kvs_data)).hexdigest()
            if key not in __KVS_CONN_CACHE:
                __KVS_CONN_CACHE[key] = java.jclass("KVS")(*kvs_data)
            self.cache = __KVS_CONN_CACHE[key]
        else:
            self.cache = java.jclass("KVS")(*kvs_data)

        return fn(self, *args, **kwargs)

    return decorated


def get_iml_list(imls, intensity_measure_type):
    """Build the appropriate Arbitrary Discretized Func from the IMLs,
    based on the IMT"""

    return list_to_jdouble_array(
        [IML_SCALING[intensity_measure_type](x) for x in imls])


def preload(fn):
    """A decorator for preload steps that must run on the Jobber node"""

    @functools.wraps(fn)
    def preloader(self, *args, **kwargs):  # pylint: disable=C0111
        source_model_lt = self.job_ctxt.params.get(
            'SOURCE_MODEL_LOGIC_TREE_FILE_PATH')
        gmpe_lt = self.job_ctxt.params.get('GMPE_LOGIC_TREE_FILE_PATH')
        basepath = self.job_ctxt.params.get('BASE_PATH')
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
    calc.sample_and_save_source_model_logictree(
        kvs.get_client(), key, seed, mfd_bin_width)


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
    calc.sample_and_save_gmpe_logictree(kvs.get_client(), key, seed)


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


def store_site_model(input_mdl, source):
    """Invoke site model parser and save the site-specified parameter data to
    the database.

    :param input_mdl:
        The `uiapi.input` record which the new `hzrdi.site_model` records
        reference. This `input` record acts as a container for the site model
        data.
    :param source:
        Filename or file-like object containing the site model XML data.
    ."""
    parser = nrml_parsers.SiteModelParser(source)
    for node in parser.parse():
        sm = models.SiteModel()
        sm.vs30 = node.vs30
        sm.vs30_type = node.vs30_type
        sm.z1pt0 = node.z1pt0
        sm.z2pt5 = node.z2pt5
        sm.location = node.wkt
        sm.input = input_mdl
        sm.save()


def validate_site_model(sm_nodes, sites):
    """Given the geometry for a site model and the geometry of interest for the
    calculation, make sure the geometry of interest lies completely inside of
    the convex hull formed by the site model locations.

    :param sm_nodes:
        Sequence of :class:`~openquake.db.models.SiteModel` objects.
    :param sites:
        Sequence of :class:`~openquake.shapes.Site` objects which represent the
        calculation points of interest.

    :raises:
        :exception:`~openquake.job.config.ValidationException` if the area of
        interest (given as a collection of sites) is not entirely contained by
        the site model.
    """



class BaseHazardCalculator(Calculator):
    """Contains common functionality for Hazard calculators"""

    def initialize(self):
        """Read the raw site model from the database and populate the
        `uiapi.site_model`.
        """
        site_model = models.inputs4job(
            self.job_ctxt.job_id, input_type='site_model')

        if len(site_model) == 0:
            # No site model found for this job. Nothing to do here.
            return

        [site_model] = site_model  # Should only be 1 record.
        # Explicit cast to `str` here because the XML parser doesn't like
        # unicode. (More specifically, lxml doesn't like unicode.)
        site_model_content = str(site_model.model_content.raw_content)
        store_site_model(site_model, StringIO.StringIO(site_model_content))

    def pre_execute(self):
        basepath = self.job_ctxt.params.get('BASE_PATH')
        if not self.job_ctxt['CALCULATION_MODE'] in (
                'Scenario', 'Scenario Damage'):
            source_model_lt = self.job_ctxt.params.get(
                'SOURCE_MODEL_LOGIC_TREE_FILE_PATH')
            gmpe_lt = self.job_ctxt.params.get('GMPE_LOGIC_TREE_FILE_PATH')
            self.calc = logictree.LogicTreeProcessor(
                basepath, source_model_lt, gmpe_lt)

    def execute(self):
        """Calculation logic goes here; subclasses must implement this."""
        raise NotImplementedError()

    def store_source_model(self, seed):
        """Generates a source model from the source model logic tree."""
        if getattr(self, "calc", None) is None:
            self.pre_execute()
        store_source_model(self.job_ctxt.job_id, seed,
                           self.job_ctxt.params, self.calc)

    def store_gmpe_map(self, seed):
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file."""
        if getattr(self, "calc", None) is None:
            self.pre_execute()
        store_gmpe_map(self.job_ctxt.job_id, seed, self.calc)

    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        return generate_erf(self.job_ctxt.job_id, self.cache)

    def set_gmpe_params(self, gmpe_map):
        """Push parameters from configuration file into the GMPE objects"""
        set_gmpe_params(gmpe_map, self.job_ctxt.params)

    def generate_gmpe_map(self):
        """Generate the GMPE map from the stored GMPE logic tree."""
        gmpe_map = generate_gmpe_map(self.job_ctxt.job_id, self.cache)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map

    def parameterize_sites(self, site_list):
        """Convert python Sites to Java Sites, and add default parameters."""
        # TODO(JMC): There's Java code for this already, sets each site to have
        # the same default parameters

        jpype = java.jvm()
        jsite_list = java.jclass("ArrayList")()
        for x in site_list:
            site = shapes.java_site(x.longitude, x.latitude)

            vs30 = java.jclass("DoubleParameter")(jpype.JString("Vs30"))
            vs30.setValue(
                float(self.job_ctxt.params['REFERENCE_VS30_VALUE']))
            depth25 = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
            depth25.setValue(float(
                self.job_ctxt.params[
                    'REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM']))
            sadigh = java.jclass("StringParameter")("Sadigh Site Type")
            sadigh.setValue(self.job_ctxt.params['SADIGH_SITE_TYPE'])

            depth1km = java.jclass("DoubleParameter")(jpype.JString(
                "Depth 1.0 km/sec"))
            depth1km.setValue(
                float(self.job_ctxt.params['DEPTHTO1PT0KMPERSEC']))
            vs30_type = java.jclass("StringParameter")("Vs30 Type")
            # Enum values must be capitalized in the Java domain!
            vs30_type.setValue(
                self.job_ctxt.params['VS30_TYPE'].capitalize())

            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            site.addParameter(depth1km)
            site.addParameter(vs30_type)
            jsite_list.add(site)
        return jsite_list


def mget_decoded(keys):
    """
    Retrieve multiple JSON values from the KVS

    :param keys: keys to retrieve (the corresponding value must be a
        JSON string)
    :type keys: list
    :returns: one value for each key in the list
    """
    decoder = json.JSONDecoder()

    return [decoder.decode(value) for value in kvs.get_client().mget(keys)]


def compute_mean_curve(curves):
    """Compute a mean hazard curve.

    The input parameter is a list of arrays where each array
    contains just the y values of the corresponding hazard curve.
    """

    return numpy.array(curves).mean(axis=0)


def compute_quantile_curve(curves, quantile):
    """Compute a quantile hazard curve.

    The input parameter is a list of arrays where each array
    contains just the y values of the corresponding hazard curve.
    """
    result = []

    if len(numpy.array(curves).flat):
        result = mquantiles(curves, quantile, axis=0)[0]

    return result


def poes_at(job_id, site, realizations):
    """Return all the json deserialized hazard curves for
    a single site (different realizations).

    :param job_id: the id of the job.
    :type job_id: integer
    :param site: site where the curves are computed.
    :type site: :py:class:`shapes.Site` object
    :param realizations: number of realizations.
    :type realizations: integer
    :returns: the hazard curves.
    :rtype: list of :py:class:`list` of :py:class:`float`
        containing the probability of exceedence for each realization
    """
    keys = [kvs.tokens.hazard_curve_poes_key(job_id, realization, site)
                for realization in xrange(realizations)]
    # get the probablity of exceedence for each curve in the site
    return mget_decoded(keys)


def compute_mean_hazard_curves(job_id, sites, realizations):
    """Compute a mean hazard curve for each site in the list
    using as input all the pre-computed curves for different realizations."""
    keys = []
    for site in sites:
        poes = poes_at(job_id, site, realizations)

        mean_poes = compute_mean_curve(poes)

        key = kvs.tokens.mean_hazard_curve_key(job_id, site)
        keys.append(key)

        kvs.set_value_json_encoded(key, mean_poes)

    return keys


def compute_quantile_hazard_curves(job_id, sites, realizations, quantiles):
    """Compute a quantile hazard curve for each site in the list
    using as input all the pre-computed curves for different realizations.
    """

    LOG.debug("[QUANTILE_HAZARD_CURVES] List of quantiles is %s" % quantiles)

    keys = []
    for site in sites:
        poes = poes_at(job_id, site, realizations)

        for quantile in quantiles:
            quantile_poes = compute_quantile_curve(poes, quantile)

            key = kvs.tokens.quantile_hazard_curve_key(
                    job_id, site, quantile)
            keys.append(key)

            kvs.set_value_json_encoded(key, quantile_poes)

    return keys


def build_interpolator(poes, imls, site=None):
    """
    Return a function interpolating the specified points.

    :param site: the site to which the points belong (used only for debugging
                 purposes)
    :type site: :py:class:`shapes.Site` or None
    :param poes: the PoEs (abscissae)
    :type poes: list of :py:class:`float`
    :param imls: the IMLs (ordinates)
    :type imls: list of :py:class:`float`
    :return: the interpolating function
    :rtype: a function fn(poe, site=None), that given a PoE will return the IML
    """
    # In our interpolation, PoE becomes the x axis, IML the y axis, therefore
    # the arrays have to be reversed (x axis has to be monotonically
    # increasing).
    poes = numpy.array(poes)[::-1]
    imls = numpy.array(imls)[::-1]

    interpolator = interp1d(poes, numpy.log(imls), kind='linear')

    def safe_interpolator(poe):
        """
        Return the interpolated IML, limiting the value between the minimum and
        maximum IMLs of the original points describing the curve.
        """
        if poe > poes[-1]:
            LOG.debug("[HAZARD_MAP] Interpolation out of bounds for PoE %s, "\
                "using maximum PoE value pair, PoE: %s, IML: %s, at site %s"
                % (poe, poes[-1], imls[-1], site))
            return imls[-1]

        if poe < poes[0]:
            LOG.debug("[HAZARD_MAP] Interpolation out of bounds for PoE %s, "\
                "using minimum PoE value pair, PoE: %s, IML: %s, at site %s"
                % (poe, poes[0], imls[0], site))
            return imls[0]

        return math.exp(interpolator(poe))

    return safe_interpolator


def compute_quantile_hazard_maps(job_id, sites, quantiles, imls, poes):
    """Compute quantile hazard maps using as input all the
    pre computed quantile hazard curves.
    """

    LOG.debug("[QUANTILE_HAZARD_MAPS] List of POEs is %s" % poes)
    LOG.debug("[QUANTILE_HAZARD_MAPS] List of quantiles is %s" % quantiles)

    keys = []
    for quantile in quantiles:
        for site in sites:
            quantile_poes = kvs.get_value_json_decoded(
                kvs.tokens.quantile_hazard_curve_key(job_id, site, quantile))

            interpolate = build_interpolator(quantile_poes, imls, site)

            for poe in poes:
                key = kvs.tokens.quantile_hazard_map_key(
                        job_id, site, poe, quantile)
                keys.append(key)

                kvs.set_value_json_encoded(key, interpolate(poe))

    return keys


def compute_mean_hazard_maps(job_id, sites, imls, poes):
    """Compute mean hazard maps using as input all the
    pre computed mean hazard curves.
    """

    LOG.debug("[MEAN_HAZARD_MAPS] List of POEs is %s" % poes)

    keys = []
    for site in sites:
        mean_poes = kvs.get_value_json_decoded(
            kvs.tokens.mean_hazard_curve_key(job_id, site))
        interpolate = build_interpolator(mean_poes, imls, site)

        for poe in poes:
            key = kvs.tokens.mean_hazard_map_key(job_id, site, poe)
            keys.append(key)

            kvs.set_value_json_encoded(key, interpolate(poe))

    return keys
