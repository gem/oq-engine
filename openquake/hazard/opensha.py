# -*- coding: utf-8 -*-

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
Wrapper around the OpenSHA-lite java library.
"""

import math
import os
import multiprocessing
import numpy
import random

from itertools import izip

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake import xml

from openquake.hazard import classical_psha
from openquake.hazard import job
from openquake.hazard import tasks
from openquake.job.mixins import Mixin
from openquake.output import hazard as hazard_output
from openquake.utils import config
from openquake.utils import tasks as utils_tasks

LOG = logs.LOG

# NOTE: this refers to how the values are stored in KVS. In the config
# file, values are stored untransformed (i.e., the list of IMLs is
# not stored as logarithms).
IML_SCALING = {'PGA': numpy.log,
               'MMI': lambda iml: iml,
               'PGV': numpy.log,
               'PGD': numpy.log,
               'SA': numpy.log,
              }

HAZARD_CURVE_FILENAME_PREFIX = 'hazardcurve'
HAZARD_MAP_FILENAME_PREFIX = 'hazardmap'


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


def unwrap_validation_error(jpype, runtime_exception, path=None):
    """Unwraps the nested exception of a runtime exception.  Throws
    either a XMLValidationError or the original Java exception"""
    ex = runtime_exception.__javaobject__

    if type(ex) is jpype.JPackage('org').gem.engine.XMLValidationError:
        raise xml.XMLValidationError(ex.getCause().getMessage(),
                                     path or ex.getFileName())

    if type(ex) is jpype.JPackage('org').gem.engine.XMLMismatchError:
        raise xml.XMLMismatchError(path or ex.getFileName(), ex.getActualTag(),
                                   ex.getExpectedTag())

    if ex.getCause() and type(ex.getCause()) is \
            jpype.JPackage('org').dom4j.DocumentException:
        raise xml.XMLValidationError(ex.getCause().getMessage(), path)

    raise runtime_exception


class BasePSHAMixin(Mixin):
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
                self.params.get("SOURCE_MODEL_LOGIC_TREE_FILE_PATH"))

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
                jpype, ex, self.params.get("GMPE_LOGIC_TREE_FILE_PATH"))

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
            site.addParameter(vs30)
            site.addParameter(depth25)
            site.addParameter(sadigh)
            jsite_list.add(site)
        return jsite_list


# pylint: disable=R0904
class ClassicalMixin(BasePSHAMixin):
    """Classical PSHA method for performing Hazard calculations.

    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.

    Note that this Mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the Job configuration file."""

    def number_of_tasks(self):
        """How many `celery` tasks should be used for the calculations?"""
        value = self.params.get("HAZARD_TASKS")
        value = value.strip() if value else None
        return 2 * multiprocessing.cpu_count() if value is None else int(value)

    def do_curves(self, sites, realizations,
                  serializer=None,
                  the_task=tasks.compute_hazard_curve):
        """Trigger the calculation of hazard curves, serialize as requested.

        The calculated curves will only be serialized if the `serializer`
        parameter is not `None`.

        :param sites: The sites for which to calculate hazard curves.
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param realizations: The number of realizations to calculate
        :type realizations: :py:class:`int`
        :param serializer: A serializer for the calculated hazard curves,
            receives the KVS keys of the calculated hazard curves in
            its single parameter.
        :type serializer: a callable with a single parameter: list of strings
        :param the_task: The `celery` task to use for the hazard curve
            calculation, it takes the following parameters:
                * job ID
                * the sites for which to calculate the hazard curves
                * the logic tree realization number
        :type the_task: a callable taking three parameters
        :returns: KVS keys of the calculated hazard curves.
        :rtype: list of string
        """
        source_model_generator = random.Random()
        source_model_generator.seed(
                self.params.get("SOURCE_MODEL_LT_RANDOM_SEED", None))

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.params.get("GMPE_LT_RANDOM_SEED", None))

        for realization in xrange(0, realizations):
            LOG.info("Calculating hazard curves for realization %s"
                     % realization)
            self.store_source_model(source_model_generator.getrandbits(32))
            self.store_gmpe_map(source_model_generator.getrandbits(32))

            utils_tasks.distribute(
                self.number_of_tasks(), the_task, ("site_list", sites),
                dict(job_id=self.job_id, realization=realization),
                flatten_results=True)

            if serializer:
                serializer(sites, realization)

    def param_set(self, name):
        """Is the parameter with the given `name` set and non-empty?

        :param name: The name of the parameter that should be set and
            non-empty.
        :return: `True` if the parameter in question set and non-empty, `False`
            otherwise.
        :rtype: bool
        """
        value = self.params.get(name)
        return value is not None and value.strip()

    # pylint: disable=R0913
    def do_means(self, sites, realizations,
                 curve_serializer=None,
                 curve_task=tasks.compute_mean_curves,
                 map_func=None,
                 map_serializer=None):
        """Trigger the calculation of mean curves/maps, serialize as requested.

        The calculated mean curves/maps will only be serialized if the
        corresponding `serializer` parameter was set.

        :param sites: The sites for which to calculate mean curves/maps.
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param realizations: The number of realizations that were calculated
        :type realizations: :py:class:`int`
        :param curve_serializer: A serializer for the calculated curves,
            receives the KVS keys of the calculated curves in
            its single parameter.
        :type curve_serializer: function([string])
        :param map_serializer: A serializer for the calculated maps,
            receives the KVS keys of the calculated maps in its single
            parameter.
        :type map_serializer: function([string])
        :param curve_task: The `celery` task to use for the curve calculation,
            it takes the following parameters:
                * job ID
                * the sites for which to calculate the hazard curves
        :type curve_task: function(string, [:py:class:`openquake.shapes.Site`])
        :param map_func: A function that computes mean hazard maps.
        :type map_func: function(:py:class:`openquake.job.Job`)
        :returns: `None`
        """
        if not self.param_set("COMPUTE_MEAN_HAZARD_CURVE"):
            return

        # Compute and serialize the mean curves.
        LOG.info("Computing mean hazard curves")

        utils_tasks.distribute(
            self.number_of_tasks(), curve_task, ("sites", sites),
            dict(job_id=self.job_id, realizations=realizations),
            flatten_results=True)

        if curve_serializer:
            LOG.info("Serializing mean hazard curves")

            curve_serializer(sites)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for mean hazard maps set"
            assert map_serializer, "No serializer for the mean hazard maps set"

            LOG.info("Computing/serializing mean hazard maps")
            map_func(self.job_id, sites, self.imls, self.poes_hazard_maps)
            map_serializer(sites, self.poes_hazard_maps)

    # pylint: disable=R0913
    def do_quantiles(self, sites, realizations, quantiles,
                     curve_serializer=None,
                     curve_task=tasks.compute_quantile_curves,
                     map_func=None,
                     map_serializer=None):
        """Trigger the calculation/serialization of quantile curves/maps.

        The calculated quantile curves/maps will only be serialized if the
        corresponding `serializer` parameter was set.

        :param sites: The sites for which to calculate quantile curves/maps.
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param realizations: The number of realizations that were calculated
        :type realizations: :py:class:`int`
        :param quantiles: The quantiles to calculate
        :param quantiles: list of float
        :param curve_serializer: A serializer for the calculated curves,
            receives the KVS keys of the calculated curves in
            its single parameter.
        :type curve_serializer: function([string])
        :param map_serializer: A serializer for the calculated maps,
            receives the KVS keys of the calculated maps in its single
            parameter.
        :type map_serializer: function([string])
        :param curve_task: The `celery` task to use for the curve calculation,
            it takes the following parameters:
                * job ID
                * the sites for which to calculate the hazard curves
        :type curve_task: function(string, [:py:class:`openquake.shapes.Site`])
        :param map_func: A function that computes quantile hazard maps.
        :type map_func: function(:py:class:`openquake.job.Job`)
        :returns: `None`
        """
        if not quantiles:
            return

        # compute and serialize quantile hazard curves
        LOG.info("Computing quantile hazard curves")

        utils_tasks.distribute(
            self.number_of_tasks(), curve_task, ("sites", sites),
            dict(job_id=self.job_id, realizations=realizations,
                 quantiles=quantiles),
            flatten_results=True)

        if curve_serializer:
            LOG.info("Serializing quantile curves for %s values"
                     % len(quantiles))
            for quantile in quantiles:
                curve_serializer(sites, quantile)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for quantile maps set."
            assert map_serializer, "No serializer for the quantile maps set."

            # quantile maps
            LOG.info("Computing quantile hazard maps")
            map_func(self.job_id, sites, quantiles, self.imls,
                     self.poes_hazard_maps)

            LOG.info("Serializing quantile maps for %s values"
                     % len(quantiles))
            for quantile in quantiles:
                map_serializer(sites, self.poes_hazard_maps, quantile)

    @java.jexception
    @preload
    def execute(self):
        """
        Trigger the calculation and serialization of hazard curves, mean hazard
        curves/maps and quantile curves.
        """
        sites = self.sites_to_compute()
        realizations = int(self.params["NUMBER_OF_LOGIC_TREE_SAMPLES"])

        LOG.info("Going to run classical PSHA hazard for %s realizations "
                 "and %s sites" % (realizations, len(sites)))

        self.do_curves(sites, realizations,
            serializer=self.serialize_hazard_curve_of_realization)

        # mean curves
        self.do_means(sites, realizations,
            curve_serializer=self.serialize_mean_hazard_curves,
            map_func=classical_psha.compute_mean_hazard_maps,
            map_serializer=self.serialize_mean_hazard_map)

        # quantile curves
        self.do_quantiles(sites, realizations, self.quantile_levels,
            curve_serializer=self.serialize_quantile_hazard_curves,
            map_func=classical_psha.compute_quantile_hazard_maps,
            map_serializer=self.serialize_quantile_hazard_map)

    def serialize_hazard_curve_of_realization(self, sites, realization):
        """
        Serialize the hazard curves of a set of sites for a given realization.

        :param sites: the sites of which the curves will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param realization: the realization to be serialized
        :type realization: :py:class:`int`
        """
        hc_attrib_update = {'endBranchLabel': realization}
        nrml_file = self.hazard_curve_filename(realization)
        key_template = kvs.tokens.hazard_curve_poes_key_template(self.job_id,
                                                        realization)
        self.serialize_hazard_curve(nrml_file, key_template,
                                    hc_attrib_update, sites)

    def serialize_mean_hazard_curves(self, sites):
        """
        Serialize the mean hazard curves of a set of sites.

        :param sites: the sites of which the curves will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        """
        hc_attrib_update = {'statistics': 'mean'}
        nrml_file = self.mean_hazard_curve_filename()
        key_template = kvs.tokens.mean_hazard_curve_key_template(self.job_id)
        self.serialize_hazard_curve(nrml_file, key_template, hc_attrib_update,
                                    sites)

    def serialize_quantile_hazard_curves(self, sites, quantile):
        """
        Serialize the quantile hazard curves of a set of sites for a given
        quantile.

        :param sites: the sites of which the curves will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param quantile: the quantile to be serialized
        :type quantile: :py:class:`float`
        """
        hc_attrib_update = {
            'statistics': 'quantile',
            'quantileValue': quantile}
        nrml_file = self.quantile_hazard_curve_filename(quantile)
        key_template = \
            kvs.tokens.quantile_hazard_curve_key_template(self.job_id,
                                                          str(quantile))

        self.serialize_hazard_curve(nrml_file, key_template, hc_attrib_update,
                                    sites)

    def serialize_hazard_curve(self, nrml_file, key_template, hc_attrib_update,
                               sites):
        """
        Serialize the hazard curves of a set of sites.

        Depending on the parameters the serialized curve will be a plain, mean
        or quantile hazard curve.

        :param nrml_file: the output filename
        :type nrml_file: :py:class:`string`
        :param key_template: a template for constructing the key to get, for
                             each site, its curve from the KVS
        :type key_template: :py:class:`string`
        :param hc_attrib_update: a dictionary containing metadata for the set
                                 of curves that will be serialized
        :type hc_attrib_update: :py:class:`dict`
        :param sites: the sites of which the curve will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        """
        nrml_path = self.build_nrml_path(nrml_file)

        curve_writer = hazard_output.create_hazardcurve_writer(
            self.job_id, self.serialize_results_to, nrml_path)
        hc_data = []

        for site in sites:
            # Use hazard curve ordinate values (PoE) from KVS and abscissae
            # from the IML list in config.
            hc_attrib = {
                'investigationTimeSpan': self['INVESTIGATION_TIME'],
                'IMLValues': self.imls,
                'IMT': self['INTENSITY_MEASURE_TYPE'],

                'PoEValues': kvs.get_value_json_decoded(key_template
                                                        % hash(site))}

            hc_attrib.update(hc_attrib_update)
            hc_data.append((site, hc_attrib))

        curve_writer.serialize(hc_data)

        return nrml_path

    def serialize_mean_hazard_map(self, sites, poes):
        """
        Serialize the mean hazard map for a set of sites, one map for each
        given PoE.

        :param sites: the sites of which the map will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param poes: the PoEs at which the map will be serialized
        :type poes: list of :py:class:`float`
        """
        for poe in poes:
            nrml_file = self.mean_hazard_map_filename(poe)

            hm_attrib_update = {'statistics': 'mean'}
            key_template = kvs.tokens.mean_hazard_map_key_template(self.job_id,
                                                          poe)

            self.serialize_hazard_map_at_poe(sites, poe, key_template,
                                             hm_attrib_update, nrml_file)

    def serialize_quantile_hazard_map(self, sites, poes, quantile):
        """
        Serialize the quantile hazard map for a set of sites, one map for each
        given PoE and quantile.

        :param sites: the sites of which the map will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param poes: the PoEs at which the maps will be serialized
        :type poes: list of :py:class:`float`
        :param quantile: the quantile at which the maps will be serialized
        :type quantile: :py:class:`float`
        """
        for poe in poes:
            nrml_file = self.quantile_hazard_map_filename(quantile, poe)

            key_template = kvs.tokens.quantile_hazard_map_key_template(
                                             self.job_id, poe, quantile)

            hm_attrib_update = {'statistics': 'quantile',
                                'quantileValue': quantile}

            self.serialize_hazard_map_at_poe(sites, poe, key_template,
                                             hm_attrib_update, nrml_file)

    def serialize_hazard_map_at_poe(self, sites, poe, key_template,
                                    hm_attrib_update, nrml_file):
        """
        Serialize the hazard map for a set of sites at a given PoE.

        Depending on the parameters the serialized map will be a mean or
        quantile hazard map.

        :param sites: the sites of which the map will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param poe: the PoE at which the map will be serialized
        :type poe: :py:class:`float`
        :param key_template: a template for constructing the key used to get,
                             for each site, its map from the KVS
        :type key_template: :py:class:`string`
        :param hc_attrib_update: a dictionary containing metadata for the set
                                 of maps that will be serialized
        :type hc_attrib_update: :py:class:`dict`
        :param nrml_file: the output filename
        :type nrml_file: :py:class:`string`
        """
        nrml_path = self.build_nrml_path(nrml_file)

        LOG.debug("Generating NRML hazard map file for PoE %s, "\
            "%s nodes in hazard map: %s" % (
            poe, len(sites), nrml_file))

        map_writer = hazard_output.create_hazardmap_writer(
            self.job_id, self.serialize_results_to, nrml_path)
        hm_data = []

        for site in sites:
            # use hazard map IML values from KVS
            hm_attrib = {
                'investigationTimeSpan': self.params['INVESTIGATION_TIME'],
                'IMT': self.params['INTENSITY_MEASURE_TYPE'],
                'vs30': self.params['REFERENCE_VS30_VALUE'],
                'IML': kvs.get_value_json_decoded(key_template % hash(site)),
                'poE': poe}

            hm_attrib.update(hm_attrib_update)
            hm_data.append((site, hm_attrib))

        map_writer.serialize(hm_data)

        return nrml_path

    @preload
    def compute_hazard_curve(self, sites, realization):
        """ Compute hazard curves, write them to KVS as JSON,
        and return a list of the KVS keys for each curve. """
        jpype = java.jvm()
        try:
            calc = java.jclass("HazardCalculator")
            poes_list = calc.getHazardCurvesAsJson(
                self.parameterize_sites(sites),
                self.generate_erf(),
                self.generate_gmpe_map(),
                self.get_iml_list(),
                float(self.params['MAXIMUM_DISTANCE']))
        except jpype.JavaException, ex:
            unwrap_validation_error(jpype, ex)

        # write the poes to the KVS and return a list of the keys

        curve_keys = []
        for site, poes in izip(sites, poes_list):
            curve_key = kvs.tokens.hazard_curve_poes_key(
                self.job_id, realization, site)

            kvs.set(curve_key, poes)

            curve_keys.append(curve_key)

        return curve_keys

    def _hazard_curve_filename(self, filename_part):
        "Helper to build the filenames of hazard curves"
        return self.build_nrml_path('%s-%s.xml'
                                    % (HAZARD_CURVE_FILENAME_PREFIX,
                                       filename_part))

    def hazard_curve_filename(self, realization):
        """
        Build the name of a file that will contain an hazard curve for a given
        realization.
        """
        return self._hazard_curve_filename(realization)

    def mean_hazard_curve_filename(self):
        """
        Build the name of a file that will contain the mean hazard curve for
        this job.
        """
        return self._hazard_curve_filename('mean')

    def quantile_hazard_curve_filename(self, quantile):
        """
        Build the name of a file that will contain the quantile hazard curve
        for this job and the given quantile.
        """
        return self._hazard_curve_filename('quantile-%.2f' % quantile)

    def _hazard_map_filename(self, filename_part):
        "Helper to build the filenames of hazard maps"
        return self.build_nrml_path('%s-%s.xml'
                                    % (HAZARD_MAP_FILENAME_PREFIX,
                                       filename_part))

    def mean_hazard_map_filename(self, poe):
        """
        Build the name of a file that will contain the mean hazard map for this
        job and the given PoE.
        """
        return self._hazard_map_filename('%s-mean' % poe)

    def quantile_hazard_map_filename(self, quantile, poe):
        """
        Build the name of a file that will contain the quantile hazard map for
        this job and the given PoE and quantile.
        """
        return self._hazard_map_filename('%s-quantile-%.2f' % (poe, quantile))

    @property
    def quantile_levels(self):
        "Returns the quantile levels specified in the config file of this job"
        return self.extract_values_from_config(
            classical_psha.QUANTILE_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)

    @property
    def poes_hazard_maps(self):
        """
        Returns the PoEs at which the hazard maps will be calculated, as
        specified in the config file of this job.
        """
        return self.extract_values_from_config(
            classical_psha.POES_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)


class EventBasedMixin(BasePSHAMixin):
    """Probabilistic Event Based method for performing Hazard calculations.

    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.

    Note that this Mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the Job configuration file."""

    @java.jexception
    @preload
    def execute(self):
        """Main hazard processing block.

        Loops through various random realizations, spawning tasks to compute
        GMFs."""
        source_model_generator = random.Random()
        source_model_generator.seed(
                self.params.get('SOURCE_MODEL_LT_RANDOM_SEED', None))

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.params.get('GMPE_LT_RANDOM_SEED', None))

        gmf_generator = random.Random()
        gmf_generator.seed(self.params.get('GMF_RANDOM_SEED', None))

        histories = int(self.params['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])
        LOG.info(
            "Going to run hazard for %s histories of %s realizations each."
            % (histories, realizations))

        for i in range(0, histories):
            pending_tasks = []
            for j in range(0, realizations):
                self.store_source_model(source_model_generator.getrandbits(32))
                self.store_gmpe_map(gmpe_generator.getrandbits(32))
                pending_tasks.append(
                    tasks.compute_ground_motion_fields.delay(
                        self.job_id, self.sites_to_compute(),
                        i, j, gmf_generator.getrandbits(32)))

            for task in pending_tasks:
                task.wait()
                if task.status != 'SUCCESS':
                    raise Exception(task.result)

            for j in range(0, realizations):
                stochastic_set_key = kvs.tokens.stochastic_set_key(self.job_id,
                                                                   i, j)
                print "Writing output for ses %s" % stochastic_set_key
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    self.serialize_gmf(ses)

    def serialize_gmf(self, ses):
        """
        Write each GMF to an NRML file or to DB depending on job configuration.
        """
        iml_list = [float(param)
                    for param
                    in self.params['INTENSITY_MEASURE_LEVELS'].split(",")]

        LOG.debug("IML: %s" % (iml_list))
        files = []

        nrml_path = ''

        for event_set in ses:
            for rupture in ses[event_set]:

                if self.params['GMF_OUTPUT'].lower() == 'true':
                    common_path = os.path.join(self.base_path,
                            self['OUTPUT_DIR'],
                            "gmf-%s-%s" % (str(event_set.replace("!", "_")),
                                           str(rupture.replace("!", "_"))))
                    nrml_path = "%s.xml" % common_path

                gmf_writer = hazard_output.create_gmf_writer(
                    self.job_id, self.serialize_results_to, nrml_path)
                gmf_data = {}
                for site_key in ses[event_set][rupture]:
                    site = ses[event_set][rupture][site_key]
                    site_obj = shapes.Site(site['lon'], site['lat'])
                    gmf_data[site_obj] = \
                        {'groundMotion': math.exp(float(site['mag']))}

                gmf_writer.serialize(gmf_data)
                files.append(nrml_path)
        return files

    @preload
    def compute_ground_motion_fields(self, site_list, history, realization,
                                     seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.tokens.stochastic_set_key(self.job_id, history, realization)
        gmc = self.params['GROUND_MOTION_CORRELATION']
        correlate = (gmc == "true" and True or False)
        stochastic_set_id = "%s!%s" % (history, realization)
        java.jclass("HazardCalculator").generateAndSaveGMFs(
                self.cache, key, stochastic_set_id, jsite_list,
                self.generate_erf(),
                self.generate_gmpe_map(),
                java.jclass("Random")(seed),
                jpype.JBoolean(correlate))


job.HazJobMixin.register("Event Based", EventBasedMixin, order=0)
job.HazJobMixin.register("Classical", ClassicalMixin, order=1)
