# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
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

import os
import itertools
import collections

from openquake.hazardlib import correlation
from openquake.hazardlib.imt import from_string

# FIXME: one must import the engine before django to set DJANGO_SETTINGS_MODULE
from openquake.engine.db import models
from django.db import transaction

from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib.risk import parsers

from openquake.commonlib import logictree, source
from openquake.commonlib.general import block_splitter, ceil, distinct

from openquake.engine.input import exposure
from openquake.engine import logs
from openquake.engine import writer
from openquake.engine.calculators import base
from openquake.engine.calculators.post_processing import mean_curve
from openquake.engine.calculators.post_processing import quantile_curve
from openquake.engine.calculators.post_processing import (
    weighted_quantile_curve
)
from openquake.engine.export import core as export_core
from openquake.engine.export import hazard as hazard_export
from openquake.engine.utils import config
from openquake.engine.performance import EnginePerformanceMonitor

#: Maximum number of hazard curves to cache, for selects or inserts
CURVE_CACHE_SIZE = 100000

QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"
# Dilation in decimal degrees (http://en.wikipedia.org/wiki/Decimal_degrees)
# 1e-5 represents the approximate distance of one meter at the equator.
DILATION_ONE_METER = 1e-5


def make_gsim_lt(hc, trts):
    """
    Helper to instantiate a GsimLogicTree object from the logic tree file.

    :param hc: `HazardCalculation` instance
    :param trts: list of tectonic region type strings
    """
    fname = os.path.join(hc.base_path, hc.inputs['gsim_logic_tree'])
    return logictree.GsimLogicTree(
        fname, trts, hc.number_of_logic_tree_samples, hc.random_seed)


def store_site_model(job, site_model_source):
    """Invoke site model parser and save the site-specified parameter data to
    the database.

    :param job:
        The job that is loading this site_model_source
    :param site_model_source:
        Filename or file-like object containing the site model XML data.
    :returns:
        `list` of ids of the newly-inserted `hzrdi.site_model` records.
    """
    parser = nrml_parsers.SiteModelParser(site_model_source)
    data = [models.SiteModel(vs30=node.vs30,
                             vs30_type=node.vs30_type,
                             z1pt0=node.z1pt0,
                             z2pt5=node.z2pt5,
                             location=node.wkt,
                             job_id=job.id)
            for node in parser.parse()]
    return writer.CacheInserter.saveall(data)


def get_correl_model(hc):
    """
    Helper function for constructing the appropriate correlation model.

    :param hc:
        A :class:`openquake.engine.db.models.HazardCalculation` instance.

    :returns:
        A correlation object. See :mod:`openquake.hazardlib.correlation` for
        more info.
    """
    correl_model_cls = getattr(
        correlation,
        '%sCorrelationModel' % hc.ground_motion_correlation_model,
        None)
    if correl_model_cls is None:
        # There's no correlation model for this calculation.
        return None

    return correl_model_cls(**hc.ground_motion_correlation_params)


