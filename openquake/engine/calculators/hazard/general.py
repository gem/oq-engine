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
import random
import itertools
import collections
from operator import attrgetter

import numpy

from openquake.hazardlib.imt import from_string

# FIXME: one must import the engine before django to set DJANGO_SETTINGS_MODULE
from openquake.engine.db import models
from django.db import transaction

from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib.risk import parsers

from openquake.commonlib import logictree, source
from openquake.commonlib.general import split_in_blocks, distinct

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
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks

#: Maximum number of hazard curves to cache, for selects or inserts
CURVE_CACHE_SIZE = 100000

QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"
# Dilation in decimal degrees (http://en.wikipedia.org/wiki/Decimal_degrees)
# 1e-5 represents the approximate distance of one meter at the equator.
DILATION_ONE_METER = 1e-5
 # the following is quite arbitrary, it gives output weights that I like (MS)
NORMALIZATION_FACTOR = 1E-4


class InputWeightLimit(Exception):
    pass


class OutputWeightLimit(Exception):
    pass


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


def all_equal(obj, value):
    """
    :param obj: a numpy array or something else
    :param value: a numeric value
    :returns: a boolean
    """
    eq = (obj == value)
    if isinstance(eq, numpy.ndarray):
        return eq.all()
    else:
        return eq


