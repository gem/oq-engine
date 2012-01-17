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

"""Core functionality for Classical PSHA-based hazard calculations."""


import json
import multiprocessing
import random
import time

from itertools import izip

from celery.task import task

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import xml
from openquake.output import hazard as hazard_output
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks
from openquake.calculators.hazard import general

LOG = logs.LOG
HAZARD_LOG = logs.HAZARD_LOG

HAZARD_CURVE_FILENAME_PREFIX = 'hazardcurve'
HAZARD_MAP_FILENAME_PREFIX = 'hazardmap'


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


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator("h")
def compute_hazard_curve(job_id, sites, realization):
    """ Generate hazard curve for a given site list. """

    calculator = utils_tasks.calculator_for_task(job_id, 'hazard')
    keys = calculator.compute_hazard_curve(sites, realization)
    return keys


@task
@java.unpack_exception
@stats.progress_indicator("h")
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    # We don't actually need the CalculationProxy returned by this function
    # (yet) but this does check if the calculation is still in progress.
    utils_tasks.get_running_calculation(job_id)
    kvs_client = kvs.get_client()

    mgm_key = kvs.tokens.mgm_key(job_id, block_id, site_id)
    mgm = kvs_client.get(mgm_key)

    return json.JSONDecoder().decode(mgm)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator("h")
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    # We don't actually need the CalculationProxy returned by this function
    # (yet) but this does check if the calculation is still in progress.
    utils_tasks.get_running_calculation(job_id)

    HAZARD_LOG.info("Computing MEAN curves for %s sites (job_id %s)"
                    % (len(sites), job_id))

    return general.compute_mean_hazard_curves(job_id, sites, realizations)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator("h")
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    # We don't actually need the CalculationProxy returned by this function
    # (yet) but this does check if the calculation is still in progress.
    utils_tasks.get_running_calculation(job_id)

    HAZARD_LOG.info("Computing QUANTILE curves for %s sites (job_id %s)"
                    % (len(sites), job_id))

    return general.compute_quantile_hazard_curves(job_id, sites, realizations,
                                                  quantiles)


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
class ClassicalHazardCalculator(general.BaseHazardCalculator):
    """Classical PSHA method for performing Hazard calculations."""

    def number_of_tasks(self):
        """How many `celery` tasks should be used for the calculations?"""
        value = self.calc_proxy["HAZARD_TASKS"]
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
            self.calc_proxy["SOURCE_MODEL_LT_RANDOM_SEED"])

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.calc_proxy["GMPE_LT_RANDOM_SEED"])

        for realization in xrange(0, realizations):
            stats.pk_inc(self.calc_proxy.job_id, "hcls_crealization")
            LOG.info("Calculating hazard curves for realization %s"
                     % realization)
            self.store_source_model(source_model_generator.getrandbits(32))
            self.store_gmpe_map(source_model_generator.getrandbits(32))

            utils_tasks.distribute(
                self.number_of_tasks(), the_task, ("sites", sites),
                dict(job_id=self.calc_proxy.job_id, realization=realization),
                flatten_results=True, ath=serializer)

    # pylint: disable=R0913
    def do_means(self, sites, realizations,
                 curve_serializer=None,
                 curve_task=compute_mean_curves,
                 map_func=None, map_serializer=None):
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
        :type map_func: function(:py:class:`openquake.engine.CalculationProxy`)
        :returns: `None`
        """
        if not self.calc_proxy["COMPUTE_MEAN_HAZARD_CURVE"]:
            return

        # Compute and serialize the mean curves.
        LOG.info("Computing mean hazard curves")

        utils_tasks.distribute(
            self.number_of_tasks(), curve_task, ("sites", sites),
            dict(job_id=self.calc_proxy.job_id, realizations=realizations),
            flatten_results=True, ath=curve_serializer)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for mean hazard maps set"
            assert map_serializer, "No serializer for the mean hazard maps set"

            LOG.info("Computing/serializing mean hazard maps")
            map_func(self.calc_proxy.job_id, sites, self.calc_proxy.imls,
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
        :type map_func: function(:py:class:`openquake.engine.CalculationProxy`)
        :returns: `None`
        """
        if not quantiles:
            return

        # compute and serialize quantile hazard curves
        LOG.info("Computing quantile hazard curves")

        utils_tasks.distribute(
            self.number_of_tasks(), curve_task, ("sites", sites),
            dict(job_id=self.calc_proxy.job_id, realizations=realizations,
                 quantiles=quantiles),
            flatten_results=True, ath=curve_serializer)

        if self.poes_hazard_maps:
            assert map_func, "No calculation function for quantile maps set."
            assert map_serializer, "No serializer for the quantile maps set."

            # quantile maps
            LOG.info("Computing quantile hazard maps")
            map_func(self.calc_proxy.job_id, sites, quantiles,
                     self.calc_proxy.imls, self.poes_hazard_maps)

            LOG.info("Serializing quantile maps for %s values"
                     % len(quantiles))
            for quantile in quantiles:
                map_serializer(sites, self.poes_hazard_maps, quantile)

    @java.unpack_exception
    @general.create_java_cache
    def execute(self, kvs_keys_purged=None):  # pylint: disable=W0221
        """
        Trigger the calculation and serialization of hazard curves, mean hazard
        curves/maps and quantile curves.

        :param kvs_keys_purged: a list only passed by tests who check the
            kvs keys used/purged in the course of the calculation.
        :returns: the keys used in the course of the calculation (for the sake
            of testability).
        """
        sites = self.calc_proxy.sites_to_compute()
        realizations = self.calc_proxy["NUMBER_OF_LOGIC_TREE_SAMPLES"]

        LOG.info("Going to run classical PSHA hazard for %s realizations "
                 "and %s sites" % (realizations, len(sites)))

        stats.pk_set(self.calc_proxy.job_id, "hcls_sites", len(sites))
        stats.pk_set(self.calc_proxy.job_id, "hcls_realizations",
                     realizations)

        block_size = config.hazard_block_size()
        stats.pk_set(self.calc_proxy.job_id, "block_size", block_size)

        blocks = range(0, len(sites), block_size)
        stats.pk_set(self.calc_proxy.job_id, "blocks", len(blocks))

        for start in blocks:
            stats.pk_inc(self.calc_proxy.job_id, "cblock")
            end = start + block_size
            data = sites[start:end]

            self.do_curves(
                data, realizations,
                serializer=self.serialize_hazard_curve_of_realization)

            # mean curves
            self.do_means(
                data, realizations,
                curve_serializer=self.serialize_mean_hazard_curves,
                map_func=general.compute_mean_hazard_maps,
                map_serializer=self.serialize_mean_hazard_map)

            # quantile curves
            quantiles = self.quantile_levels
            self.do_quantiles(
                data, realizations, quantiles,
                curve_serializer=self.serialize_quantile_hazard_curves,
                map_func=general.compute_quantile_hazard_maps,
                map_serializer=self.serialize_quantile_hazard_map)

            # Done with this chunk, purge intermediate results from kvs.
            release_data_from_kvs(self.calc_proxy.job_id, data, realizations,
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
            self.calc_proxy.job_id, realization)
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
            self.calc_proxy.job_id)
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
                self.calc_proxy.job_id, str(quantile))
            self.serialize_hazard_curve(nrml_file, key_template,
                                        hc_attrib_update, sites)

    # Silencing 'Too many local variables'
    # pylint: disable=R0914
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

        nrml_path = self.calc_proxy.build_nrml_path(nrml_file)

        curve_writer = hazard_output.create_hazardcurve_writer(
            self.calc_proxy.job_id, self.calc_proxy.serialize_results_to,
            nrml_path)

        sites = set(sites)
        accounted_for = set()
        dgen = duration_generator(0.1)
        duration = dgen.next()

        while accounted_for != sites:
            hc_data = []
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
                        self.calc_proxy['INVESTIGATION_TIME'],
                    'IMLValues': self.calc_proxy.imls,
                    'IMT': self.calc_proxy['INTENSITY_MEASURE_TYPE'],
                    'PoEValues': value}
                hc_attrib.update(hc_attrib_update)
                hc_data.append((site, hc_attrib))
                accounted_for.add(site)
                results_found += 1
            if not results_found:
                # No results found, increase the sleep duration.
                duration = dgen.next()
            else:
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
                self.calc_proxy.job_id, poe)

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
                self.calc_proxy.job_id, poe, quantile)

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
        nrml_path = self.calc_proxy.build_nrml_path(nrml_file)

        LOG.info("Generating NRML hazard map file for PoE %s, "
                 "%s nodes in hazard map: %s" % (poe, len(sites), nrml_file))

        map_writer = hazard_output.create_hazardmap_writer(
            self.calc_proxy.job_id, self.calc_proxy.serialize_results_to,
            nrml_path)
        hm_data = []

        for site in sites:
            key = key_template % hash(site)
            # use hazard map IML values from KVS
            hm_attrib = {
                'investigationTimeSpan':
                    self.calc_proxy['INVESTIGATION_TIME'],
                'IMT': self.calc_proxy['INTENSITY_MEASURE_TYPE'],
                'vs30': self.calc_proxy['REFERENCE_VS30_VALUE'],
                'IML': kvs.get_value_json_decoded(key),
                'poE': poe}

            hm_attrib.update(hm_attrib_update)
            hm_data.append((site, hm_attrib))

        map_writer.serialize(hm_data)

        return nrml_path

    @general.create_java_cache
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
                general.get_iml_list(
                    self.calc_proxy.imls,
                    self.calc_proxy.params['INTENSITY_MEASURE_TYPE']),
                self.calc_proxy['MAXIMUM_DISTANCE'])
        except jpype.JavaException, ex:
            unwrap_validation_error(jpype, ex)

        # write the poes to the KVS and return a list of the keys

        curve_keys = []
        for site, poes in izip(sites, poes_list):
            curve_key = kvs.tokens.hazard_curve_poes_key(
                self.calc_proxy.job_id, realization, site)

            kvs.get_client().set(curve_key, poes)

            curve_keys.append(curve_key)

        return curve_keys

    def _hazard_curve_filename(self, filename_part):
        "Helper to build the filenames of hazard curves"
        return self.calc_proxy.build_nrml_path('%s-%s.xml'
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
        """Helper to build the filenames of hazard maps"""
        return self.calc_proxy.build_nrml_path('%s-%s.xml'
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
        """Returns the quantile levels specified in the config file of this
        job.
        """
        return self.calc_proxy.extract_values_from_config(
            general.QUANTILE_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)

    @property
    def poes_hazard_maps(self):
        """
        Returns the PoEs at which the hazard maps will be calculated, as
        specified in the config file of this job.
        """
        return self.calc_proxy.extract_values_from_config(
            general.POES_PARAM_NAME,
            check_value=lambda v: v >= 0.0 and v <= 1.0)
