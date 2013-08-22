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

import math
import os
import random
import re
import StringIO

import openquake.hazardlib
import openquake.hazardlib.site
import numpy

from django.db import transaction, connections
from django.db.models import Sum
from shapely import geometry

from openquake.hazardlib import correlation
from openquake.hazardlib import geo as hazardlib_geo
from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib.risk import parsers

from openquake.engine.input import exposure
from openquake.engine import engine
from openquake.engine import logs
from openquake.engine import writer
from openquake.engine.calculators import base
from openquake.engine.calculators.post_processing import mean_curve
from openquake.engine.calculators.post_processing import quantile_curve
from openquake.engine.calculators.post_processing import (
    weighted_quantile_curve
)
from openquake.engine.db import models
from openquake.engine.export import core as export_core
from openquake.engine.export import hazard as hazard_export
from openquake.engine.input import logictree
from openquake.engine.input import source
from openquake.engine.utils import config
from openquake.engine.utils import stats
from openquake.engine.utils.general import block_splitter
from openquake.engine.performance import EnginePerformanceMonitor

#: Maximum number of hazard curves to cache, for selects or inserts
CURVE_CACHE_SIZE = 100000

QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"
# Dilation in decimal degrees (http://en.wikipedia.org/wiki/Decimal_degrees)
# 1e-5 represents the approximate distance of one meter at the equator.
DILATION_ONE_METER = 1e-5


