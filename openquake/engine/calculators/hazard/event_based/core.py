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

"""
Core calculator functionality for computing stochastic event sets and ground
motion fields using the 'event-based' method.

Stochastic events sets (which can be thought of as collections of ruptures) are
computed iven a set of seismic sources and investigation time span (in years).

For more information on computing stochastic event sets, see
:mod:`openquake.hazardlib.calc.stochastic`.

One can optionally compute a ground motion field (GMF) given a rupture, a site
collection (which is a collection of geographical points with associated soil
parameters), and a ground shaking intensity model (GSIM).

For more information on computing ground motion fields, see
:mod:`openquake.hazardlib.calc.gmf`.
"""

import random

import openquake.hazardlib.imt
import numpy.random

from django.db import transaction
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc import gmf
from openquake.hazardlib.calc import stochastic
from openquake.hazardlib.geo import ComplexFaultSurface
from openquake.hazardlib.geo import MultiSurface
from openquake.hazardlib.geo import SimpleFaultSurface
from openquake.hazardlib.source import CharacteristicFaultSource
from openquake.hazardlib.source import ComplexFaultSource
from openquake.hazardlib.source import SimpleFaultSource

from openquake.engine import logs
from openquake.engine import writer
from openquake.engine.calculators import base
from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators.hazard.classical import (
    post_processing as cls_post_proc)
from openquake.engine.calculators.hazard.event_based import post_processing
from openquake.engine.db import models
from openquake.engine.input import logictree
from openquake.engine.utils import stats, tasks as utils_tasks
from openquake.engine.utils.general import block_splitter
from openquake.engine.performance import EnginePerformanceMonitor


#: Always 1 for the computation of ground motion fields in the event-based
#: hazard calculator.
DEFAULT_GMF_REALIZATIONS = 1


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@utils_tasks.oqtask
@stats.count_progress('h')
def ses_and_gmfs(job_id, src_ids, lt_rlz_id, task_seed, result_grp_ordinal):
    """
    Celery task for the stochastic event set calculator.

    Samples logic trees and calls the stochastic event set calculator.

    Once stochastic event sets are calculated, results will be saved to the
    database. See :class:`openquake.engine.db.models.SESCollection`.

    Optionally (specified in the job configuration using the
    `ground_motion_fields` parameter), GMFs can be computed from each rupture
    in each stochastic event set. GMFs are also saved to the database.

    Once all of this work is complete, a signal will be sent via AMQP to let
    the control noe know that the work is complete. (If there is any work left
    to be dispatched, this signal will indicate to the control node that more
    work can be enqueued.)

    :param int job_id:
        ID of the currently running job.
    :param src_ids:
        List of ids of parsed source models from which we will generate
        stochastic event sets/ruptures.
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param int task_seed:
        Value for seeding numpy/scipy in the computation of stochastic event
        sets and ground motion fields.
    :param int result_grp_ordinal:
        The result group in which the calculation results will be placed.
        This ID basically corresponds to the sequence number of the task,
        in the context of the entire calculation.
    """
    logs.LOG.debug(('> starting `stochastic_event_sets` task: job_id=%s, '
                    'lt_realization_id=%s') % (job_id, lt_rlz_id))

    # filtering sources
    with EnginePerformanceMonitor('filtering sources', job_id, ses_and_gmfs):

        numpy.random.seed(task_seed)

        hc = models.HazardCalculation.objects.get(oqjob=job_id)

        # filters
        ssd_filter = filters.source_site_distance_filter(hc.maximum_distance)
        rup_filter = filters.rupture_site_distance_filter(hc.maximum_distance)

        # complete_logic_tree_ses flag
        cmplt_lt_ses = None
        if hc.complete_logic_tree_ses:
            cmplt_lt_ses = models.SES.objects.get(
                ses_collection__output__oq_job=job_id,
                ordinal=None)

        lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)
        ltp = logictree.LogicTreeProcessor(hc.id)

        apply_uncertainties = ltp.parse_source_model_logictree_path(
            lt_rlz.sm_lt_path)

        gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

        sources = list(haz_general.gen_sources(
            src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
            hc.width_of_mfd_bin, hc.area_source_discretization))

        sources_sites = ((src, hc.site_collection) for src in sources)
        filtered_sources = [src for src, _ in ssd_filter(sources_sites)]

        logs.LOG.debug('Considering %d sources (of %d)',
                       len(filtered_sources), len(sources))

    filtered_away = 0  # ruptures filtered away by the maximum distance

    # Compute and save stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    for ses_rlz_n in xrange(1, hc.ses_per_logic_tree_path + 1):
        logs.LOG.debug('> computing stochastic event set %s of %s'
                       % (ses_rlz_n, hc.ses_per_logic_tree_path))

        # This is the container for all ruptures for this stochastic event set
        # (specified by `ordinal` and the logic tree realization).
        # NOTE: Many tasks can contribute ruptures to this SES.
        ses = models.SES.objects.get(
            ses_collection__lt_realization=lt_rlz, ordinal=ses_rlz_n)

        with EnginePerformanceMonitor('computing ses', job_id, ses_and_gmfs):
            all_ruptures = list(stochastic.stochastic_event_set_poissonian(
                                filtered_sources, hc.investigation_time))
            ruptures_sites = ((rupture, hc.site_collection)
                              for rupture in all_ruptures)
            filtered_ruptures = [rup for rup, _ in rup_filter(ruptures_sites)]

            filtered_away += len(all_ruptures) - len(filtered_ruptures)
            if not filtered_ruptures:
                continue

        logs.LOG.debug('Considering %d ruptures (of %d)',
                       len(filtered_ruptures), len(all_ruptures))

        with EnginePerformanceMonitor('saving ses', job_id, ses_and_gmfs):
            rupture_ids = [
                _save_ses_rupture(
                    ses, rupture, cmplt_lt_ses, result_grp_ordinal, i)
                for i, rupture in enumerate(filtered_ruptures, 1)]

        if hc.ground_motion_fields:
            with EnginePerformanceMonitor(
                    'computing gmfs', job_id, ses_and_gmfs):
                gmf_cache = compute_gmf_cache(
                    hc, gsims, filtered_ruptures, rupture_ids,
                    result_grp_ordinal)
            with EnginePerformanceMonitor('saving gmfs', job_id, ses_and_gmfs):
                # This will be the "container" for all computed GMFs
                # for this stochastic event set.
                gmf_set = models.GmfSet.objects.get(
                    gmf_collection__lt_realization=lt_rlz,
                    ses_ordinal=ses_rlz_n)
                _save_gmfs(gmf_set, gmf_cache, hc.points_to_compute(),
                           result_grp_ordinal)
    if filtered_away:
        logs.LOG.debug('%d rupture(s) filtered away by the maximum distance '
                       'criterium for set %d', filtered_away, ses_rlz_n)
    logs.LOG.debug('< task complete, signaling completion')
    base.signal_task_complete(job_id=job_id, num_items=len(src_ids))