@tasks.oqtask
def filter_and_split_sources(job_id, sources, sitecol):
    """
    Filter and split a list of hazardlib sources.

    :param int job_id: ID of the current job
    :param list sources: the original sources
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection` instance
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    discr = hc.area_source_discretization
    maxdist = hc.maximum_distance
    srcs = []
    for src in sources:
        sites = src.filter_sites_by_distance_to_source(maxdist, sitecol)
        if sites is not None:
            for ss in source.split_source(src, discr):
                srcs.append(ss)
    return srcs


class AllSources(object):
    """
    A container for sources of different tectonic region types.
    The `split` method yields pairs (trt_model, block-of-sources).
    """
    def __init__(self):
        self.sources = []
        self.weight = {}
        self.trt_model = {}

    def append(self, src, weight, trt_model):
        """
        Collect a source, together with its weight and trt_model.
        """
        self.sources.append(src)
        self.weight[src] = weight
        self.trt_model[src] = trt_model

    def split(self, hint):
        """
        Split the sources in a number of blocks close to the given `hint`.

        :param int hint: hint for the number of blocks
        """
        if self.sources:
            for block in split_in_blocks(
                    self.sources, hint,
                    self.weight.__getitem__,
                    self.trt_model.__getitem__):
                trt_model = self.trt_model[block[0]]
                yield trt_model, block

    def get_total_weight(self):
        """
        Return the total weight of the sources
        """
        return sum(self.weight.itervalues())


class BaseHazardCalculator(base.Calculator):
    """
    Abstract base class for hazard calculators. Contains a bunch of common
    functionality, like initialization procedures.
    """

    def __init__(self, job):
        super(BaseHazardCalculator, self).__init__(job)
        # a dictionary trt_model_id -> num_ruptures
        self.num_ruptures = collections.defaultdict(int)
        # now a dictionary (trt_model_id, gsim) -> poes
        self.curves = {}

    @property
    def hc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.engine.db.models.HazardCalculation`.
        """
        return self.job.hazard_calculation

    @EnginePerformanceMonitor.monitor
    def process_sources(self):
        """
        Filter and split the sources in parallel.
        Return the list of processed sources.
        """
        self.all_sources = AllSources()
        self.job.is_running = True
        self.job.save()
        num_models = len(self.source_collector)
        for i, trt_model_id in enumerate(sorted(self.source_collector), 1):
            trt_model = models.TrtModel.objects.get(pk=trt_model_id)
            sc = self.source_collector[trt_model_id]
            # NB: the filtering of the sources by site is slow, so it is
            # done in parallel
            sm_lt_path = tuple(trt_model.lt_model.sm_lt_path)
            logs.LOG.progress(
                '[%d of %d] Filtering/splitting %d source(s) for '
                'sm_lt_path=%s, TRT=%s, model=%s', i, num_models,
                len(sc.sources), sm_lt_path, trt_model.tectonic_region_type,
                trt_model.lt_model.sm_name)
            if len(sc.sources) > self.concurrent_tasks:
                # filter in parallel
                sc.sources = tasks.apply_reduce(
                    filter_and_split_sources,
                    (self.job.id, sc.sources, self.hc.site_collection),
                    list.__add__, [], self.concurrent_tasks)
            else:  # few sources
                # filter sequentially on a single core
                sc.sources = filter_and_split_sources.task_func(
                    self.job.id, sc.sources, self.hc.site_collection)
            sc.sources.sort(key=attrgetter('source_id'))
            if not sc.sources:
                logs.LOG.warn(
                    'Could not find sources close to the sites in %s '
                    'sm_lt_path=%s, maximum_distance=%s km',
                    trt_model.lt_model.sm_name, sm_lt_path,
                    self.hc.maximum_distance)
                continue
            for src in sc.sources:
                self.all_sources.append(
                    src, sc.update_num_ruptures(src), trt_model)
            trt_model.num_sources = len(sc.sources)
            trt_model.num_ruptures = sc.num_ruptures
            trt_model.save()
        return self.all_sources.get_total_weight()

    def task_arg_gen(self):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.
        Yielded results are of the form
        (job_id, site_collection, sources, trt_model_id, gsims).
        """
        if self._task_args:
            # the method was already called and the arguments generated
            for args in self._task_args:
                yield args
            return
        sitecol = self.hc.site_collection
        task_no = 0
        tot_sources = 0
        for trt_model, block in self.all_sources.split(self.concurrent_tasks):
            args = (self.job.id, sitecol, block, trt_model.id)
            self._task_args.append(args)
            yield args
            tot_sources += len(block)
            task_no += 1
            logs.LOG.info('Submitting task #%d, %d source(s), weight=%d',
                          task_no, len(block), block.weight)
        logs.LOG.info('Processed %d sources for %d TRTs',
                      tot_sources, len(self.source_collector))

    def task_completed(self, result):
        """
        Simply call the method `agg_curves`.

        :param result: the result of the .core_calc_task
        """
        self.agg_curves(self.curves, result)

    @EnginePerformanceMonitor.monitor
    def agg_curves(self, acc, result):
        """
        This is used to incrementally update hazard curve results by combining
        an initial value with some new results. (Each set of new results is
        computed over only a subset of seismic sources defined in the
        calculation model.)

        :param acc:
            A dictionary of curves
        :param result:
            A triplet `(curves_by_gsim, trt_model_id, bbs)`.
            `curves_by_gsim` is a list of pairs `(gsim, curves_by_imt)`
            where `curves_by_imt` is a list of 2-D numpy arrays
            representing the new results which need to be combined
            with the current value. These should be the same shape as
            `acc[tr_model_id, gsim][j]` where `gsim` is the GSIM
            name and `j` is the IMT ordinal.
        """
        curves_by_gsim, trt_model_id, bbs = result
        for gsim, probs in curves_by_gsim:
            pnes = []
            for prob, zero in itertools.izip(probs, self.zeros):
                pnes.append(1 - (zero if all_equal(prob, 0) else prob))
            pnes1 = numpy.array(pnes)
            pnes2 = 1 - acc.get((trt_model_id, gsim), self.zeros)
            acc[trt_model_id, gsim] = 1 - pnes1 * pnes2

        if self.hc.poes_disagg:
            for bb in bbs:
                self.bb_dict[bb.lt_model_id, bb.site_id].update_bb(bb)

        return acc

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
        self.initialize_sources()

        # The input weight is given by the number of ruptures generated
        # by the sources; for point sources however a corrective factor
        # given by the parameter `point_source_weight` is applied
        input_weight = self.process_sources()

        self.imtls = self.hc.intensity_measure_types_and_levels
        n_sites = len(self.hc.site_collection)
        if self.imtls:
            n_imts = float(len(self.imtls))
            n_levels = sum(len(lvls) for lvls in self.imtls.itervalues()
                           ) / n_imts
            self.zeros = numpy.array(
                [numpy.zeros((n_sites, len(self.imtls[imt])))
                 for imt in sorted(self.imtls)])
            self.ones = [numpy.zeros(len(self.imtls[imt]), dtype=float)
                         for imt in sorted(self.imtls)]
            logs.LOG.info('%d IMT, %s level(s) and %d site(s)',
                          n_imts, n_levels, n_sites)
        else:
            n_imts = len(self.hc.intensity_measure_types)
            n_levels = 0

        # The output weight is a pure number which is proportional to the size
        # of the expected output of the calculator. For classical and disagg
        # calculators it is given by
        # n_sites * n_realizations * n_imts * n_levels;
        # for the event based calculator is given by n_sites * n_realizations
        # * n_levels * n_imts * (n_ses * investigation_time) / 10000
        max_realizations = self.get_max_realizations()
        output_weight = n_sites * n_imts * max_realizations
        if 'EventBased' in self.__class__.__name__:
            total_time = (self.hc.investigation_time *
                          self.hc.ses_per_logic_tree_path)
            output_weight *= total_time * NORMALIZATION_FACTOR
        else:
            output_weight *= n_levels

        logs.LOG.info('Total weight of the sources=%s', input_weight)
        logs.LOG.info('Expected output size=%s', output_weight)
        with transaction.commit_on_success(using='job_init'):
            models.JobInfo.objects.create(
                oq_job=self.job,
                num_sites=n_sites,
                num_realizations=max_realizations,
                num_imts=n_imts,
                num_levels=n_levels,
                input_weight=input_weight,
                output_weight=output_weight)
        self.check_limits(input_weight, output_weight)
        return input_weight, output_weight

    def check_limits(self, input_weight, output_weight):
        """
        Compute the total weight of the source model and the expected
        output size and compare them with the parameters max_input_weight
        and max_output_weight in openquake.cfg; if the parameters are set
        """
        if (self.max_input_weight and
                input_weight > self.max_input_weight):
            raise InputWeightLimit(
                'A limit of %d on the maximum source model weight was set. '
                'The weight of your model is %d. Please reduce your model '
                'or raise the parameter max_input_weight in openquake.cfg'
                % (self.max_input_weight, input_weight))
        elif self.max_output_weight and output_weight > self.max_output_weight:
            raise OutputWeightLimit(
                'A limit of %d on the maximum output weight was set. '
                'The weight of your output is %d. Please reduce the number '
                'of sites, the number of IMTs, the number of realizations '
                'or the number of stochastic event sets; otherwise, '
                'raise the parameter max_output_weight in openquake.cfg'
                % (self.max_input_weight, input_weight))

    def post_execute(self):
        """Inizialize realizations"""
        self.initialize_realizations()
        if self.curves:
            # must be called after the realizations are known
            self.save_hazard_curves()

    @EnginePerformanceMonitor.monitor
    def initialize_sources(self):
        """
        Parse source models and validate source logic trees. It also
        filters the sources far away and apply uncertainties to the
        relevant ones. Notice that sources are automatically split.

        :returns:
            a list with the number of sources for each source model
        """
        logs.LOG.progress("initializing sources")
        self.source_model_lt = logictree.SourceModelLogicTree.from_hc(self.hc)
        sm_paths = distinct(self.source_model_lt)
        nrml_to_hazardlib = source.NrmlHazardlibConverter(
            self.hc.investigation_time,
            self.hc.rupture_mesh_spacing,
            self.hc.width_of_mfd_bin,
            self.hc.area_source_discretization,
        )
        # define an ordered dictionary trt_model_id -> SourceCollector
        self.source_collector = collections.OrderedDict()
        for i, (sm, weight, smpath) in enumerate(sm_paths):
            fname = os.path.join(self.hc.base_path, sm)
            apply_unc = self.source_model_lt.make_apply_uncertainties(smpath)
            source_collectors = source.parse_source_model(
                fname, nrml_to_hazardlib, apply_unc)
            trts = [sc.trt for sc in source_collectors]

            self.source_model_lt.tectonic_region_types.update(trts)
            lt_model = models.LtSourceModel.objects.create(
                hazard_calculation=self.hc, sm_lt_path=smpath, ordinal=i,
                sm_name=sm, weight=weight)
            if self.hc.inputs.get('gsim_logic_tree'):  # check TRTs
                gsims_by_trt = lt_model.make_gsim_lt(trts).values
            else:
                gsims_by_trt = {}

            # save TrtModels for each tectonic region type
            for sc in source_collectors:
                # NB: the source_collectors are ordered by number of sources
                # and lexicographically, so the models are in the right order
                trt_model_id = models.TrtModel.objects.create(
                    lt_model=lt_model,
                    tectonic_region_type=sc.trt,
                    num_sources=len(sc.sources),
                    num_ruptures=sc.num_ruptures,
                    min_mag=sc.min_mag,
                    max_mag=sc.max_mag,
                    gsims=gsims_by_trt.get(sc.trt, [])).id
                self.source_collector[trt_model_id] = sc

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

    def get_max_realizations(self):
        """
        Return the number of realizations that will be generated.
        In the event based case such number can be over-estimated,
        if the method is called in the pre_execute phase, because
        some tectonic region types may have no occurrencies. The
        number is correct if the method is called in the post_execute
        phase.
        """
        if self.hc.number_of_logic_tree_samples:
            return self.hc.number_of_logic_tree_samples
        gsim_lt_dict = {}  # gsim_lt per source model logic tree path
        for sm, weight, sm_lt_path in self.source_model_lt:
            lt_model = models.LtSourceModel.objects.get(
                hazard_calculation=self.hc, sm_lt_path=sm_lt_path)
            if not sm_lt_path in gsim_lt_dict:
                gsim_lt_dict[sm_lt_path] = lt_model.make_gsim_lt()
        return sum(gsim_lt.get_num_paths()
                   for gsim_lt in gsim_lt_dict.itervalues())

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
        num_samples = self.hc.number_of_logic_tree_samples
        gsim_lt_dict = {}  # gsim_lt per source model logic tree path
        for idx, (sm, weight, sm_lt_path) in enumerate(self.source_model_lt):
            lt_model = models.LtSourceModel.objects.get(
                hazard_calculation=self.hc, sm_lt_path=sm_lt_path)
            if not sm_lt_path in gsim_lt_dict:
                gsim_lt_dict[sm_lt_path] = lt_model.make_gsim_lt()
            gsim_lt = gsim_lt_dict[sm_lt_path]
            if num_samples:  # sampling, pick just one gsim realization
                rnd = random.Random(self.hc.random_seed + idx)
                rlzs = [logictree.sample_one(gsim_lt, rnd)]
            else:
                rlzs = list(gsim_lt)  # full enumeration
            logs.LOG.info('Creating %d GMPE realization(s) for model %s, %s',
                          len(rlzs), lt_model.sm_name, lt_model.sm_lt_path)
            self._initialize_realizations(idx, lt_model, rlzs, gsim_lt)
        num_ind_rlzs = sum(gsim_lt.get_num_paths()
                           for gsim_lt in gsim_lt_dict.itervalues())
        if num_samples > num_ind_rlzs:
            logs.LOG.warn("""
