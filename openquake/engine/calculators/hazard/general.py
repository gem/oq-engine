# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
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
import re
import collections

import openquake.hazardlib
import openquake.hazardlib.site
from openquake.hazardlib import correlation

# FIXME: one must import the engine before django to set DJANGO_SETTINGS_MODULE
from openquake.engine.db import models
from django.db import transaction

from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib.risk import parsers

from openquake.engine.input import source, exposure
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
from openquake.engine.input import logictree
from openquake.engine.utils import config
from openquake.engine.utils.general import block_splitter
from openquake.engine.performance import EnginePerformanceMonitor

#: Maximum number of hazard curves to cache, for selects or inserts
CURVE_CACHE_SIZE = 100000

QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"
# Dilation in decimal degrees (http://en.wikipedia.org/wiki/Decimal_degrees)
# 1e-5 represents the approximate distance of one meter at the equator.
DILATION_ONE_METER = 1e-5


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


def im_dict_to_hazardlib(im_dict):
    """
    Given the dict of intensity measure types and levels, convert them to a
    dict with the same values, except create :mod:`mhlib.imt` objects for the
    new keys.

    :returns:
        A dict of intensity measure level lists, keyed by an IMT object. See
        :mod:`openquake.hazardlib.imt` for more information.
    """
    # TODO: file a bug about  SA periods in hazardlib imts.
    # Why are values of 0.0 not allowed? Technically SA(0.0) means PGA, but
    # there must be a reason why we can't do this.
    hazardlib_im = {}

    for imt, imls in im_dict.items():
        hazardlib_imt = imt_to_hazardlib(imt)
        hazardlib_im[hazardlib_imt] = imls

    return hazardlib_im