def compute_gmf_cache(hc, gsims, ruptures, rupture_ids,
                      result_grp_ordinal):
    """
    Compute a ground motion field value for each rupture, for all the
    points affected by that rupture, for all IMTs.
    """
    imts = [haz_general.imt_to_hazardlib(x)
            for x in hc.intensity_measure_types]
    correl_model = None
    if hc.ground_motion_correlation_model is not None:
        correl_model = haz_general.get_correl_model(hc)

    n_points = len(hc.points_to_compute())

    # initialize gmf_cache, a dict imt -> {gmvs, rupture_ids}
    gmf_cache = dict((imt, dict(gmvs=numpy.empty((n_points, 0)),
                                rupture_ids=[]))
                     for imt in imts)

    for rupture, rupture_id in zip(ruptures, rupture_ids):

        # Compute and save ground motion fields
        gmf_calc_kwargs = {
            'rupture': rupture,
            'sites': hc.site_collection,
            'imts': imts,
            'gsim': gsims[rupture.tectonic_region_type],
            'truncation_level': hc.truncation_level,
            'realizations': DEFAULT_GMF_REALIZATIONS,
            'correlation_model': correl_model,
            'rupture_site_filter': filters.rupture_site_distance_filter(
                hc.maximum_distance),
        }
        gmf_dict = gmf.ground_motion_fields(**gmf_calc_kwargs)

        # update the gmf cache:
        for imt_key, v in gmf_dict.iteritems():
            gmf_cache[imt_key]['gmvs'] = numpy.append(
                gmf_cache[imt_key]['gmvs'], v, axis=1)
            gmf_cache[imt_key]['rupture_ids'].append(rupture_id)

    return gmf_cache