The number of independent realizations is %d but you are using %d samplings.
That means that some GMPEs will be sampled more than once, resulting in
duplicated data and redundant computation. You should switch to full
enumeration mode, i.e. set number_of_logic_tree_samples=0 in your .ini file.
""", num_ind_rlzs, num_samples)

    @transaction.commit_on_success(using='job_init')
    def _initialize_realizations(self, idx, lt_model, realizations, gsim_lt):
        # create the realizations for the given lt source model
        trt_models = lt_model.trtmodel_set.filter(num_ruptures__gt=0)
        if not trt_models:
            return
        rlz_ordinal = idx * len(realizations)
        for gsim_by_trt, weight, lt_path in realizations:
            if lt_model.weight is not None and weight is not None:
                weight = lt_model.weight * weight
            else:
                weight = None
            rlz = models.LtRealization.objects.create(
                lt_model=lt_model, gsim_lt_path=lt_path,
                weight=weight, ordinal=rlz_ordinal)
            rlz_ordinal += 1
            for trt_model in trt_models:
                trt = trt_model.tectonic_region_type
                # populate the association table rlz <-> trt_model
                models.AssocLtRlzTrtModel.objects.create(
                    rlz=rlz, trt_model=trt_model, gsim=gsim_by_trt[trt])
                trt_model.gsims = gsim_lt.values[trt]
                trt_model.save()

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

    # this could be parallelized in the future, however in all the cases
    # I have seen until now, the serialized approach is fast enough (MS)
    @EnginePerformanceMonitor.monitor
    def save_hazard_curves(self):
        """
        Post-execution actions. At the moment, all we do is finalize the hazard
        curve results.
        """
        imtls = self.hc.intensity_measure_types_and_levels
        points = self.hc.points_to_compute()
        sorted_imts = sorted(imtls)
        curves_by_imt = dict((imt, []) for imt in sorted_imts)

        for rlz in self._get_realizations():
            # create a multi-imt curve
            multicurve = models.Output.objects.create_output(
                self.job, "hc-multi-imt-rlz-%s" % rlz.id,
                "hazard_curve_multi")
            models.HazardCurve.objects.create(
                output=multicurve, lt_realization=rlz,
                investigation_time=self.hc.investigation_time)

            with self.monitor('building curves per realization'):
                imt_curves = zip(
                    sorted_imts, models.build_curves(rlz, self.curves))
            for imt, curves in imt_curves:
                curves_by_imt[imt].append(curves)

                # create a new `HazardCurve` 'container' record for each
                # realization for each intensity measure type
                hc_im_type, sa_period, sa_damping = from_string(imt)

                # save output
                hco = models.Output.objects.create(
                    oq_job=self.job,
                    display_name="Hazard Curve rlz-%s-%s" % (rlz.id, imt),
                    output_type='hazard_curve',
                )

                # save hazard_curve
                haz_curve = models.HazardCurve.objects.create(
                    output=hco,
                    lt_realization=rlz,
                    investigation_time=self.hc.investigation_time,
                    imt=hc_im_type,
                    imls=imtls[imt],
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                )

                # save hazard_curve_data
                logs.LOG.info('saving %d hazard curves for %s, imt=%s',
                              len(points), hco, imt)
                writer.CacheInserter.saveall([models.HazardCurveData(
                    hazard_curve=haz_curve,
                    poes=list(poes),
                    location='POINT(%s %s)' % (p.longitude, p.latitude),
                    weight=rlz.weight)
                    for p, poes in zip(points, curves)])

        self.curves = {}  # save memory for the post-processing phase
        if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
            self.curves_by_imt = curves_by_imt

    @EnginePerformanceMonitor.monitor
    def do_aggregate_post_proc(self):
        """
        Grab hazard data for all realizations and sites from the database and
        compute mean and/or quantile aggregates (depending on which options are
        enabled in the calculation).

        Post-processing results will be stored directly into the database.
        """
        del self.source_collector  # save memory
        weights = [rlz.weight for rlz in models.LtRealization.objects.filter(
            lt_model__hazard_calculation=self.hc)]
        num_rlzs = len(weights)
        if not num_rlzs:
            logs.LOG.warn('No realizations for hazard_calculation_id=%d',
                          self.hc.id)
            return
        elif num_rlzs == 1 and self.hc.quantile_hazard_curves:
            logs.LOG.warn(
                'There is only one realization, the configuration parameter '
                'quantile_hazard_curves should not be set')
            return

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

            # num_rlzs * num_sites * num_levels
            # NB: different IMTs can have different num_levels
            all_curves_for_imt = numpy.array(self.curves_by_imt[imt])
            del self.curves_by_imt[imt]  # save memory
            with transaction.commit_on_success(using='job_init'):
                inserter = writer.CacheInserter(
                    models.HazardCurveData, CURVE_CACHE_SIZE)

                # curve_poes below is an array num_rlzs * num_levels
                for i, site in enumerate(self.hc.site_collection):
                    wkt = site.location.wkt2d
                    curve_poes = numpy.array(
                        [c_by_rlz[i] for c_by_rlz in all_curves_for_imt])
                    # do means and quantiles
                    # quantiles first:
                    if self.hc.quantile_hazard_curves:
                        for quantile in self.hc.quantile_hazard_curves:
                            if self.hc.number_of_logic_tree_samples == 0:
                                # explicitly weighted quantiles
                                q_curve = weighted_quantile_curve(
                                    curve_poes, weights, quantile)
                            else:
                                # implicitly weighted quantiles
                                q_curve = quantile_curve(
                                    curve_poes, quantile)
                            inserter.add(
                                models.HazardCurveData(
                                    hazard_curve_id=(
                                        container_ids['q%s' % quantile]),
                                    poes=q_curve.tolist(),
                                    location=wkt)
                            )

                    # then means
                    if self.hc.mean_hazard_curves:
                        m_curve = mean_curve(curve_poes, weights=weights)
                        inserter.add(
                            models.HazardCurveData(
                                hazard_curve_id=container_ids['mean'],
                                poes=m_curve.tolist(),
                                location=wkt)
                        )
                inserter.flush()
