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


import functools
import hashlib
import json
import math
import multiprocessing
import os
import random
import time

from itertools import izip

from celery.task import task

from openquake import job
from openquake import kvs
from openquake import java
from openquake import logs
from openquake import shapes
from openquake import xml

from openquake.hazard.general import BasePSHAMixin, preload, get_iml_list
from openquake.hazard import classical_psha
from openquake.hazard import tasks
from openquake.hazard import job as hazard_job 
from openquake.hazard.calc import CALCULATORS
from openquake.hazard.general import BasePSHAMixin, get_iml_list
from openquake.output import hazard as hazard_output
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

LOG = logs.LOG
HAZARD_LOG = logs.HAZARD_LOG

HAZARD_CURVE_FILENAME_PREFIX = 'hazardcurve'
HAZARD_MAP_FILENAME_PREFIX = 'hazardmap'


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


@task
@java.unpack_exception
def generate_erf(job_id):
    """
    Stubbed ERF generator

    Takes a job_id, returns a job_id.

    Connects to the Java HazardEngine using hazardwrapper, waits for an ERF to
    be generated, and then writes it to KVS.
    """

    # TODO(JM): implement real ERF computation

    utils_tasks.check_job_status(job_id)
    kvs.get_client().set(kvs.tokens.erf_key(job_id),
                         json.JSONEncoder().encode([job_id]))

    return job_id


@task
@java.unpack_exception
@stats.progress_indicator
def compute_ground_motion_fields(job_id, sites, history, realization, seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a sites list
    utils_tasks.check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        hazengine.compute_ground_motion_fields(sites, history, realization,
                                               seed)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_hazard_curve(job_id, sites, realization):
    """ Generate hazard curve for a given site list. """
    utils_tasks.check_job_status(job_id)
    the_job = job.Job.from_kvs(job_id)
    calc_mode = the_job['CALCULATION_MODE']
    calculator = CALCULATORS[calc_mode](the_job)
    keys = calculator.compute_hazard_curve(sites, realization)
    return keys


@task
@java.unpack_exception
@stats.progress_indicator
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    utils_tasks.check_job_status(job_id)
    kvs_client = kvs.get_client()

    mgm_key = kvs.tokens.mgm_key(job_id, block_id, site_id)
    mgm = kvs_client.get(mgm_key)

    return json.JSONDecoder().decode(mgm)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    utils_tasks.check_job_status(job_id)
    HAZARD_LOG.info("Computing MEAN curves for %s sites (job_id %s)"
                    % (len(sites), job_id))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
                                                     realizations)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    utils_tasks.check_job_status(job_id)
    HAZARD_LOG.info("Computing QUANTILE curves for %s sites (job_id %s)"
                    % (len(sites), job_id))

    return classical_psha.compute_quantile_hazard_curves(
        job_id, sites, realizations, quantiles)