def imt_to_hazardlib(imt):
    """Covert an IMT string to an hazardlib object.

    :param str imt:
        Given the IMT string (defined in the job config file), convert it to
        equivlent hazardlib object. See :mod:`openquake.hazardlib.imt`.
    """
    if 'SA' in imt:
        match = re.match(r'^SA\(([^)]+?)\)$', imt)
        period = float(match.group(1))
        return openquake.hazardlib.imt.SA(period, models.DEFAULT_SA_DAMPING)
    else:
        imt_class = getattr(openquake.hazardlib.imt, imt)
        return imt_class()


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
        # a dictionary source model name -> source_ids
        self.sources_per_model = collections.defaultdict(list)
        # a dictionary rlz -> source model name (in the logic tree)
        self.rlz_to_sm = {}

    def clean_up(self, *args, **kwargs):
        """Clean up dictionaries at the end"""
        self.sources_per_model.clear()
        self.rlz_to_sm.clear()

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

    def task_arg_gen(self, block_size):
        """
        To override in subclasses
        """

    def _get_realizations(self):
        """
        Get all of the logic tree realizations for this calculation.
        """
        return models.LtRealization.objects\
            .filter(hazard_calculation=self.hc).order_by('id')

    @EnginePerformanceMonitor.monitor
    def initialize_sources(self):
        """
        Parse and validate source logic trees
        """
        logs.LOG.progress("initializing sources")
        for src_path in logictree.read_logic_trees(self.hc):
            for src_nrml in nrml_parsers.SourceModelParser(
                    os.path.join(self.hc.base_path, src_path)).parse():
                src = source.nrml_to_hazardlib(
                    src_nrml,
                    self.hc.rupture_mesh_spacing,
                    self.hc.width_of_mfd_bin,
                    self.hc.area_source_discretization)
                if self.hc.sites_affected_by(src):
                    self.sources_per_model[src_path].append(src)
            logs.LOG.info(
                'found %d relevant sources for model %s',
                len(self.sources_per_model[src_path]), src_path)
        # reorder the sources by typology, to have a better distribution:
        # Area, CharacteristicFault, ComplexFault, Point, SimpleFault
        for src_list in self.sources_per_model.itervalues():
            src_list.sort(key=lambda src: src.__class__.__name__)

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
        sites = self.hc.points_to_compute(save_sites=True)
        logs.LOG.info('Considering %d sites', len(sites))

        site_model_inp = self.hc.site_model
        if site_model_inp:
            store_site_model(self.job, site_model_inp)

    # Silencing 'Too many local variables'
    # pylint: disable=R0914
    @transaction.commit_on_success(using='job_init')
    def initialize_realizations(self, rlz_callbacks=None):
        """
        Create records for the `hzrdr.lt_realization`.

        This function works either in random sampling mode (when lt_realization
        models get the random seed value) or in enumeration mode (when weight
        values are populated). In both cases we record the logic tree paths
        for both trees in the `lt_realization` record, as well as ordinal
        number of the realization (zero-based).

        :param rlz_callbacks:
            Optionally, you can specify a list of callbacks for each
            realization.  In the case of the classical hazard calculator, for
            example, we would include a callback function to create initial
            records for temporary hazard curve result data.

            Callbacks should accept a single argument:
            A :class:`~openquake.engine.db.models.LtRealization` object.
        """
        logs.LOG.progress("initializing realizations")
        if self.job.hazard_calculation.number_of_logic_tree_samples > 0:
            # random sampling of paths
            self._initialize_realizations_montecarlo(
                rlz_callbacks=rlz_callbacks)
        else:
            # full paths enumeration
            self._initialize_realizations_enumeration(
                rlz_callbacks=rlz_callbacks)

    def _initialize_realizations_enumeration(self, rlz_callbacks=None):
        """
        Perform full paths enumeration of logic trees and populate
        lt_realization table.

        :param rlz_callbacks:
            See :meth:`initialize_realizations` for more info.
        """
        hc = self.job.hazard_calculation
        ltp = logictree.LogicTreeProcessor.from_hc(hc)
        self.rlz_to_sm = {}

        for i, path_info in enumerate(ltp.enumerate_paths()):
            source_model_filename, weight, sm_lt_path, gsim_lt_path = path_info

            lt_rlz = models.LtRealization.objects.create(
                hazard_calculation=hc,
                ordinal=i,
                seed=None,
                weight=weight,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # total_items is obsolete and will be removed
                total_items=-1)

            self.rlz_to_sm[lt_rlz] = source_model_filename

            # Run realization callback (if any) to do additional initialization
            # for each realization:
            if rlz_callbacks is not None:
                for cb in rlz_callbacks:
                    cb(lt_rlz)

    def _initialize_realizations_montecarlo(self, rlz_callbacks=None):
        """
        Perform random sampling of both logic trees and populate lt_realization
        table.

        :param rlz_callbacks:
            See :meth:`initialize_realizations` for more info.
        """
        # Each realization will have two seeds:
        # One for source model logic tree, one for GSIM logic tree.
        rnd = random.Random()
        seed = self.hc.random_seed
        rnd.seed(seed)

        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
        self.rlz_to_sm = {}

        # The first realization gets the seed we specified in the config file.
        for i in xrange(self.hc.number_of_logic_tree_samples):
            # Sample source model logic tree branch paths:
            source_model_filename, sm_lt_path = (
                ltp.sample_source_model_logictree(
                    rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32)))

            # Sample GSIM logic tree branch paths:
            gsim_lt_path = ltp.sample_gmpe_logictree(
                rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32))

            lt_rlz = models.LtRealization.objects.create(
                hazard_calculation=self.hc,
                ordinal=i,
                seed=seed,
                weight=None,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # total_items is obsolete and will be removed
                total_items=-1
            )

            self.rlz_to_sm[lt_rlz] = source_model_filename

            # Run realization callback (if any) to do additional initialization
            # for each realization:
            if rlz_callbacks is not None:
                for cb in rlz_callbacks:
                    cb(lt_rlz)

            # update the seed for the next realization
            seed = rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32)
            rnd.seed(seed)

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
            hazard_calculation=self.hc).count()

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
            im_type, sa_period, sa_damping = models.parse_imt(imt)

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