def store_site_model(input_mdl, site_model_source):
    """Invoke site model parser and save the site-specified parameter data to
    the database.

    :param input_mdl:
        The `uiapi.input` record which the new `hzrdi.site_model` records
        reference. This `input` record acts as a container for the site model
        data.
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
                             input_id=input_mdl.id)
            for node in parser.parse()]
    return writer.CacheInserter.saveall(data)


def gen_sources(src_ids, apply_uncertainties, rupture_mesh_spacing,
                width_of_mfd_bin, area_source_discretization):
    """
    Hazardlib source objects generator for a given set of sources.

    Performs lazy loading, converting and processing of sources.

    :param src_ids:
        A list of IDs for :class:`openquake.engine.db.models.ParsedSource`
        records.
    :param apply_uncertainties:
        A function to be called on each generated source. See
        :meth:`openquake.engine.input.logictree.LogicTreeProcessor.\
parse_source_model_logictree_path`

    For information about the other parameters, see
    :func:`openquake.engine.input.source.nrml_to_hazardlib`.
    """
    for src_id in src_ids:
        parsed_source = models.ParsedSource.objects.get(id=src_id)

        hazardlib_source = source.nrml_to_hazardlib(
            parsed_source.nrml, rupture_mesh_spacing, width_of_mfd_bin,
            area_source_discretization)

        apply_uncertainties(hazardlib_source)
        yield hazardlib_source


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


def update_realization(lt_rlz_id, num_items):
    """
    Call this function when a task is complete to update realization counters
    with the ``num_items`` completed.

    If the `completed_items` becomes equal to the `total_items` for the
    realization, the realization will be marked as complete.

    .. note::
        Because this function performs a SELECT FOR UPDATE query, it is
        expected that this should be called in the context of a transaction, to
        avoid race conditions.

    :param int lt_rlz_id:
        ID of the :class:`openquake.engine.db.models.LtRealization` we want
        to update.
    :param int num_items:
        The number of items by which we want to increment the realization's
        `completed_items` counter.
    """
    ltr_query = """
    SELECT * FROM hzrdr.lt_realization
    WHERE id = %s
    FOR UPDATE
    """

    [lt_rlz] = models.LtRealization.objects.raw(
        ltr_query, [lt_rlz_id])

    lt_rlz.completed_items += num_items
    if lt_rlz.completed_items == lt_rlz.total_items:
        lt_rlz.is_complete = True

    lt_rlz.save()


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


def validate_site_model(sm_nodes, mesh):
    """Given the geometry for a site model and the geometry of interest for the
    calculation (``mesh``, make sure the geometry of interest lies completely
    inside of the convex hull formed by the site model locations.

    If a point of interest lies directly on top of a vertex or edge of the site
    model area (a polygon), it is considered "inside"

    :param sm_nodes:
        Sequence of :class:`~openquake.engine.db.models.SiteModel` objects.
    :param mesh:
        A :class:`openquake.hazardlib.geo.mesh.Mesh` which represents the
        calculation points of interest.

    :raises:
        :exc:`RuntimeError` if the area of interest (given as a mesh) is not
        entirely contained by the site model.
    """
    sm_mp = geometry.MultiPoint(
        [(n.location.x, n.location.y) for n in sm_nodes]
    )

    sm_ch = sm_mp.convex_hull
    # Enlarging the area if the site model nodes
    # create a straight line with zero area.
    if sm_ch.area == 0:
        sm_ch = sm_ch.buffer(DILATION_ONE_METER)

    sm_poly = hazardlib_geo.Polygon(
        [hazardlib_geo.Point(*x) for x in sm_ch.exterior.coords]
    )

    # "Intersects" is the correct operation (not "contains"), since we're just
    # checking a collection of points (mesh). "Contains" would tell us if the
    # points are inside the polygon, but would return `False` if a point was
    # directly on top of a polygon edge or vertex. We want these points to be
    # included.
    intersects = sm_poly.intersects(mesh)

    if not intersects.all():
        raise RuntimeError(
            ['Sites of interest are outside of the site model coverage area.'
             ' This configuration is invalid.']
        )


class BaseHazardCalculator(base.Calculator):
    """
    Abstract base class for hazard calculators. Contains a bunch of common
    functionality, like initialization procedures.
    """

    def __init__(self, *args, **kwargs):
        super(BaseHazardCalculator, self).__init__(*args, **kwargs)

        self.progress.update(in_queue=0)

    @property
    def hc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.engine.db.models.HazardCalculation`.
        """
        return self.job.hazard_calculation

    def block_size(self):
        """
        For hazard calculators, the number of work items per task
        is specified in the configuration file.
        """
        return int(config.get('hazard', 'block_size'))

    def point_source_block_size(self):
        """
        Similar to :meth:`block_size`, except that this parameter applies
        specifically to grouping of point sources.
        """
        return int(config.get('hazard', 'point_source_block_size'))

    def concurrent_tasks(self):
        """
        For hazard calculators, the number of tasks to be in queue
        at any given time is specified in the configuration file.
        """
        return int(config.get('hazard', 'concurrent_tasks'))

    def task_arg_gen(self, block_size, check_num_task=True):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        For this default implementation, yielded results are triples of
        (job_id, realization_id, source_id_list).

        Override this in subclasses as necessary.

        :param int block_size:
            The (max) number of work items for each each task. In this case,
            sources.
        """
        point_source_block_size = self.point_source_block_size()

        realizations = self._get_realizations()

        n = 0  # number of yielded arguments
        for lt_rlz in realizations:
            # separate point sources from all the other types, since
            # we distribution point sources in different sized chunks
            # point sources first
            point_source_ids = self._get_point_source_ids(lt_rlz)

            for block in block_splitter(point_source_ids,
                                        point_source_block_size):
                task_args = (self.job.id, block, lt_rlz.id)
                yield task_args
                n += 1
            # now for area and fault sources
            other_source_ids = self._get_source_ids(lt_rlz)

            for block in block_splitter(other_source_ids, block_size):
                task_args = (self.job.id, block, lt_rlz.id)
                yield task_args
                n += 1

        # this sanity check should go into a unit test, and will likely
        # go there in the future
        if check_num_task:
            num_tasks = models.JobStats.objects.get(
                oq_job=self.job.id).num_tasks
            assert num_tasks == n, 'Expected %d tasks, got %d' % (num_tasks, n)

    def _get_realizations(self):
        """
        Get all of the logic tree realizations for this calculation.
        """
        return models.LtRealization.objects\
            .filter(hazard_calculation=self.hc, is_complete=False)\
            .order_by('id')

    @staticmethod
    def _get_point_source_ids(lt_rlz):
        """
        Get `parsed_source` IDs for all of the point sources for a given logic
        tree realization. See also :meth:`_get_source_ids`.

        :param lt_rlz:
            A :class:`openquake.engine.db.models.LtRealization` instance.
        """
        return models.SourceProgress.objects\
            .filter(is_complete=False, lt_realization=lt_rlz,
                    parsed_source__source_type='point')\
            .order_by('id')\
            .values_list('parsed_source_id', flat=True)

    @staticmethod
    def _get_source_ids(lt_rlz):
        """
        Get `parsed_source` IDs for all sources for a given logic tree
        realization, except for point sources. See
        :meth:`_get_point_source_ids`.

        :param lt_rlz:
            A :class:`openquake.engine.db.models.LtRealization` instance.
        """
        return models.SourceProgress.objects\
            .filter(is_complete=False, lt_realization=lt_rlz,
                    parsed_source__source_type__in=['area',
                                                    'complex',
                                                    'simple',
                                                    'characteristic'])\
            .order_by('id')\
            .values_list('parsed_source_id', flat=True)

    def finalize_hazard_curves(self):
        """
        Create the final output records for hazard curves. This is done by
        copying the temporary results from `htemp.hazard_curve_progress` to
        `hzrdr.hazard_curve` (for metadata) and `hzrdr.hazard_curve_data` (for
        the actual curve PoE values). Foreign keys are made from
        `hzrdr.hazard_curve` to `hzrdr.lt_realization` (realization information
        is need to export the full hazard curve results).
        """
        im = self.hc.intensity_measure_types_and_levels
        points = self.hc.points_to_compute()

        # prepare site locations for the stored function call
        lons = '{%s}' % ', '.join(str(v) for v in points.lons)
        lats = '{%s}' % ', '.join(str(v) for v in points.lats)

        realizations = models.LtRealization.objects.filter(
            hazard_calculation=self.hc.id)

        for rlz in realizations:
            # create a new `HazardCurve` 'container' record for each
            # realization (virtual container for multiple imts)
            models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "hc-multi-imt-rlz-%s" % rlz.id,
                    "hazard_curve_multi"),
                lt_realization=rlz,
                imt=None,
                investigation_time=self.hc.investigation_time)

            # create a new `HazardCurve` 'container' record for each
            # realization for each intensity measure type
            for imt, imls in im.items():
                hc_im_type, sa_period, sa_damping = models.parse_imt(imt)

                hco = models.Output(
                    owner=self.hc.owner,
                    oq_job=self.job,
                    display_name="hc-rlz-%s" % rlz.id,
                    output_type='hazard_curve',
                )
                hco.save()

                haz_curve = models.HazardCurve(
                    output=hco,
                    lt_realization=rlz,
                    investigation_time=self.hc.investigation_time,
                    imt=hc_im_type,
                    imls=imls,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                )
                haz_curve.save()

                with transaction.commit_on_success(using='reslt_writer'):
                    cursor = connections['reslt_writer'].cursor()

                    # TODO(LB): I don't like the fact that we have to pass
                    # potentially huge arguments (100k sites, for example).
                    # I would like to be able to fetch this site data from
                    # the stored function, but at the moment, the only form
                    # available is a pickled `SiteCollection` object, and I've
                    # experienced problems trying to import third-party libs
                    # in a DB function context and could not get it to reliably
                    # work.
                    # As a fix, in addition to caching the pickled
                    # SiteCollection in the DB, we could store also arrays for
                    # lons and lats. It's duplicated information, but we have a
                    # relatively low number of HazardCalculation records, so it
                    # shouldn't be a big deal.
                    cursor.execute(
                        """
                        SELECT hzrdr.finalize_hazard_curves(
                            %s, %s, %s, %s, %s, %s)
                        """,
                        [self.hc.id, rlz.id, haz_curve.id, imt, lons, lats]
                    )

    @EnginePerformanceMonitor.monitor
    def initialize_sources(self):
        """
        Parse and validation logic trees (source and gsim). Then get all
        sources referenced in the the source model logic tree, create
        :class:`~openquake.engine.db.models.Input` records for all of them,
        parse then, and save the parsed sources to the `parsed_source` table
        (see :class:`openquake.engine.db.models.ParsedSource`).
        """
        logs.LOG.progress("initializing sources")

        [smlt] = models.inputs4hcalc(
            self.hc.id, input_type='source_model_logic_tree')
        [gsimlt] = models.inputs4hcalc(
            self.hc.id, input_type='gsim_logic_tree')

        source_paths = logictree.read_logic_trees_from_db(self.hc.id)

        for src_path in source_paths:
            full_path = os.path.join(self.hc.base_path, src_path)

            # Get the 'source' Input:
            inp = engine.get_or_create_input(
                full_path, 'source', self.hc.owner, haz_calc_id=self.hc.id
            )

            models.Src2ltsrc.objects.create(hzrd_src=inp, lt_src=smlt,
                                            filename=src_path)
            src_content = inp.model_content.as_string_io
            sm_parser = nrml_parsers.SourceModelParser(src_content)

            # Covert
            src_db_writer = source.SourceDBWriter(
                inp, sm_parser.parse(), self.hc.rupture_mesh_spacing,
                self.hc.width_of_mfd_bin,
                self.hc.area_source_discretization
            )
            src_db_writer.serialize()

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
        queryset = self.hc.inputs.filter(
            input_type__in=[vf_type
                            for vf_type, _desc
                            in models.Input.VULNERABILITY_TYPE_CHOICES])
        if queryset.exists():
            logs.LOG.progress("parsing risk models")

            hc.intensity_measure_types_and_levels = dict()
            hc.intensity_measure_types = list()

            for input_type in queryset:
                content = input_type.model_content.as_string_io
                intensity_measure_types_and_levels = dict(
                    (record['IMT'], record['IML']) for record in
                    parsers.VulnerabilityModelParser(content)
                )

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

        queryset = self.hc.inputs.filter(input_type='fragility')
        if queryset.exists():
            hc.intensity_measure_types_and_levels = dict()
            hc.intensity_measure_types = list()

            parser = iter(
                parsers.FragilityModelParser(
                    queryset.all()[0].model_content.as_string_io
                )
            )
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
        queryset = self.hc.inputs.filter(input_type='exposure')
        if queryset.exists():
            exposure_model_input = queryset.all()[0]
            content = exposure_model_input.model_content.as_string_io
            with logs.tracing('storing exposure'):
                exposure.ExposureDBWriter(
                    exposure_model_input).serialize(
                        parsers.ExposureModelParser(content))

    @EnginePerformanceMonitor.monitor
    def initialize_site_model(self):
        """
        If a site model is specified in the calculation configuration, parse
        it and load it into the `hzrdi.site_model` table. This includes a
        validation step to ensure that the area covered by the site model
        completely envelops the calculation geometry. (If this requirement is
        not satisfied, an exception will be raised. See
        :func:`openquake.engine.calculators.hazard.general.validate_site_model`.)
        """
        logs.LOG.progress("initializing site model")
        site_model_inp = models.get_site_model(self.hc.id)
        if site_model_inp:
            # Store `site_model` records:
            store_site_model(
                site_model_inp, site_model_inp.model_content.as_string_io
            )

            # Get the site model records we stored:
            site_model_data = models.SiteModel.objects.filter(
                input=site_model_inp)

            validate_site_model(
                site_model_data, self.hc.points_to_compute(save_sites=True)
            )
        else:
            self.hc.points_to_compute(save_sites=True)

    # Silencing 'Too many local variables'
    # pylint: disable=R0914
    @transaction.commit_on_success(using='reslt_writer')
    def initialize_realizations(self, rlz_callbacks=None):
        """
        Create records for the `hzrdr.lt_realization` and
        `htemp.source_progress` records.

        This function works either in random sampling mode (when lt_realization
        models get the random seed value) or in enumeration mode (when weight
        values are populated). In both cases we record the logic tree paths
        for both trees in the `lt_realization` record, as well as ordinal
        number of the realization (zero-based).

        Then we create `htemp.source_progress` records for each source
        in the source model chosen for each realization,
        see :meth:`initialize_source_progress`.

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

    def initialize_pr_data(self):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        stats.pk_set(self.job.id, "lvr", 0)
        rs = models.LtRealization.objects.filter(
            hazard_calculation=self.job.hazard_calculation)
        total = rs.aggregate(Sum("total_items"))
        done = rs.aggregate(Sum("completed_items"))
        stats.pk_set(self.job.id, "nhzrd_total", total.values().pop())
        if done > 0:
            stats.pk_set(self.job.id, "nhzrd_done", done.values().pop())

    def _initialize_realizations_enumeration(self, rlz_callbacks=None):
        """
        Perform full paths enumeration of logic trees and populate
        lt_realization table.

        :param rlz_callbacks:
            See :meth:`initialize_realizations` for more info.
        """
        hc = self.job.hazard_calculation
        [smlt] = models.inputs4hcalc(hc.id,
                                     input_type='source_model_logic_tree')
        ltp = logictree.LogicTreeProcessor(hc.id)
        hzrd_src_cache = {}

        for i, path_info in enumerate(ltp.enumerate_paths()):
            sm_name, weight, sm_lt_path, gsim_lt_path = path_info

            lt_rlz = models.LtRealization(
                hazard_calculation=hc,
                ordinal=i,
                seed=None,
                weight=weight,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # we will update total_items in initialize_source_progress()
                total_items=-1)
            lt_rlz.save()

            if not sm_name in hzrd_src_cache:
                # Get the source model for this sample:
                hzrd_src = models.Src2ltsrc.objects.get(
                    lt_src=smlt.id, filename=sm_name).hzrd_src
                # and cache it
                hzrd_src_cache[sm_name] = hzrd_src
            else:
                hzrd_src = hzrd_src_cache[sm_name]

            # Create source_progress objects
            self.initialize_source_progress(lt_rlz, hzrd_src)

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

        [smlt] = models.inputs4hcalc(self.hc.id,
                                     input_type='source_model_logic_tree')

        ltp = logictree.LogicTreeProcessor(self.hc.id)

        hzrd_src_cache = {}

        # The first realization gets the seed we specified in the config file.
        for i in xrange(self.hc.number_of_logic_tree_samples):
            # Sample source model logic tree branch paths:
            sm_name, sm_lt_path = ltp.sample_source_model_logictree(
                rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32))

            # Sample GSIM logic tree branch paths:
            gsim_lt_path = ltp.sample_gmpe_logictree(
                rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32))

            lt_rlz = models.LtRealization(
                hazard_calculation=self.hc,
                ordinal=i,
                seed=seed,
                weight=None,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # we will update total_items in initialize_source_progress()
                total_items=-1
            )
            lt_rlz.save()

            if not sm_name in hzrd_src_cache:
                # Get the source model for this sample:
                hzrd_src = models.Src2ltsrc.objects.get(
                    lt_src=smlt.id, filename=sm_name).hzrd_src
                # and cache it
                hzrd_src_cache[sm_name] = hzrd_src
            else:
                hzrd_src = hzrd_src_cache[sm_name]

            # Create source_progress objects
            self.initialize_source_progress(lt_rlz, hzrd_src)

            # Run realization callback (if any) to do additional initialization
            # for each realization:
            if rlz_callbacks is not None:
                for cb in rlz_callbacks:
                    cb(lt_rlz)

            # update the seed for the next realization
            seed = rnd.randint(models.MIN_SINT_32, models.MAX_SINT_32)
            rnd.seed(seed)

    @staticmethod
    def initialize_source_progress(lt_rlz, hzrd_src):
        """
        Create ``source_progress`` models for given logic tree realization
        and set total sources of realization.

        :param lt_rlz:
            :class:`openquake.engine.db.models.LtRealization` object to
            initialize source progress for.
        :param hztd_src:
            :class:`openquake.engine.db.models.Input` object that needed parsed
            sources are referencing.
        """
        cursor = connections['reslt_writer'].cursor()
        src_progress_tbl = models.SourceProgress._meta.db_table
        parsed_src_tbl = models.ParsedSource._meta.db_table
        lt_rlz_tbl = models.LtRealization._meta.db_table
        cursor.execute("""
            INSERT INTO "%s" (lt_realization_id, parsed_source_id, is_complete)
            SELECT %%s, id, FALSE
            FROM "%s" WHERE input_id = %%s
            ORDER BY id
            """ % (src_progress_tbl, parsed_src_tbl),
            [lt_rlz.id, hzrd_src.id])
        cursor.execute("""
            UPDATE "%s" SET total_items = (
                SELECT count(1) FROM "%s" WHERE lt_realization_id = %%s
            )""" % (lt_rlz_tbl, src_progress_tbl),
            [lt_rlz.id])
        transaction.commit_unless_managed()

    def initialize_hazard_curve_progress(self, lt_rlz):
        """
        As a calculation progresses, workers will periodically update the
        intermediate results. These results will be stored in
        `htemp.hazard_curve_progress` until the calculation is completed.

        Before the core calculation begins, we need to initalize these records,
        one data set per IMT. Each dataset will be stored in the database as a
        pickled 2D numpy array (with number of rows == calculation points of
        interest and number of columns == number of IML values for a given
        IMT).

        We will create 1 `hazard_curve_progress` record per IMT per
        realization.

        :param lt_rlz:
            :class:`openquake.engine.db.models.LtRealization` object to
            associate with these inital hazard curve values.
        """
        num_points = len(self.hc.points_to_compute())

        im_data = self.hc.intensity_measure_types_and_levels
        for imt, imls in im_data.items():
            hc_prog = models.HazardCurveProgress()
            hc_prog.lt_realization = lt_rlz
            hc_prog.imt = imt
            hc_prog.result_matrix = numpy.zeros((num_points, len(imls)))
            hc_prog.save()

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

    def record_init_stats(self):
        """
        Record some basic job stats, including the number of sites,
        realizations (end branches), and total number of tasks for the job.

        This should be run between the `pre-execute` and `execute` phases, once
        the job has been fully initialized.
        """
        # Record num sites, num realizations, and num tasks.
        num_sites = len(self.hc.points_to_compute())
        realizations = models.LtRealization.objects.filter(
            hazard_calculation=self.hc.id)
        num_rlzs = realizations.count()

        [job_stats] = models.JobStats.objects.filter(oq_job=self.job.id)
        job_stats.num_sites = num_sites
        job_stats.num_tasks = self.calc_num_tasks()
        job_stats.num_realizations = num_rlzs
        job_stats.save()

    def calc_num_tasks(self):
        """
        The number of tasks is inferred from the number of sources
        per realization by using the formula::

                     N * n   N * n0
         num_tasks = ----- + ------
                       b       b0

        where:

          N is the number of realizations
          n is the number of complex source
          n0 is the number of point sources
          b is the the block_size
          b0 is the the point_source_block_size

        The divisions are intended rounded to the closest upper integer
        (ceil).
        """
        num_tasks = 0
        block_size = self.block_size()
        point_source_block_size = self.point_source_block_size()
        total_sources = 0
        for lt_rlz in self._get_realizations():
            n = len(self._get_source_ids(lt_rlz))
            n0 = len(self._get_point_source_ids(lt_rlz))
            logs.LOG.debug('complex sources: %s, point sources: %d', n, n0)
            total_sources += n + n0
            ntasks = math.ceil(float(n) / block_size)
            ntasks0 = math.ceil(float(n0) / point_source_block_size)
            logs.LOG.debug(
                'complex sources tasks: %s, point sources tasks: %d',
                ntasks, ntasks0)
            num_tasks += ntasks + ntasks0
        logs.LOG.info('Total number of sources: %d', total_sources)
        return int(num_tasks)

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
                    display_name='mean-curves-%s' % imt,
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
                            'quantile(%s)-curves-%s' % (quantile, imt)
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

            with transaction.commit_on_success(using='reslt_writer'):
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