def release_data_from_kvs(job_id, sites, realizations, quantiles, poes,
                          kvs_keys_purged):
    """Purge the hazard curve data for the given `sites` from the kvs.

    The parameters below will be used to construct kvs keys for
        - hazard curves (including means and quantiles)
        - hazard maps (including means)

    :param int job_id: the identifier of the job at hand
    :param list sites: the sites for which to purge content from the kvs
    :param int sites: the number of logic tree passes for this calculation
    :param list sites: the quantiles specified for this calculation
    :param list poes: the probabilities of exceedence specified for this
        calculation
    :param kvs_keys_purged: a list only passed by tests who check the
        kvs keys used/purged in the course of the calculation.
    """
    for realization in xrange(0, realizations):
        template = kvs.tokens.hazard_curve_poes_key_template(
            job_id, realization)
        keys = [template % hash(site) for site in sites]
        kvs.get_client().delete(*keys)
        if kvs_keys_purged is not None:
            kvs_keys_purged.extend(keys)

    template = kvs.tokens.mean_hazard_curve_key_template(job_id)
    keys = [template % hash(site) for site in sites]
    kvs.get_client().delete(*keys)
    if kvs_keys_purged is not None:
        kvs_keys_purged.extend(keys)

    for quantile in quantiles:
        template = kvs.tokens.quantile_hazard_curve_key_template(
            job_id, quantile)
        keys = [template % hash(site) for site in sites]
        for poe in poes:
            template = kvs.tokens.quantile_hazard_map_key_template(
                job_id, poe, quantile)
            keys.extend([template % hash(site) for site in sites])
        kvs.get_client().delete(*keys)
        if kvs_keys_purged is not None:
            kvs_keys_purged.extend(keys)

    for poe in poes:
        template = kvs.tokens.mean_hazard_map_key_template(job_id, poe)
        keys = [template % hash(site) for site in sites]
        kvs.get_client().delete(*keys)
        if kvs_keys_purged is not None:
            kvs_keys_purged.extend(keys)


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
        value = self.job_profile["HAZARD_TASKS"]
        return 2 * multiprocessing.cpu_count() if value is None else int(value)

    def do_curves(self, sites, realizations, serializer=None,
                  the_task=compute_hazard_curve):
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
            self.job_profile["SOURCE_MODEL_LT_RANDOM_SEED"])

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.job_profile["GMPE_LT_RANDOM_SEED"])

        for realization in xrange(0, realizations):
            stats.incr_counter(self.job_profile.job_id,
                               "classical:do_curves:realization")
            LOG.info("Calculating hazard curves for realization %s"
                     % realization)
            self.store_source_model(source_model_generator.getrandbits(32))
            self.store_gmpe_map(source_model_generator.getrandbits(32))

            utils_tasks.distribute(
                self.number_of_tasks(), the_task, ("sites", sites),
                dict(job_id=self.job_profile.job_id, realization=realization),
                flatten_results=True, ath=serializer)

    # pylint: disable=R0913
    def do_means(self, sites, realizations,
                 curve_serializer=None,
                 curve_task=compute_mean_curves,
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
        if not self.job_profile["COMPUTE_MEAN_HAZARD_CURVE"]:
            return

        # Compute and serialize the mean curves.
        LOG.info("Computing mean hazard curves")

        utils_tasks.distribute(
            self.number_of_tasks(), curve_task, ("sites", sites),
            dict(job_id=self.job_profile.job_id, realizations=realizations),
            flatten_results=True, ath=curve_serializer)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for mean hazard maps set"
            assert map_serializer, "No serializer for the mean hazard maps set"

            LOG.info("Computing/serializing mean hazard maps")
            map_func(self.job_profile.job_id, sites, self.job_profile.imls,
                     self.poes_hazard_maps)
            map_serializer(sites, self.poes_hazard_maps)

    # pylint: disable=R0913
    def do_quantiles(self, sites, realizations, quantiles,
                     curve_serializer=None,
                     curve_task=compute_quantile_curves,
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
            dict(job_id=self.job_profile.job_id, realizations=realizations,
                 quantiles=quantiles),
            flatten_results=True, ath=curve_serializer)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for quantile maps set."
            assert map_serializer, "No serializer for the quantile maps set."

            # quantile maps
            LOG.info("Computing quantile hazard maps")
            map_func(self.job_profile.job_id, sites, quantiles,
                     self.job_profile.imls, self.poes_hazard_maps)

            LOG.info("Serializing quantile maps for %s values"
                     % len(quantiles))
            for quantile in quantiles:
                map_serializer(sites, self.poes_hazard_maps, quantile)

    @java.unpack_exception
    @create_java_cache
    def execute(self, kvs_keys_purged=None):
        """
        Trigger the calculation and serialization of hazard curves, mean hazard
        curves/maps and quantile curves.

        :param kvs_keys_purged: a list only passed by tests who check the
            kvs keys used/purged in the course of the calculation.
        :returns: the keys used in the course of the calculation (for the sake
            of testability).
        """
        sites = self.job_profile.sites_to_compute()
        realizations = self.job_profile["NUMBER_OF_LOGIC_TREE_SAMPLES"]

        LOG.info("Going to run classical PSHA hazard for %s realizations "
                 "and %s sites" % (realizations, len(sites)))

        stats.set_total(self.job_profile.job_id, "classical:execute:sites",
                        len(sites))
        stats.set_total(
            self.job_profile.job_id, "classical:execute:realizations",
            realizations)

        block_size = config.hazard_block_size()
        for start in xrange(0, len(sites), block_size):
            end = start + block_size

            data = sites[start:end]

            self.do_curves(data, realizations,
                serializer=self.serialize_hazard_curve_of_realization)

            # mean curves
            self.do_means(data, realizations,
                curve_serializer=self.serialize_mean_hazard_curves,
                map_func=classical_psha.compute_mean_hazard_maps,
                map_serializer=self.serialize_mean_hazard_map)

            # quantile curves
            quantiles = self.quantile_levels
            self.do_quantiles(data, realizations, quantiles,
                curve_serializer=self.serialize_quantile_hazard_curves,
                map_func=classical_psha.compute_quantile_hazard_maps,
                map_serializer=self.serialize_quantile_hazard_map)

            # Done with this chunk, purge intermediate results from kvs.
            release_data_from_kvs(self.job_profile.job_id, data, realizations,
                                  quantiles, self.poes_hazard_maps,
                                  kvs_keys_purged)

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
        key_template = kvs.tokens.hazard_curve_poes_key_template(
            self.job_profile.job_id, realization)
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
        key_template = kvs.tokens.mean_hazard_curve_key_template(
            self.job_profile.job_id)
        self.serialize_hazard_curve(nrml_file, key_template, hc_attrib_update,
                                    sites)

    def serialize_quantile_hazard_curves(self, sites, quantiles):
        """
        Serialize the quantile hazard curves of a set of sites for a given
        quantile.

        :param sites: the sites of which the curves will be serialized
        :type sites: list of :py:class:`openquake.shapes.Site`
        :param quantile: the quantile to be serialized
        :type quantile: :py:class:`float`
        """
        for quantile in quantiles:
            hc_attrib_update = {
                'statistics': 'quantile',
                'quantileValue': quantile}
            nrml_file = self.quantile_hazard_curve_filename(quantile)
            key_template = kvs.tokens.quantile_hazard_curve_key_template(
                self.job_profile.job_id, str(quantile))
            self.serialize_hazard_curve(nrml_file, key_template,
                                        hc_attrib_update, sites)

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

        def duration_generator(value):
            """
            Returns the initial value when called for the first time and
            the double value upon each subsequent invocation.

            N.B.: the maximum value returned will never exceed 90 (seconds).
            """
            yield value
            while True:
                if value < 45:
                    value *= 2
                yield value

        nrml_path = self.job_profile.build_nrml_path(nrml_file)

        curve_writer = hazard_output.create_hazardcurve_writer(
            self.job_profile.job_id, self.job_profile.serialize_results_to,
            nrml_path)
        hc_data = []

        sites = set(sites)
        accounted_for = set()
        dgen = duration_generator(0.1)
        duration = dgen.next()

        while accounted_for != sites:
            # Sleep a little before checking the availability of additional
            # hazard curve results.
            time.sleep(duration)
            results_found = 0
            for site in sites:
                key = key_template % hash(site)
                value = kvs.get_value_json_decoded(key)
                if value is None or site in accounted_for:
                    # The curve for this site is not ready yet. Proceed to
                    # the next.
                    continue
                # Use hazard curve ordinate values (PoE) from KVS and abscissae
                # from the IML list in config.
                hc_attrib = {
                    'investigationTimeSpan':
                        self.job_profile['INVESTIGATION_TIME'],
                    'IMLValues': self.job_profile.imls,
                    'IMT': self.job_profile['INTENSITY_MEASURE_TYPE'],
                    'PoEValues': value}
                hc_attrib.update(hc_attrib_update)
                hc_data.append((site, hc_attrib))
                accounted_for.add(site)
                results_found += 1
            if not results_found:
                # No results found, increase the sleep duration.
                duration = dgen.next()

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
            key_template = kvs.tokens.mean_hazard_map_key_template(
                self.job_profile.job_id, poe)

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
                self.job_profile.job_id, poe, quantile)

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
        nrml_path = self.job_profile.build_nrml_path(nrml_file)

        LOG.info("Generating NRML hazard map file for PoE %s, "
                 "%s nodes in hazard map: %s" % (poe, len(sites), nrml_file))

        map_writer = hazard_output.create_hazardmap_writer(
            self.job_profile.job_id, self.job_profile.serialize_results_to,
            nrml_path)
        hm_data = []

        for site in sites:
            key = key_template % hash(site)
            # use hazard map IML values from KVS
            hm_attrib = {
                'investigationTimeSpan':
                    self.job_profile['INVESTIGATION_TIME'],
                'IMT': self.job_profile['INTENSITY_MEASURE_TYPE'],
                'vs30': self.job_profile['REFERENCE_VS30_VALUE'],
                'IML': kvs.get_value_json_decoded(key),
                'poE': poe}

            hm_attrib.update(hm_attrib_update)
            hm_data.append((site, hm_attrib))

        map_writer.serialize(hm_data)

        return nrml_path

    @create_java_cache
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
                get_iml_list(
                    self.job_profile.imls,
                    self.job_profile.params['INTENSITY_MEASURE_TYPE']),
                self.job_profile['MAXIMUM_DISTANCE'])
        except jpype.JavaException, ex:
            unwrap_validation_error(jpype, ex)

        # write the poes to the KVS and return a list of the keys

        curve_keys = []
        for site, poes in izip(sites, poes_list):
            curve_key = kvs.tokens.hazard_curve_poes_key(
                self.job_profile.job_id, realization, site)

            kvs.get_client().set(curve_key, poes)

            curve_keys.append(curve_key)

        return curve_keys

    def _hazard_curve_filename(self, filename_part):
        "Helper to build the filenames of hazard curves"
        return self.job_profile.build_nrml_path('%s-%s.xml'
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
        return self.job_profile.build_nrml_path('%s-%s.xml'
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
        return self.job_profile.extract_values_from_config(
            classical_psha.QUANTILE_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)

    @property
    def poes_hazard_maps(self):
        """
        Returns the PoEs at which the hazard maps will be calculated, as
        specified in the config file of this job.
        """
        return self.job_profile.extract_values_from_config(
            classical_psha.POES_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)


class EventBasedMixin(BasePSHAMixin):
    """Probabilistic Event Based method for performing Hazard calculations.

    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.

    Note that this Mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the Job configuration file."""

    @java.unpack_exception
    @create_java_cache
    def execute(self):
        """Main hazard processing block.

        Loops through various random realizations, spawning tasks to compute
        GMFs."""
        source_model_generator = random.Random()
        source_model_generator.seed(
            self.job_profile['SOURCE_MODEL_LT_RANDOM_SEED'])

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.job_profile['GMPE_LT_RANDOM_SEED'])

        gmf_generator = random.Random()
        gmf_generator.seed(self.job_profile['GMF_RANDOM_SEED'])

        histories = self.job_profile['NUMBER_OF_SEISMICITY_HISTORIES']
        realizations = self.job_profile['NUMBER_OF_LOGIC_TREE_SAMPLES']
        LOG.info(
            "Going to run hazard for %s histories of %s realizations each."
            % (histories, realizations))

        for i in range(0, histories):
            pending_tasks = []
            for j in range(0, realizations):
                self.store_source_model(source_model_generator.getrandbits(32))
                self.store_gmpe_map(gmpe_generator.getrandbits(32))
                pending_tasks.append(
                    compute_ground_motion_fields.delay(
                        self.job_profile.job_id, self.sites_to_compute(),
                        i, j, gmf_generator.getrandbits(32)))

            for task in pending_tasks:
                task.wait()
                if task.status != 'SUCCESS':
                    raise Exception(task.result)

            for j in range(0, realizations):
                stochastic_set_key = kvs.tokens.stochastic_set_key(
                    self.job_profile.job_id, i, j)
                LOG.info("Writing output for ses %s" % stochastic_set_key)
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    self.serialize_gmf(ses)

    def serialize_gmf(self, ses):
        """
        Write each GMF to an NRML file or to DB depending on job configuration.
        """
        iml_list = self.job_profile['INTENSITY_MEASURE_LEVELS']

        LOG.debug("IML: %s" % (iml_list))
        files = []

        nrml_path = ''

        for event_set in ses:
            for rupture in ses[event_set]:

                if self.job_profile['GMF_OUTPUT']:
                    common_path = os.path.join(self.base_path,
                            self.job_profile['OUTPUT_DIR'],
                            "gmf-%s-%s" % (str(event_set.replace("!", "_")),
                                           str(rupture.replace("!", "_"))))
                    nrml_path = "%s.xml" % common_path

                gmf_writer = hazard_output.create_gmf_writer(
                    self.job_profile.job_id,
                    self.job_profile.serialize_results_to,
                    nrml_path)
                gmf_data = {}
                for site_key in ses[event_set][rupture]:
                    site = ses[event_set][rupture][site_key]
                    site_obj = shapes.Site(site['lon'], site['lat'])
                    gmf_data[site_obj] = \
                        {'groundMotion': math.exp(float(site['mag']))}

                gmf_writer.serialize(gmf_data)
                files.append(nrml_path)
        return files

    @create_java_cache
    def compute_ground_motion_fields(self, site_list, history, realization,
                                     seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.tokens.stochastic_set_key(self.job_profile.job_id, history,
                                            realization)
        correlate = self.job_profile['GROUND_MOTION_CORRELATION']
        stochastic_set_id = "%s!%s" % (history, realization)
        java.jclass("HazardCalculator").generateAndSaveGMFs(
                self.cache, key, stochastic_set_id, jsite_list,
                self.generate_erf(),
                self.generate_gmpe_map(),
                java.jclass("Random")(seed),
                jpype.JBoolean(correlate))


hazard_job.HazJobMixin.register("Event Based", EventBasedMixin)
hazard_job.HazJobMixin.register("Event Based BCR", EventBasedMixin)
hazard_job.HazJobMixin.register("Classical", ClassicalMixin)
hazard_job.HazJobMixin.register("Classical BCR", ClassicalMixin)
