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

from django.db import transaction
from nhlib import geo as nhlib_geo
from scipy.interpolate import interp1d
from scipy.stats.mstats import mquantiles
from shapely import geometry

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


@transaction.commit_on_success(using='job_init')
def store_site_model(input_mdl, source):
    """Invoke site model parser and save the site-specified parameter data to
    the database.

    :param input_mdl:
        The `uiapi.input` record which the new `hzrdi.site_model` records
        reference. This `input` record acts as a container for the site model
        data.
    :param source:
        Filename or file-like object containing the site model XML data.
    :returns:
        `list` of :class:`openquake.db.models.SiteModel` objects. These
        represent to newly-inserted `hzrdi.site_model` records.
    ."""
    parser = nrml_parsers.SiteModelParser(source)

    sm_data = []

    for node in parser.parse():
        sm = models.SiteModel()
        sm.vs30 = node.vs30
        sm.vs30_type = node.vs30_type
        sm.z1pt0 = node.z1pt0
        sm.z2pt5 = node.z2pt5
        sm.location = node.wkt
        sm.input = input_mdl
        sm.save()
        sm_data.append(sm)

    return sm_data


def validate_site_model(sm_nodes, sites):
    """Given the geometry for a site model and the geometry of interest for the
    calculation, make sure the geometry of interest lies completely inside of
    the convex hull formed by the site model locations.

    If a site of interest lies directly on top of a vertex or edge of the site
    model area (a polygon), it is considered "inside"

    :param sm_nodes:
        Sequence of :class:`~openquake.db.models.SiteModel` objects.
    :param sites:
        Sequence of :class:`~openquake.shapes.Site` objects which represent the
        calculation points of interest.

    :raises:
        :exc:`openquake.job.config.ValidationException` if the area of
        interest (given as a collection of sites) is not entirely contained by
        the site model.
    """
    sm_mp = geometry.MultiPoint(
        [(n.location.x, n.location.y) for n in sm_nodes]
    )
    sm_poly = nhlib_geo.Polygon(
        [nhlib_geo.Point(*x) for x in sm_mp.convex_hull.exterior.coords]
    )

    interest_mesh = nhlib_geo.Mesh.from_points_list(sites)

    # "Intersects" is the correct operation (not "contains"), since we're just
    # checking a collection of points (mesh). "Contains" would tell us if the
    # points are inside the polygon, but would return `False` if a point was
    # directly on top of a polygon edge or vertex. We want these points to be
    # included.
    intersects = sm_poly.intersects(interest_mesh)

    if not intersects.all():
        raise ValidationException(
            ['Sites of interest are outside of the site model coverage area.'
             ' This configuration is invalid.']
        )


def get_site_model(job_id):
    """Get the site model :class:`~openquake.db.models.Input` record for the
    given job id.

    :param int job_id:
        ID of a job.

    :returns:
        The site model :class:`~openquake.db.models.Input` record for this job.
    :raises:
        :exc:`RuntimeError` if the job has more than 1 site model.
    """
    site_model = models.inputs4job(job_id, input_type='site_model')

    if len(site_model) == 0:
        return None
    elif len(site_model) > 1:
        # Multiple site models for 1 job are not allowed.
        raise RuntimeError("Only 1 site model per job is allowed, found %s."
                           % len(site_model))

    # There's only one site model.
    return site_model[0]


def get_closest_site_model_data(input_model, site):
    """Get the closest available site model data from the database for a given
    site model :class:`~openquake.db.models.Input` and
    :class:`~openquake.shapes.Site`.

    :param input_model:
        :class:`openquake.db.models.Input` with `input_type` of 'site_model'.
    :param site:
        :class:`openquake.shapes.Site` instance.

    :returns:
        The closest :class:`openquake.db.models.SiteModel` for the given
        ``input_model`` and ``site`` of interest.

        This function uses the PostGIS `ST_Distance_Sphere
        <http://postgis.refractions.net/docs/ST_Distance_Sphere.html>`_
        function to calculate distance.

        If there is no site model data, return `None`.
    """
    query = """
    SELECT
        hzrdi.site_model.*,
        min(ST_Distance_Sphere(location, %s))
            AS min_distance
    FROM hzrdi.site_model where input_id = %s
    GROUP BY id
    ORDER BY min_distance
    LIMIT 1;"""

    raw_query_set = models.SiteModel.objects.raw(
        query, ['SRID=4326; %s' % site.point.wkt, input_model.id]
    )

    site_model_data = list(raw_query_set)

    assert len(site_model_data) <= 1, (
        "This query should return at most 1 record.")

    if len(site_model_data) == 1:
        return site_model_data[0]
    else:
        return None