@transaction.commit_on_success(using='reslt_writer')
def _save_ses_rupture(ses, rupture, complete_logic_tree_ses,
                      result_grp_ordinal, rupture_ordinal):
    """
    Helper function for saving stochastic event set ruptures to the database.

    :param ses:
        A :class:`openquake.engine.db.models.SES` instance. This will be DB
        'container' for the new rupture record.
    :param rupture:
        A :class:`openquake.hazardlib.source.rupture.Rupture` instance.
    :param complete_logic_tree_ses:
        :class:`openquake.engine.db.models.SES` representing the `complete
        logic tree` stochastic event set.
        If not None, save a copy of the input `rupture` to this SES.
    :param int result_grp_ordinal:
        The result group in which the calculation results will be placed.
        This ID basically corresponds to the sequence number of the task,
        in the context of the entire calculation.
    :param int rupture_ordinal:
        The ordinal of a rupture with a given result group (indicated by
        ``result_grp_ordinal``).
    """
    is_from_fault_source = (
        rupture.source_typology in (ComplexFaultSource, SimpleFaultSource)
        or
        (rupture.source_typology is CharacteristicFaultSource
         and isinstance(rupture.surface, (ComplexFaultSurface,
                                          SimpleFaultSurface)))
    )
    is_multi_surface = False
    if (rupture.source_typology is CharacteristicFaultSource
            and isinstance(rupture.surface, MultiSurface)):
        is_multi_surface = True

    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = rupture.surface.get_mesh()
        lons = surf_mesh.lons
        lats = surf_mesh.lats
        depths = surf_mesh.depths
    else:
        if is_multi_surface:
            # `list` of openquake.hazardlib.geo.surface.planar.PlanarSurface
            # objects:
            surfaces = rupture.surface.surfaces

            # lons, lats, and depths are arrays with len == 4*N, where N is the
            # number of surfaces in the multisurface
            # for each `corner_*`, the ordering is:
            #   - top left
            #   - top right
            #   - bottom left
            #   - bottom right
            lons = numpy.concatenate([x.corner_lons for x in surfaces])
            lats = numpy.concatenate([x.corner_lats for x in surfaces])
            depths = numpy.concatenate([x.corner_depths for x in surfaces])
        else:
            # For area or point source,
            # rupture geometry is represented by a planar surface,
            # defined by 3D corner points
            surface = rupture.surface
            lons = numpy.zeros((4))
            lats = numpy.zeros((4))
            depths = numpy.zeros((4))

            # NOTE: It is important to maintain the order of these corner
            # points.
            # TODO: check the ordering
            for i, corner in enumerate((surface.top_left,
                                        surface.top_right,
                                        surface.bottom_left,
                                        surface.bottom_right)):
                lons[i] = corner.longitude
                lats[i] = corner.latitude
                depths[i] = corner.depth

    # TODO: Possible future optimiztion:
    # Refactor this to do bulk insertion of ruptures
    rupture_id = models.SESRupture.objects.create(
        ses=ses,
        magnitude=rupture.mag,
        strike=rupture.surface.get_strike(),
        dip=rupture.surface.get_dip(),
        rake=rupture.rake,
        surface=rupture.surface,
        tectonic_region_type=rupture.tectonic_region_type,
        is_from_fault_source=is_from_fault_source,
        is_multi_surface=is_multi_surface,
        lons=lons,
        lats=lats,
        depths=depths,
        result_grp_ordinal=result_grp_ordinal,
        rupture_ordinal=rupture_ordinal,
    ).id

    # FIXME(lp): do not save a copy. use the same approach used for
    # gmf and gmfset
    if complete_logic_tree_ses is not None:
        models.SESRupture.objects.create(
            ses=complete_logic_tree_ses,
            magnitude=rupture.mag,
            strike=rupture.surface.get_strike(),
            dip=rupture.surface.get_dip(),
            rake=rupture.rake,
            tectonic_region_type=rupture.tectonic_region_type,
            is_from_fault_source=is_from_fault_source,
            is_multi_surface=is_multi_surface,
            lons=lons,
            lats=lats,
            depths=depths,
            result_grp_ordinal=result_grp_ordinal,
            rupture_ordinal=rupture_ordinal,
        )

    return rupture_id


