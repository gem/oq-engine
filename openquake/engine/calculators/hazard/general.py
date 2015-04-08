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

import itertools
import collections
from operator import attrgetter

from django.contrib.gis.geos.point import Point

import numpy

from openquake.hazardlib.imt import from_string

# FIXME: one must import the engine before django to set DJANGO_SETTINGS_MODULE
from openquake.engine.db import models

from openquake.baselib import general
from openquake.commonlib import readinput, risk_parsers, source
from openquake.commonlib.readinput import (
    get_site_collection, get_site_model)

from openquake.engine.input import exposure
from openquake.engine import logs
from openquake.engine import writer
from openquake.engine.calculators import base
from openquake.risklib import scientific

from openquake.engine.calculators.hazard.post_processing import (
    hazard_curves_to_hazard_map, do_uhs_post_proc)

from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks

QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"
# Dilation in decimal degrees (http://en.wikipedia.org/wiki/Decimal_degrees)
# 1e-5 represents the approximate distance of one meter at the equator.
DILATION_ONE_METER = 1E-5


class InputWeightLimit(Exception):
    pass


class OutputWeightLimit(Exception):
    pass


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


class SiteModelParams(object):
    """
    Wrapper around the SiteModel table with a method .get_closest

    :param job:
        a :class:`openquake.engine.db.models.OqJob` instance
    :param site_model_objects:
        an iterable over objects with attributes
        vs30, measured, z1pt0, z2pt5, lon, lat
    """
    def __init__(self, job, site_model_objects):
        self.job = job
        data = [models.SiteModel(
                vs30=obj.vs30,
                vs30_type='measured' if obj.measured else 'inferred',
                z1pt0=obj.z1pt0,
                z2pt5=obj.z2pt5,
                location=Point(obj.lon, obj.lat),
                job_id=job.id)
                for obj in site_model_objects]
        writer.CacheInserter.saveall(data)

    def get_closest(self, lon, lat):
        """
        :param lon: a given longitude
        :param lat: a given latitude
        :returns:
           the SiteMode record closest to the given longitude and latitude
        """
        query = """\
        SELECT s.*, min(ST_Distance_Sphere(
                        location, 'SRID=4326; POINT(%s %s)')) AS min_dist
        FROM hzrdi.site_model AS s
        WHERE job_id = %d GROUP BY id
        ORDER BY min_dist LIMIT 1;""" % (lon, lat, self.job.id)
        [sm] = models.SiteModel.objects.raw(query)
        return sm