def set_java_site_parameters(jsite, sm_data):
    """Given a site model node and an OpenSHA `Site` object,
    set vs30, vs30, z2pt5, and z1pt0 parameters.

    :param jsite:
        A `org.opensha.commons.data.Site` jpype object.
    :param sm_data:
        :class:`openquake.db.models.SiteModel` instance.
    :returns:
        The ``jsite`` input object (so this function can be chained).
    """
    vs30_param = java.jclass("DoubleParameter")("Vs30")
    vs30_param.setValue(sm_data.vs30)

    vs30_type_param = java.jclass("StringParameter")("Vs30 Type")
    vs30_type_param.setValue(sm_data.vs30_type)

    z1pt0_param = java.jclass("DoubleParameter")("Depth 1.0 km/sec")
    z1pt0_param.setValue(sm_data.z1pt0)

    z2pt5_param = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
    z2pt5_param.setValue(sm_data.z2pt5)

    jsite.addParameter(vs30_param)
    jsite.addParameter(vs30_type_param)
    jsite.addParameter(z1pt0_param)
    jsite.addParameter(z2pt5_param)

    return jsite


class BaseHazardCalculator(Calculator):
    """Contains common functionality for Hazard calculators"""

    def initialize(self):
        """Read the raw site model from the database and populate the
        `uiapi.site_model`.
        """
        site_model = get_site_model(self.job_ctxt.oq_job.id)

        if site_model is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model.model_content.raw_content)
            site_model_data = store_site_model(
                site_model, StringIO.StringIO(site_model_content)
            )

            validate_site_model(
                site_model_data, self.job_ctxt.sites_to_compute()
            )

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
        """Set vs30, vs30 type, z1pt0, z2pt5, and sadigh site type parameters
        on all input sites, returning a jpype `ArrayList` of OpenSHA `Site`
        objects.

        For vs30, vs30 type, z1pt0, and z2pt5:
        These params can be defined in general for the entire calculation.
        Alternatively, the calculation can define a `SITE_MODEL`, which supply
        site-specific parameters. This method handles both cases.

        NOTE: If a `SITE_MODEL` is used, it needs to be properly stored first.
        See :function:`~openquake.calculators.hazard.general.store_site_model`.

        :param site_list:
            `list` of :class:`~openquake.shapes.Site` objects.
        :returns:
            jpype `ArrayList` of `org.opensha.commons.data.Site` objects (with
            the above parameters set).
        """
        # make sure the JVM is started
        java.jvm()

        # the return value
        jsite_list = java.jclass("ArrayList")()

        job_profile = self.job_ctxt.oq_job_profile

        # The `sadigh site type` is the same in any case
        sadigh_param = java.jclass("StringParameter")("Sadigh Site Type")
        sadigh_param.setValue(job_profile.sadigh_site_type)

        site_model = get_site_model(self.job_ctxt.oq_job.id)

        if site_model is not None:
            # set site-specific parameters:
            for site in site_list:
                jsite = site.to_java()

                sm_data = get_closest_site_model_data(site_model, site)
                set_java_site_parameters(jsite, sm_data)
                # The sadigh site type param is not site specific, but we need
                # to set it anyway.
                jsite.addParameter(sadigh_param)

                jsite_list.add(jsite)
        else:
            # use the same parameters for all sites
            vs30_param = java.jclass("DoubleParameter")("Vs30")
            vs30_param.setValue(job_profile.reference_vs30_value)

            vs30_type_param = java.jclass("StringParameter")("Vs30 Type")
            vs30_type_param.setValue(job_profile.vs30_type)

            z1pt0_param = java.jclass("DoubleParameter")("Depth 1.0 km/sec")
            z1pt0_param.setValue(job_profile.depth_to_1pt_0km_per_sec)

            z2pt5_param = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
            z2pt5_param.setValue(
                job_profile.reference_depth_to_2pt5km_per_sec_param
            )

            for site in site_list:
                jsite = site.to_java()

                jsite.addParameter(vs30_param)
                jsite.addParameter(vs30_type_param)
                jsite.addParameter(z1pt0_param)
                jsite.addParameter(z2pt5_param)
                jsite.addParameter(sadigh_param)

                jsite_list.add(jsite)

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