@transaction.commit_on_success(using='reslt_writer')
def _save_gmfs(gmf_set, gmf_dict, points_to_compute, result_grp_ordinal):
    """
    Helper method to save computed GMF data to the database.

    :param gmf_set:
        A :class:`openquake.engine.db.models.GmfSet` instance, which will be
        the "container" for these GMFs.
    :param dict gmf_dict:
        The dict used to cache/buffer up GMF results during the calculation.
    :param points_to_compute:
        An :class:`openquake.hazardlib.geo.mesh.Mesh` object, representing all
        of the points of interest for a calculation.
    :param int result_grp_ordinal:
        The sequence number (1 to N) of the task which computed these results.

        A calculation consists of N tasks, so this tells us which task computed
        the data.
    """

    inserter = writer.BulkInserter(models.Gmf)

    for imt, gmf_data in gmf_dict.iteritems():

        gmfs = gmf_data['gmvs']
        # ``gmfs`` and ``rupture_ids`` come in as a numpy.matrix and
        # a list. we want them as an array; it handles subscripting in
        # the way that we want
        gmfs = numpy.array(gmfs)
        rupture_ids = numpy.array(gmf_data['rupture_ids'])

        sa_period = None
        sa_damping = None
        if isinstance(imt, openquake.hazardlib.imt.SA):
            sa_period = imt.period
            sa_damping = imt.damping
        imt_name = imt.__class__.__name__

        for all_gmvs, location in zip(gmfs, points_to_compute):
            # take only the nonzero ground motion values and the
            # corresponding rupture ids
            nonzero_gmvs_idxs = numpy.where(all_gmvs != 0)
            gmvs = all_gmvs[nonzero_gmvs_idxs].tolist()
            relevant_rupture_ids = rupture_ids[nonzero_gmvs_idxs].tolist()

            if gmvs:
                inserter.add_entry(
                    gmf_set_id=gmf_set.id,
                    imt=imt_name,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                    location=location.wkt2d,
                    gmvs=gmvs,
                    rupture_ids=relevant_rupture_ids,
                    result_grp_ordinal=result_grp_ordinal,
                )

    inserter.flush()


class EventBasedHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """
    core_calc_task = ses_and_gmfs

    def task_arg_gen(self, block_size):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        Yielded results are quadruples of (job_id, realization_id,
        source_id_list, random_seed). (random_seed will be used to seed
        numpy for temporal occurence sampling.)

        :param int block_size:
            The (max) number of work items for each task. In this case,
            sources.
        """
        point_source_block_size = self.point_source_block_size()

        rnd = random.Random()
        rnd.seed(self.hc.random_seed)

        realizations = self._get_realizations()

        result_grp_ordinal = 1
        for lt_rlz in realizations:
            # separate point sources from all the other types, since
            # we distribution point sources in different sized chunks
            # point sources first
            point_source_ids = self._get_point_source_ids(lt_rlz)

            for block in block_splitter(point_source_ids,
                                        point_source_block_size):
                # Since this seed will used for numpy random seeding, it needs
                # to be positive (since numpy will convert it to a unsigned
                # long).
                task_seed = rnd.randint(0, models.MAX_SINT_32)
                task_args = (self.job.id, block, lt_rlz.id, task_seed,
                             result_grp_ordinal)
                yield task_args
                result_grp_ordinal += 1

            # now for area and fault sources
            other_source_ids = self._get_source_ids(lt_rlz)

            for block in block_splitter(other_source_ids, block_size):
                # Since this seed will used for numpy random seeding, it needs
                # to be positive (since numpy will convert it to a unsigned
                # long).
                task_seed = rnd.randint(0, models.MAX_SINT_32)
                task_args = (self.job.id, block, lt_rlz.id, task_seed,
                             result_grp_ordinal)
                yield task_args
                result_grp_ordinal += 1

    def initialize_ses_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.engine.db.models.Output`,
        :class:`~openquake.engine.db.models.SESCollection` and
        :class:`~openquake.engine.db.models.SES` "container" records for
        a single realization.

        Stochastic event set ruptures computed for this realization will be
        associated to these containers.
        """
        output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='ses-coll-rlz-%s' % lt_rlz.id,
            output_type='ses')

        ses_coll = models.SESCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        for i in xrange(1, self.hc.ses_per_logic_tree_path + 1):
            models.SES.objects.create(
                ses_collection=ses_coll,
                investigation_time=self.hc.investigation_time,
                ordinal=i)

    def initialize_complete_lt_ses_db_records(self):
        """
        Optional; if the user has requested to collect a `complete logic tree`
        stochastic event set (containing all ruptures from all realizations),
        initialize DB records for those results here.

        Throughout the course of the calculation, computed ruptures will be
        copied into this collection. See :func:`_save_ses_rupture` for more
        info.
        """
        # `complete logic tree` SES
        clt_ses_output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='complete logic tree SES',
            output_type='complete_lt_ses')

        clt_ses_coll = models.SESCollection.objects.create(
            output=clt_ses_output)

        investigation_time = self._compute_investigation_time(self.hc)

        models.SES.objects.create(
            ses_collection=clt_ses_coll,
            investigation_time=investigation_time)

    def initialize_complete_lt_gmf_db_records(self):
        """
        Optional; if the user has requested to collect a `complete logic tree`
        GMF set (containing all ground motion fields from all realizations),
        initialize DB records for those results here.

        Throughout the course of the calculation, computed GMFs will be copied
        into this collection. See :func:`_save_gmf_nodes` for more info.
        """
        # `complete logic tree` GMF
        clt_gmf_output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='complete logic tree GMF',
            output_type='complete_lt_gmf')

        gmf_coll = models.GmfCollection.objects.create(
            output=clt_gmf_output)

        investigation_time = self._compute_investigation_time(self.hc)

        models.GmfSet.objects.create(
            gmf_collection=gmf_coll,
            investigation_time=investigation_time)

    @staticmethod
    def _compute_investigation_time(haz_calc):
        """
        Helper method for :meth:`initialize_complete_lt_ses_db_records` and
        :meth:`initialize_complete_lt_gmf_db_records` to compute the
        investigation time for a given set of results.

        :param haz_calc:
            :class:`openquake.engine.db.models.HazardCalculation` object for
            the current job.
        """
        if haz_calc.number_of_logic_tree_samples > 0:
            # The calculation is set to do Monte-Carlo sampling of logic trees
            # The number of logic tree realizations is specified explicitly in
            # job configuration.
            n_lt_realizations = haz_calc.number_of_logic_tree_samples
        else:
            # The calculation is set do end-branch enumeration of all logic
            # tree paths
            # We can get the number of logic tree realizations by counting
            # initialized lt_realization records.
            n_lt_realizations = models.LtRealization.objects.filter(
                hazard_calculation=haz_calc.id).count()

        investigation_time = (haz_calc.investigation_time
                              * haz_calc.ses_per_logic_tree_path
                              * n_lt_realizations)

        return investigation_time

    def initialize_gmf_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.engine.db.models.Output`,
        :class:`~openquake.engine.db.models.GmfCollection` and
        :class:`~openquake.engine.db.models.GmfSet` "container" records for
        a single realization.

        GMFs for this realization will be associated to these containers.
        """
        output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='gmf-rlz-%s' % lt_rlz.id,
            output_type='gmf')

        gmf_coll = models.GmfCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        for i in xrange(1, self.hc.ses_per_logic_tree_path + 1):
            models.GmfSet.objects.create(
                gmf_collection=gmf_coll,
                investigation_time=self.hc.investigation_time,
                ses_ordinal=i)

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """

        # Parse risk models.
        self.parse_risk_models()

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        # Once the site model is init'd, create and cache the site collection;
        self.hc.init_site_collection()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        rlz_callbacks = [self.initialize_ses_db_records]
        if self.job.hazard_calculation.ground_motion_fields:
            rlz_callbacks.append(self.initialize_gmf_db_records)

        self.initialize_realizations(rlz_callbacks=rlz_callbacks)

        if self.job.hazard_calculation.complete_logic_tree_ses:
            self.initialize_complete_lt_ses_db_records()

        if self.job.hazard_calculation.complete_logic_tree_gmf:
            self.initialize_complete_lt_gmf_db_records()

        self.record_init_stats()

        num_sources = models.SourceProgress.objects.filter(
            is_complete=False,
            lt_realization__hazard_calculation=self.hc).count()
        self.progress['total'] = num_sources

        self.initialize_pr_data()

    def post_process(self):
        """
        If requested, perform additional processing of GMFs to produce hazard
        curves.
        """
        with EnginePerformanceMonitor(
                'populating gmf_agg', self.job.id, tracing=True):
            post_processing.populate_gmf_agg(self.job)

        if self.hc.hazard_curves_from_gmfs:
            with EnginePerformanceMonitor('generating hazard curves',
                                          self.job.id):
                post_processing.do_post_process(self.job)

            # If `mean_hazard_curves` is True and/or `quantile_hazard_curves`
            # has some value (not an empty list), do this additional
            # post-processing.
            if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
                with EnginePerformanceMonitor(
                        'generating mean/quantile curves', self.job.id):
                    self.do_aggregate_post_proc()

            if self.hc.hazard_maps:
                with EnginePerformanceMonitor(
                        'generating hazard maps', self.job.id):
                    cls_post_proc.do_hazard_map_post_process(self.job)