class BaseHazardCalculator(base.Calculator):
    """
    Abstract base class for hazard calculators. Contains a bunch of common
    functionality, like initialization procedures.
    """
    prefilter = True
    tilepath = ()  # set only by the tiling calculator

    def __init__(self, job):
        super(BaseHazardCalculator, self).__init__(job)
        # a dictionary trt_model_id -> num_ruptures
        self.num_ruptures = collections.defaultdict(int)
        # now a dictionary (trt_model_id, gsim) -> poes
        self.acc = general.AccumDict()
        self.mean_hazard_curves = self.oqparam.mean_hazard_curves
        self.quantile_hazard_curves = self.oqparam.quantile_hazard_curves
        self._hazard_curves = []
        self._realizations = []
        self._source_models = []

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Run the `.core_calc_task` in parallel, by using the apply_reduce
        distribution, but it can be overridden in subclasses.
        """
        csm = self.composite_model
        self.acc = tasks.apply_reduce(
            self.core_calc_task,
            (list(csm.sources), self.site_collection, csm.info, self.monitor),
            agg=self.agg_curves, acc=self.acc,
            weight=attrgetter('weight'), key=attrgetter('trt_model_id'))

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
            A dictionary `{trt_model_id: (curves_by_gsim, bbs)}`.
            `curves_by_gsim` is a list of pairs `(gsim, curves_by_imt)`
            where `curves_by_imt` is a list of 2-D numpy arrays
            representing the new results which need to be combined
            with the current value. These should be the same shape as
            `acc[tr_model_id, gsim][j]` where `gsim` is the GSIM
            name and `j` is the IMT ordinal.
        """
        for trt_model_id, (curves_by_gsim, bbs) in result.iteritems():
            for gsim, probs in curves_by_gsim:
                pnes = []
                for prob, zero in itertools.izip(probs, self.zeros):
                    pnes.append(1 - (zero if all_equal(prob, 0) else prob))
                pnes1 = numpy.array(pnes)
                pnes2 = 1 - acc.get((trt_model_id, gsim), self.zeros)
                acc[trt_model_id, gsim] = 1 - pnes1 * pnes2

            if self.oqparam.poes_disagg:
                for bb in bbs:
                    self.bb_dict[bb.lt_model_id, bb.site_id].update_bb(bb)

        return acc

    def pre_execute(self):
        """
        Initialize risk models, site model and sources
        """
        self.parse_risk_model()
        self.initialize_site_collection()
        self.initialize_sources()
        info = readinput.get_job_info(
            self.oqparam, self.composite_model, self.site_collection)
        models.JobInfo.objects.create(
            oq_job=self.job,
            num_sites=info['n_sites'],
            num_realizations=info['max_realizations'],
            num_imts=info['n_imts'],
            num_levels=info['n_levels'],
            input_weight=info['input_weight'],
            output_weight=info['output_weight'])
        self.check_limits(info['input_weight'], info['output_weight'])
        self.init_zeros_ones()
        return info['input_weight'], info['output_weight']

    def init_zeros_ones(self):
        imtls = self.oqparam.imtls
        if None in imtls.values():  # no levels, cannot compute curves
            return
        n_sites = len(self.site_collection)
        self.zeros = numpy.array(
            [numpy.zeros((n_sites, len(imtls[imt])))
             for imt in sorted(imtls)])
        self.ones = [numpy.zeros(len(imtls[imt]), dtype=float)
                     for imt in sorted(imtls)]

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
        # must be called after the realizations are known
        self.save_hazard_curves()

    @EnginePerformanceMonitor.monitor
    def initialize_sources(self):
        """
        Parse source models, apply uncertainties and validate source logic
        trees. Save in the database LtSourceModel and TrtModel objects.
        """
        logs.LOG.progress("initializing sources")
        self.composite_model = readinput.get_composite_source_model(
            self.oqparam, self.site_collection, self.prefilter)
        for sm in self.composite_model:
            # create an LtSourceModel for each distinct source model
            lt_model = models.LtSourceModel.objects.create(
                hazard_calculation=self.job,
                sm_lt_path=self.tilepath + sm.path,
                ordinal=sm.ordinal, sm_name=sm.name, weight=sm.weight,
                samples=sm.samples)
            self._source_models.append(lt_model)
            gsims_by_trt = sm.gsim_lt.values
            # save TrtModels for each tectonic region type
            # and stored the db ID in the in-memory models
            for trt_mod in sm.trt_models:
                trt_mod.id = models.TrtModel.objects.create(
                    lt_model=lt_model,
                    tectonic_region_type=trt_mod.trt,
                    num_sources=len(trt_mod),
                    num_ruptures=trt_mod.num_ruptures,
                    min_mag=trt_mod.min_mag,
                    max_mag=trt_mod.max_mag,
                    gsims=gsims_by_trt[trt_mod.trt]).id
        # rebuild the info object with the trt_ids coming from the db
        self.composite_model.info = source.CompositionInfo(
            self.composite_model.source_models)

    @EnginePerformanceMonitor.monitor
    def parse_risk_model(self):
        """
        If any risk model is given in the hazard calculation, the
        computation will be driven by risk data. In this case the
        locations will be extracted from the exposure file (if there
        is one) and the imt (and levels) will be extracted from the
        vulnerability model (if there is one)
        """
        oqparam = self.job.get_oqparam()
        if 'exposure' in oqparam.inputs:
            with logs.tracing('storing exposure'):
                exposure.ExposureDBWriter(
                    self.job).serialize(
                    risk_parsers.ExposureModelParser(
                        oqparam.inputs['exposure']))
        models.Imt.save_new(map(from_string, oqparam.imtls))

    @EnginePerformanceMonitor.monitor
    def initialize_site_collection(self):
        """
        Populate the hazard site table and create a sitecollection attribute.
        """
        logs.LOG.progress("initializing sites")
        points, site_ids = self.job.save_hazard_sites()
        if not site_ids:
            raise RuntimeError('No sites were imported!')

        logs.LOG.progress("initializing site collection")
        oqparam = self.job.get_oqparam()
        if 'site_model' in oqparam.inputs:
            sm_params = SiteModelParams(
                self.job, get_site_model(oqparam))
        else:
            sm_params = None
        self.site_collection = get_site_collection(
            oqparam, points, site_ids, sm_params)

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
        cm = self.composite_model
        self._realizations = []
        self.rlzs_assoc = cm.get_rlzs_assoc(
            lambda trt_model: models.TrtModel.objects.get(
                pk=trt_model.id).num_ruptures)
        gsims_by_trt_id = self.rlzs_assoc.get_gsims_by_trt_id()
        for lt_model in self._source_models:
            rlzs = self.rlzs_assoc.rlzs_by_smodel.get(lt_model.ordinal, [])
            logs.LOG.info('Creating %d realization(s) for model '
                          '%s, %s', len(rlzs), lt_model.sm_name,
                          '_'.join(lt_model.sm_lt_path))
            for rlz in rlzs:
                gsim_by_trt = self.rlzs_assoc.gsim_by_trt[rlz]
                lt_rlz = models.LtRealization.objects.create(
                    lt_model=lt_model, gsim_lt_path=rlz.gsim_rlz.lt_uid,
                    weight=rlz.weight, ordinal=rlz.ordinal)
                rlz.id = lt_rlz.id
                self._realizations.append(lt_rlz)
                for trt_model in lt_model.trtmodel_set.all():
                    trt = trt_model.tectonic_region_type
                    # populate the association table rlz <-> trt_model
                    models.AssocLtRlzTrtModel.objects.create(
                        rlz=lt_rlz, trt_model=trt_model,
                        gsim=gsim_by_trt[trt])
                    trt_model.gsims = [
                        gsim.__class__.__name__
                        for gsim in gsims_by_trt_id[trt_model.id]]
                    trt_model.save()

    # this could be parallelized in the future, however in all the cases
    # I have seen until now, the serialized approach is fast enough (MS)
    @EnginePerformanceMonitor.monitor
    def save_hazard_curves(self):
        """
        Post-execution actions. At the moment, all we do is finalize the hazard
        curve results.
        """
        if not self.acc:
            return
        imtls = self.oqparam.imtls
        points = models.HazardSite.objects.filter(
            hazard_calculation=self.job).order_by('id')
        sorted_imts = sorted(imtls)
        curves_by_imt = dict((imt, []) for imt in sorted_imts)
        individual_curves = self.job.get_param(
            'individual_curves', missing=True)
        for rlz in self._realizations:
            if individual_curves:
                # create a multi-imt curve
                multicurve = models.Output.objects.create_output(
                    self.job, "hc-multi-imt-rlz-%s" % rlz.id,
                    "hazard_curve_multi")
                models.HazardCurve.objects.create(
                    output=multicurve, lt_realization=rlz,
                    investigation_time=self.oqparam.investigation_time)

            with self.monitor('building curves per realization'):
                imt_curves = zip(
                    sorted_imts, models.build_curves(rlz, self.acc))
            for imt, curves in imt_curves:
                if individual_curves:
                    self.save_curves_for_rlz_imt(
                        rlz, imt, imtls[imt], points, curves)
                curves_by_imt[imt].append(curves)

        self.acc = {}  # save memory for the post-processing phase
        if self.mean_hazard_curves or self.quantile_hazard_curves:
            self.curves_by_imt = curves_by_imt

    def save_curves_for_rlz_imt(self, rlz, imt, imls, points, curves):
        """
        Save the curves corresponding to a given realization and IMT.

        :param rlz: a LtRealization instance
        :param imt: an IMT string
        :param imls: the intensity measure levels for the given IMT
        :param points: the points associated to the curves
        :param curves: the curves
        """
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
            investigation_time=self.oqparam.investigation_time,
            imt=hc_im_type,
            imls=imls,
            sa_period=sa_period,
            sa_damping=sa_damping,
        )
        self._hazard_curves.append(haz_curve)

        # save hazard_curve_data
        logs.LOG.info('saving %d hazard curves for %s, imt=%s',
                      len(points), hco, imt)
        writer.CacheInserter.saveall([models.HazardCurveData(
            hazard_curve=haz_curve,
            poes=list(poes),
            location=p.location,
            weight=rlz.weight)
            for p, poes in zip(points, curves)])

    @EnginePerformanceMonitor.monitor
    def do_aggregate_post_proc(self):
        """
        Grab hazard data for all realizations and sites from the database and
        compute mean and/or quantile aggregates (depending on which options are
        enabled in the calculation).

        Post-processing results will be stored directly into the database.
        """
        num_rlzs = len(self._realizations)
        if not num_rlzs:
            logs.LOG.warn('No realizations for hazard_calculation_id=%d',
                          self.job.id)
            return
        elif num_rlzs == 1 and self.quantile_hazard_curves:
            logs.LOG.warn(
                'There is only one realization, the configuration parameter '
                'quantile_hazard_curves should not be set')
            return

        weights = (None if self.oqparam.number_of_logic_tree_samples
                   else [rlz.weight for rlz in self._realizations])

        if self.oqparam.mean_hazard_curves:
            # create a new `HazardCurve` 'container' record for mean
            # curves (virtual container for multiple imts)
            models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "mean-curves-multi-imt",
                    "hazard_curve_multi"),
                statistics="mean",
                imt=None,
                investigation_time=self.oqparam.investigation_time)

        for quantile in self.quantile_hazard_curves:
            # create a new `HazardCurve` 'container' record for quantile
            # curves (virtual container for multiple imts)
            models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, 'quantile(%s)-curves' % quantile,
                    "hazard_curve_multi"),
                statistics="quantile",
                imt=None,
                quantile=quantile,
                investigation_time=self.oqparam.investigation_time)

        for imt, imls in self.oqparam.imtls.items():
            im_type, sa_period, sa_damping = from_string(imt)

            # prepare `output` and `hazard_curve` containers in the DB:
            container_ids = dict()
            if self.oqparam.mean_hazard_curves:
                mean_output = self.job.get_or_create_output(
                    display_name='Mean Hazard Curves %s' % imt,
                    output_type='hazard_curve'
                )
                mean_hc = models.HazardCurve.objects.create(
                    output=mean_output,
                    investigation_time=self.oqparam.investigation_time,
                    imt=im_type,
                    imls=imls,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    statistics='mean'
                )
                self._hazard_curves.append(mean_hc)
                container_ids['mean'] = mean_hc.id

            for quantile in self.quantile_hazard_curves:
                q_output = self.job.get_or_create_output(
                    display_name=(
                        '%s quantile Hazard Curves %s' % (quantile, imt)),
                    output_type='hazard_curve')
                q_hc = models.HazardCurve.objects.create(
                    output=q_output,
                    investigation_time=self.oqparam.investigation_time,
                    imt=im_type,
                    imls=imls,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    statistics='quantile',
                    quantile=quantile
                )
                self._hazard_curves.append(q_hc)
                container_ids['q%s' % quantile] = q_hc.id

            # num_rlzs * num_sites * num_levels
            # NB: different IMTs can have different num_levels
            all_curves_for_imt = numpy.array(self.curves_by_imt[imt])
            del self.curves_by_imt[imt]  # save memory

            inserter = writer.CacheInserter(
                models.HazardCurveData, max_cache_size=10000)

            # curve_poes below is an array num_rlzs * num_levels
            for i, site in enumerate(self.site_collection):
                wkt = site.location.wkt2d
                curve_poes = numpy.array(
                    [c_by_rlz[i] for c_by_rlz in all_curves_for_imt])

                # calc quantiles first
                for quantile in self.quantile_hazard_curves:
                    q_curve = scientific.quantile_curve(
                        curve_poes, quantile, weights)
                    inserter.add(
                        models.HazardCurveData(
                            hazard_curve_id=(
                                container_ids['q%s' % quantile]),
                            poes=q_curve.tolist(),
                            location=wkt))

                # then means
                if self.mean_hazard_curves:
                    m_curve = scientific.mean_curve(curve_poes, weights)
                    inserter.add(
                        models.HazardCurveData(
                            hazard_curve_id=container_ids['mean'],
                            poes=m_curve.tolist(),
                            location=wkt))
            inserter.flush()

    def post_process(self):
        """
        Optionally generates aggregate curves, hazard maps and
        uniform_hazard_spectra.
        """
        # means/quantiles:
        if self.mean_hazard_curves or self.quantile_hazard_curves:
            self.do_aggregate_post_proc()

        # hazard maps:
        # required for computing UHS
        # if `hazard_maps` is false but `uniform_hazard_spectra` is true,
        # just don't export the maps
        if (self.oqparam.hazard_maps or self.oqparam.uniform_hazard_spectra):
            with self.monitor('generating hazard maps', autoflush=True) as mon:
                tasks.apply_reduce(
                    hazard_curves_to_hazard_map,
                    (self._hazard_curves, self.oqparam.poes, mon))
        if self.oqparam.uniform_hazard_spectra:
            do_uhs_post_proc(self.job)