class BaseHazardCalculator(base.Calculator):
    """
    Abstract base class for hazard calculators. Contains a bunch of common
    functionality, like initialization procedures.
    """

    def __init__(self, job):
        super(BaseHazardCalculator, self).__init__(job)
        # a dictionary (sm_lt_path, trt) -> source blocks
        self.source_blocks_per_ltpath = collections.defaultdict(list)
        self.rupt_collectors = []
        self.num_ruptures = collections.defaultdict(float)

    def clean_up(self, *args, **kwargs):
        """Clean up dictionaries at the end"""
        self.source_blocks_per_ltpath.clear()

    @property
    def hc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.engine.db.models.HazardCalculation`.
        """
        return self.job.hazard_calculation

    def concurrent_tasks(self):
        """
        For hazard calculators, the number of tasks to be in queue
        at any given time is specified in the configuration file.
        """
        return int(config.get('hazard', 'concurrent_tasks'))

    def task_arg_gen(self):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        For this default implementation, yielded results are quartets
        (job_id, sources, tom, gsim_by_rlz).

        Override this in subclasses as necessary.
        """
        sitecol = self.hc.site_collection
        trt_models = models.TrtModel.objects.filter(
            lt_model__hazard_calculation=self.hc)
        for task_no, trt_model in enumerate(trt_models):
            ltpath = tuple(trt_model.lt_model.sm_lt_path)
            trt = trt_model.tectonic_region_type
            gsims = [logictree.GSIM[gsim]() for gsim in trt_model.gsims]
            for block in self.source_blocks_per_ltpath[ltpath, trt]:
                yield (self.job.id, sitecol, block, trt_model.id,
                       gsims, task_no)

    def _get_realizations(self):
        """
        Get all of the logic tree realizations for this calculation.
        """
        return models.LtRealization.objects\
            .filter(lt_model__hazard_calculation=self.hc).order_by('id')

    def pre_execute(self):
        """
        Initialize risk models, site model and sources
        """
        self.parse_risk_models()
        self.initialize_site_model()
        lt_models = self.initialize_sources()
        js = models.JobStats.objects.get(oq_job=self.job)
        js.num_sources = [model.get_num_sources() for model in lt_models]
        js.save()

    def post_execute(self):
        """Inizialize realizations, except for the scenario calculator"""
        if self.hc.calculation_mode != 'scenario':
            self.initialize_realizations()

    @EnginePerformanceMonitor.monitor
    def initialize_sources(self):
        """
        Parse source models and validate source logic trees. It also
        filters the sources far away and apply uncertainties to the
        relevant ones. As a side effect it populates the instance dictionary
        `.source_blocks_per_ltpath`. Notice that sources are automatically
        split.

        :returns:
            a list with the number of sources for each source model
        """
        logs.LOG.progress("initializing sources")
        self.source_model_lt = logictree.SourceModelLogicTree.from_hc(self.hc)
        sm_paths = distinct(self.source_model_lt.gen_value_weight_path())
        nblocks = ceil(config.get('hazard', 'concurrent_tasks'), len(sm_paths))
        lt_models = []
        for i, (sm, weight, smpath) in enumerate(sm_paths):
            fname = os.path.join(self.hc.base_path, sm)
            source_collector = source.parse_source_model_smart(
                fname,
                self.hc.sites_affected_by,
                self.source_model_lt.make_apply_uncertainties(smpath),
                self.hc)
            if not source_collector.source_weights:
                raise RuntimeError(
                    'Could not find sources close to the sites in %s '
                    '(maximum_distance=%s km)' %
                    (fname, self.hc.maximum_distance))

            self.source_model_lt.tectonic_region_types.update(
                source_collector.source_weights)
            lt_model = models.LtSourceModel.objects.create(
                hazard_calculation=self.hc, sm_lt_path=smpath, ordinal=i,
                sm_name=sm, weight=weight)
            lt_models.append(lt_model)
            for trt, blocks in source_collector.split_blocks(nblocks):
                self.source_blocks_per_ltpath[smpath, trt] = blocks
                n = sum(len(block) for block in blocks)
                logs.LOG.info('Found %d relevant source(s) for %s %s, TRT=%s',
                              n, sm, smpath, trt)
                logs.LOG.info('Splitting in %d blocks', len(blocks))
                for i, block in enumerate(blocks, 1):
                    logs.LOG.debug('%s, block %d: %d source(s), weight %s',
                                   trt, i, len(block), block.weight)

            # save TrtModel objects for each tectonic region type
            for trt in source_collector.sorted_trts():
                gmpe_lt = make_gsim_lt(self.hc, [trt])
                gsims = list(gmpe_lt.get_gsims(trt))
                models.TrtModel.objects.create(
                    lt_model=lt_model,
                    tectonic_region_type=trt,
                    num_sources=len(source_collector.source_weights[trt]),
                    num_ruptures=source_collector.num_ruptures[trt],
                    min_mag=source_collector.min_mag[trt],
                    max_mag=source_collector.max_mag[trt],
                    gsims=gsims)
        return lt_models

    @EnginePerformanceMonitor.monitor
    def parse_risk_models(self):
        """
        If any risk model is given in the hazard calculation, the
        computation will be driven by risk data. In this case the
        locations will be extracted from the exposure file (if there
        is one) and the imt (and levels) will be extracted from the
        vulnerability model (if there is one)
        """
        hc = self.hc
        if hc.vulnerability_models:
            logs.LOG.progress("parsing risk models")

            hc.intensity_measure_types_and_levels = dict()
            hc.intensity_measure_types = list()

            for vf in hc.vulnerability_models:
                intensity_measure_types_and_levels = dict(
                    (record['IMT'], record['IML']) for record in
                    parsers.VulnerabilityModelParser(vf))

                for imt, levels in \
                        intensity_measure_types_and_levels.items():
                    if (imt in hc.intensity_measure_types_and_levels and
                        (set(hc.intensity_measure_types_and_levels[imt]) -
                         set(levels))):
                        logs.LOG.warning(
                            "The same IMT %s is associated with "
                            "different levels" % imt)
                    else:
                        hc.intensity_measure_types_and_levels[imt] = levels

                hc.intensity_measure_types.extend(
                    intensity_measure_types_and_levels)

            # remove possible duplicates
            if hc.intensity_measure_types is not None:
                hc.intensity_measure_types = list(set(
                    hc.intensity_measure_types))
            hc.save()
            logs.LOG.info("Got IMT and levels "
                          "from vulnerability models: %s - %s" % (
                              hc.intensity_measure_types_and_levels,
                              hc.intensity_measure_types))

        if 'fragility' in hc.inputs:
            hc.intensity_measure_types_and_levels = dict()
            hc.intensity_measure_types = list()

            parser = iter(parsers.FragilityModelParser(
                hc.inputs['fragility']))
            hc = self.hc

            fragility_format, _limit_states = parser.next()

            if (fragility_format == "continuous" and
                    hc.calculation_mode != "scenario"):
                raise NotImplementedError(
                    "Getting IMT and levels from "
                    "a continuous fragility model is not yet supported")

            hc.intensity_measure_types_and_levels = dict(
                (iml['IMT'], iml['imls'])
                for _taxonomy, iml, _params, _no_damage_limit in parser)
            hc.intensity_measure_types.extend(
                hc.intensity_measure_types_and_levels)
            hc.save()

        if 'exposure' in hc.inputs:
            with logs.tracing('storing exposure'):
                exposure.ExposureDBWriter(
                    self.job).serialize(
                    parsers.ExposureModelParser(hc.inputs['exposure']))

    @EnginePerformanceMonitor.monitor
    def initialize_site_model(self):
        """
        Populate the hazard site table.

        If a site model is specified in the calculation configuration,
        parse it and load it into the `hzrdi.site_model` table.
        """
        logs.LOG.progress("initializing sites")
        self.hc.points_to_compute(save_sites=True)

        site_model_inp = self.hc.site_model
        if site_model_inp:
            store_site_model(self.job, site_model_inp)

    @transaction.commit_on_success(using='job_init')
    def initialize_realizations(self):
        """
        Create records for the `hzrdr.lt_realization`.

        This function works either in random sampling mode (when lt_realization
        models get the random seed value) or in enumeration mode (when weight
        values are populated). In both cases we record the logic tree paths
        for both trees in the `lt_realization` record, as well as ordinal
        number of the realization (zero-based).
        """
        logs.LOG.progress("initializing realizations")
        if self.hc.number_of_logic_tree_samples:  # sampling
            self.gmpe_lt = make_gsim_lt(
                self.hc, self.source_model_lt.tectonic_region_types)
            all_paths = [[path] for path in
                         self.gmpe_lt.gen_path_weight()]
        else:  # full enumeration
            # build the gmpe paths inside _initialize_realizations
            all_paths = itertools.cycle([None])
        idx = 0
        for (sm, weight, sm_lt_path), gmpe_paths in zip(
                self.source_model_lt.gen_value_weight_path(), all_paths):
            lt_model = models.LtSourceModel.objects.get(
                hazard_calculation=self.hc,
                sm_lt_path=sm_lt_path)
            self._initialize_realizations(idx, lt_model, gmpe_paths)
            idx += 1

    @transaction.commit_on_success(using='job_init')
    def _initialize_realizations(self, idx, lt_model, gmpe_paths):
        trt_models = lt_model.trtmodel_set.filter(num_ruptures__gt=0)
        if not trt_models:
            return
        if gmpe_paths is None:
            # called for full enumeration
            self.gmpe_lt = make_gsim_lt(
                self.hc, lt_model.get_tectonic_region_types())
            gmpe_paths = list(self.gmpe_lt.gen_path_weight())
        rlz_ordinal = idx * len(gmpe_paths)
        for gmpe_path, weight in gmpe_paths:
            if lt_model.weight is not None and weight is not None:
                weight = lt_model.weight * weight
            rlz = models.LtRealization.objects.create(
                lt_model=lt_model, gsim_lt_path=gmpe_path,
                weight=weight, ordinal=rlz_ordinal)
            rlz_ordinal += 1
            for trt_model in trt_models:
                # populate the associations rlz <-> trt_model
                gsim = self.gmpe_lt.get_gsim(
                    gmpe_path, trt_model.tectonic_region_type)
                models.AssocLtRlzTrtModel.objects.create(
                    rlz=rlz, trt_model=trt_model, gsim=gsim)

    def _get_outputs_for_export(self):
        """
        Util function for getting :class:`openquake.engine.db.models.Output`
        objects to be exported.

        Gathers all outputs for the job, but filters out `hazard_curve_multi`
        outputs if this option was turned off in the calculation profile.
        """
        outputs = export_core.get_outputs(self.job.id)
        if not self.hc.export_multi_curves:
            outputs = outputs.exclude(output_type='hazard_curve_multi')
        return outputs

    def _do_export(self, output_id, export_dir, export_type):
        """
        Hazard-specific implementation of
        :meth:`openquake.engine.calculators.base.Calculator._do_export`.

        Calls the hazard exporter.
        """
        return hazard_export.export(output_id, export_dir, export_type)

    @EnginePerformanceMonitor.monitor
    def do_aggregate_post_proc(self):
        """
        Grab hazard data for all realizations and sites from the database and
        compute mean and/or quantile aggregates (depending on which options are
        enabled in the calculation).

        Post-processing results will be stored directly into the database.
        """
        num_rlzs = models.LtRealization.objects.filter(
            lt_model__hazard_calculation=self.hc).count()

        num_site_blocks_per_incr = int(CURVE_CACHE_SIZE) / int(num_rlzs)
        if num_site_blocks_per_incr == 0:
            # This means we have `num_rlzs` >= `CURVE_CACHE_SIZE`.
            # The minimum number of sites should be 1.
            num_site_blocks_per_incr = 1
        slice_incr = num_site_blocks_per_incr * num_rlzs  # unit: num records

        if self.hc.mean_hazard_curves:
            # create a new `HazardCurve` 'container' record for mean
            # curves (virtual container for multiple imts)
            models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "mean-curves-multi-imt",
                    "hazard_curve_multi"),
                statistics="mean",
                imt=None,
                investigation_time=self.hc.investigation_time)

        if self.hc.quantile_hazard_curves:
            for quantile in self.hc.quantile_hazard_curves:
                # create a new `HazardCurve` 'container' record for quantile
                # curves (virtual container for multiple imts)
                models.HazardCurve.objects.create(
                    output=models.Output.objects.create_output(
                        self.job, 'quantile(%s)-curves' % quantile,
                        "hazard_curve_multi"),
                    statistics="quantile",
                    imt=None,
                    quantile=quantile,
                    investigation_time=self.hc.investigation_time)

        for imt, imls in self.hc.intensity_measure_types_and_levels.items():
            im_type, sa_period, sa_damping = from_string(imt)

            # prepare `output` and `hazard_curve` containers in the DB:
            container_ids = dict()
            if self.hc.mean_hazard_curves:
                mean_output = models.Output.objects.create_output(
                    job=self.job,
                    display_name='Mean Hazard Curves %s' % imt,
                    output_type='hazard_curve'
                )
                mean_hc = models.HazardCurve.objects.create(
                    output=mean_output,
                    investigation_time=self.hc.investigation_time,
                    imt=im_type,
                    imls=imls,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    statistics='mean'
                )
                container_ids['mean'] = mean_hc.id

            if self.hc.quantile_hazard_curves:
                for quantile in self.hc.quantile_hazard_curves:
                    q_output = models.Output.objects.create_output(
                        job=self.job,
                        display_name=(
                            '%s quantile Hazard Curves %s' % (quantile, imt)
                        ),
                        output_type='hazard_curve'
                    )
                    q_hc = models.HazardCurve.objects.create(
                        output=q_output,
                        investigation_time=self.hc.investigation_time,
                        imt=im_type,
                        imls=imls,
                        sa_period=sa_period,
                        sa_damping=sa_damping,
                        statistics='quantile',
                        quantile=quantile
                    )
                    container_ids['q%s' % quantile] = q_hc.id

            all_curves_for_imt = models.order_by_location(
                models.HazardCurveData.objects.all_curves_for_imt(
                    self.job.id, im_type, sa_period, sa_damping))

            with transaction.commit_on_success(using='job_init'):
                inserter = writer.CacheInserter(
                    models.HazardCurveData, CURVE_CACHE_SIZE)

                for chunk in models.queryset_iter(all_curves_for_imt,
                                                  slice_incr):
                    # slice each chunk by `num_rlzs` into `site_chunk`
                    # and compute the aggregate
                    for site_chunk in block_splitter(chunk, num_rlzs):
                        site = site_chunk[0].location
                        curves_poes = [x.poes for x in site_chunk]
                        curves_weights = [x.weight for x in site_chunk]

                        # do means and quantiles
                        # quantiles first:
                        if self.hc.quantile_hazard_curves:
                            for quantile in self.hc.quantile_hazard_curves:
                                if self.hc.number_of_logic_tree_samples == 0:
                                    # explicitly weighted quantiles
                                    q_curve = weighted_quantile_curve(
                                        curves_poes, curves_weights, quantile
                                    )
                                else:
                                    # implicitly weighted quantiles
                                    q_curve = quantile_curve(
                                        curves_poes, quantile
                                    )
                                inserter.add(
                                    models.HazardCurveData(
                                        hazard_curve_id=(
                                            container_ids['q%s' % quantile]),
                                        poes=q_curve.tolist(),
                                        location=site.wkt)
                                )

                        # then means
                        if self.hc.mean_hazard_curves:
                            m_curve = mean_curve(
                                curves_poes, weights=curves_weights
                            )
                            inserter.add(
                                models.HazardCurveData(
                                    hazard_curve_id=container_ids['mean'],
                                    poes=m_curve.tolist(),
                                    location=site.wkt)
                            )
                inserter.flush()
