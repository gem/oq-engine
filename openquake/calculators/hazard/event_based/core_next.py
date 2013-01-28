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
:mod:`nhlib.calc.stochastic`.

One can optionally compute a ground motion field (GMF) given a rupture, a site
collection (which is a collection of geographical points with associated soil
parameters), and a ground shaking intensity model (GSIM).

For more information on computing ground motion fields, see
:mod:`nhlib.calc.gmf`.
"""

import random

import nhlib.imt
import nhlib.source
import numpy.random

from django.db import transaction
from nhlib.calc import filters
from nhlib.calc import gmf as gmf_calc
from nhlib.calc import stochastic

from openquake import logs
from openquake import writer
from openquake.calculators import base
from openquake.calculators.hazard import general as haz_general
from openquake.calculators.hazard.classical import (
    post_processing as cls_post_processing)
from openquake.calculators.hazard.event_based import post_processing
from openquake.db import models
from openquake.db.aggregate_result_writer import MeanCurveWriter
from openquake.db.aggregate_result_writer import QuantileCurveWriter
from openquake.input import logictree
from openquake.job.validation import MAX_SINT_32
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks


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
    database. See :class:`openquake.db.models.SESCollection`.

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
    numpy.random.seed(task_seed)

    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    cmplt_lt_ses = None
    if hc.complete_logic_tree_ses:
        cmplt_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=job_id,
            complete_logic_tree_ses=True)

    if hc.ground_motion_fields:
        # For ground motion field calculation, we need the points of interest
        # for the calculation.
        points_to_compute = hc.points_to_compute()

        imts = [haz_general.imt_to_nhlib(x)
                for x in hc.intensity_measure_types]

        correl_model = None
        if hc.ground_motion_correlation_model is not None:
            correl_model = haz_general.get_correl_model(hc)

    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)
    ltp = logictree.LogicTreeProcessor(hc.id)

    apply_uncertainties = ltp.parse_source_model_logictree_path(
            lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

    sources = list(haz_general.gen_sources(
        src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
        hc.width_of_mfd_bin, hc.area_source_discretization))

    # Compute stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    for ses_rlz_n in xrange(1, hc.ses_per_logic_tree_path + 1):
        logs.LOG.debug('> computing stochastic event set %s of %s'
                       % (ses_rlz_n, hc.ses_per_logic_tree_path))

        # This is the container for all ruptures for this stochastic event set
        # (specified by `ordinal` and the logic tree realization).
        # NOTE: Many tasks can contribute ruptures to this SES.
        ses = models.SES.objects.get(
            ses_collection__lt_realization=lt_rlz, ordinal=ses_rlz_n)

        sources_sites = ((src, hc.site_collection) for src in sources)
        ssd_filter = filters.source_site_distance_filter(hc.maximum_distance)
        # Get the filtered sources, ignore the site collection:
        filtered_sources = (src for src, _ in ssd_filter(sources_sites))
        # Calculate stochastic event sets:
        logs.LOG.debug('> computing stochastic event sets')
        if hc.ground_motion_fields:
            gmf_cache = _create_gmf_cache(len(points_to_compute), imts)

            logs.LOG.debug('> computing also ground motion fields')
            # This will be the "container" for all computed ground motion field
            # results for this stochastic event set.
            gmf_set = models.GmfSet.objects.get(
                gmf_collection__lt_realization=lt_rlz, ses_ordinal=ses_rlz_n)

        ses_poissonian = stochastic.stochastic_event_set_poissonian(
            filtered_sources, hc.investigation_time)

        logs.LOG.debug('> looping over ruptures')
        rupture_ordinal = 0
        for rupture in ses_poissonian:
            rupture_ordinal += 1

            # Prepare and save SES ruptures to the db:
            logs.LOG.debug('> saving SES rupture to DB')
            _save_ses_rupture(
                ses, rupture, cmplt_lt_ses, result_grp_ordinal,
                rupture_ordinal)
            logs.LOG.debug('> done saving SES rupture to DB')

            # Compute ground motion fields (if requested)
            logs.LOG.debug('compute ground motion fields?  %s'
                           % hc.ground_motion_fields)
            if hc.ground_motion_fields:
                # Compute and save ground motion fields

                gmf_calc_kwargs = {
                    'rupture': rupture,
                    'sites': hc.site_collection,
                    'imts': imts,
                    'gsim': gsims[rupture.tectonic_region_type],
                    'truncation_level': hc.truncation_level,
                    'realizations': DEFAULT_GMF_REALIZATIONS,
                    'correlation_model': correl_model,
                    'rupture_site_filter':
                        filters.rupture_site_distance_filter(
                            hc.maximum_distance),
                }
                logs.LOG.debug('> computing ground motion fields')
                gmf_dict = gmf_calc.ground_motion_fields(**gmf_calc_kwargs)
                logs.LOG.debug('< done computing ground motion fields')

                # update the gmf cache:
                for k, v in gmf_dict.iteritems():
                    gmf_cache[k] = numpy.append(
                        gmf_cache[k], v, axis=1)

        logs.LOG.debug('< Done looping over ruptures')
        logs.LOG.debug('%s ruptures computed for SES realization %s of %s'
                       % (rupture_ordinal, ses_rlz_n,
                          hc.ses_per_logic_tree_path))
        logs.LOG.debug('< done computing stochastic event set %s of %s'
                       % (ses_rlz_n, hc.ses_per_logic_tree_path))

        if hc.ground_motion_fields:
            # save the GMFs to the DB
            logs.LOG.debug('> saving GMF results to DB')
            _save_gmfs(
                gmf_set, gmf_cache, points_to_compute, result_grp_ordinal)
            logs.LOG.debug('< done saving GMF results to DB')

    logs.LOG.debug('< task complete, signalling completion')
    base.signal_task_complete(job_id=job_id, num_items=len(src_ids))


def _create_gmf_cache(n_sites, imts):
    """
    Create a `dict` to cache GMF data during the course of a computation.

    The `dict` is keyed by IMTs (which are IMT objects from :mod:`nhlib.imt`).
    Each value is initialized to a numpy array with a shape of (n, 0), where n
    is `n_sites`.

    :param int n_sites:
        The number of sites in the calculation.
    :param imts:
        A `list` or other sequence of :mod:`nhlib.imt` IMT objects.
    """
    cache = dict()

    for imt in imts:
        cache[imt] = numpy.empty((n_sites, 0))

    return cache


def _save_ses_rupture(ses, rupture, complete_logic_tree_ses,
                      result_grp_ordinal, rupture_ordinal):
    """
    Helper function for saving stochastic event set ruptures to the database.

    :param ses:
        A :class:`openquake.db.models.SES` instance. This will be DB
        'container' for the new rupture record.
    :param rupture:
        A :class:`nhlib.source.rupture.Rupture` instance.
    :param complete_logic_tree_ses:
        :class:`openquake.db.models.SES` representing the `complete logic tree`
        stochastic event set.
        If not None, save a copy of the input `rupture` to this SES.
    :param int result_grp_ordinal:
        The result group in which the calculation results will be placed.
        This ID basically corresponds to the sequence number of the task,
        in the context of the entire calculation.
    :param int rupture_ordinal:
        The ordinal of a rupture with a given result group (inidicated by
        ``result_grp_ordinal``).
    """
    is_from_fault_source = rupture.source_typology in (
        nhlib.source.ComplexFaultSource,
        nhlib.source.SimpleFaultSource)

    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = rupture.surface.get_mesh()
        lons = surf_mesh.lons
        lats = surf_mesh.lats
        depths = surf_mesh.depths
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
        for i, corner in enumerate((surface.top_left,
                                    surface.top_right,
                                    surface.bottom_right,
                                    surface.bottom_left)):
            lons[i] = corner.longitude
            lats[i] = corner.latitude
            depths[i] = corner.depth

    # TODO: Possible future optimiztion:
    # Refactor this to do bulk insertion of ruptures
    models.SESRupture.objects.create(
        ses=ses,
        magnitude=rupture.mag,
        strike=rupture.surface.get_strike(),
        dip=rupture.surface.get_dip(),
        rake=rupture.rake,
        tectonic_region_type=rupture.tectonic_region_type,
        is_from_fault_source=is_from_fault_source,
        lons=lons,
        lats=lats,
        depths=depths,
        result_grp_ordinal=result_grp_ordinal,
        rupture_ordinal=rupture_ordinal,
    )
    if complete_logic_tree_ses is not None:
        models.SESRupture.objects.create(
            ses=complete_logic_tree_ses,
            magnitude=rupture.mag,
            strike=rupture.surface.get_strike(),
            dip=rupture.surface.get_dip(),
            rake=rupture.rake,
            tectonic_region_type=rupture.tectonic_region_type,
            is_from_fault_source=is_from_fault_source,
            lons=lons,
            lats=lats,
            depths=depths,
            result_grp_ordinal=result_grp_ordinal,
            rupture_ordinal=rupture_ordinal,
        )


@transaction.commit_on_success(using='reslt_writer')
def _save_gmfs(gmf_set, gmf_dict, points_to_compute, result_grp_ordinal):
    """
    Helper method to save computed GMF data to the database.

    :param gmf_set:
        A :class:`openquake.db.models.GmfSet` instance, which will be the
        "container" for these GMFs.
    :param dict gmf_dict:
        The dict use to cache/buffer up GMF results during the calculation.
        See :func:`_create_gmf_cache`.
    :param points_to_compute:
        An :class:`nhlib.geo.mesh.Mesh` object, representing all of the points
        of interest for a calculation.
    :param int result_grp_ordinal:
        The sequence number (1 to N) of the task which computed these results.

        A calculation consists of N tasks, so this tells us which task computed
        the data.
    """
    inserter = writer.BulkInserter(models.Gmf)

    for imt, gmfs in gmf_dict.iteritems():

        # ``gmfs`` comes in as a numpy.matrix
        # we want it is an array; it handles subscripting
        # in the way that we want
        gmfs = numpy.array(gmfs)

        sa_period = None
        sa_damping = None
        if isinstance(imt, nhlib.imt.SA):
            sa_period = imt.period
            sa_damping = imt.damping
        imt_name = imt.__class__.__name__

        for i, location in enumerate(points_to_compute):
            inserter.add_entry(
                gmf_set_id=gmf_set.id,
                imt=imt_name,
                sa_period=sa_period,
                sa_damping=sa_damping,
                location=location.wkt2d,
                gmvs=gmfs[i].tolist(),
                result_grp_ordinal=result_grp_ordinal,
            )

    inserter.flush()


def _create_gmf_record(gmf_set, imt):
    """
    Helper function to create :class:`openquake.db.models.Gmf` records. The
    record will be saved to the DB and returned.

    :param gmf_set:
        :class:`openquake.db.models.GmfSet` instance.
    :param imt:
        An instance of one of the IMT classes defined in :mod:`nhlib.imt`.

    :returns:
        The newly created :class:`openquake.db.models.Gmf` object.
    """
    gmf = models.Gmf(
        gmf_set=gmf_set, imt=imt.__class__.__name__)

    if isinstance(imt, nhlib.imt.SA):
        gmf.sa_period = imt.period
        gmf.sa_damping = imt.damping

    gmf.save()
    return gmf


class EventBasedHazardCalculator(haz_general.BaseHazardCalculatorNext):
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
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)

        realizations = models.LtRealization.objects.filter(
                hazard_calculation=self.hc, is_complete=False).order_by('id')

        result_grp_ordinal = 1
        for lt_rlz in realizations:
            source_progress = models.SourceProgress.objects.filter(
                    is_complete=False, lt_realization=lt_rlz).order_by('id')
            source_ids = source_progress.values_list('parsed_source_id',
                                                     flat=True)

            for offset in xrange(0, len(source_ids), block_size):
                # Since this seed will used for numpy random seeding, it needs
                # to be positive (since numpy will convert it to a unsigned
                # long).
                task_seed = rnd.randint(0, MAX_SINT_32)
                task_args = (
                    self.job.id,
                    source_ids[offset:offset + block_size],
                    lt_rlz.id,
                    task_seed,
                    result_grp_ordinal
                )
                yield task_args
                result_grp_ordinal += 1

    def initialize_ses_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.db.models.Output`,
        :class:`~openquake.db.models.SESCollection` and
        :class:`~openquake.db.models.SES` "container" records for a single
        realization.

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
            output=clt_ses_output, complete_logic_tree_ses=True)

        investigation_time = self._compute_investigation_time(self.hc)

        models.SES.objects.create(
            ses_collection=clt_ses_coll,
            investigation_time=investigation_time,
            complete_logic_tree_ses=True)

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
            output=clt_gmf_output, complete_logic_tree_gmf=True)

        investigation_time = self._compute_investigation_time(self.hc)

        models.GmfSet.objects.create(
            gmf_collection=gmf_coll,
            investigation_time=investigation_time,
            complete_logic_tree_gmf=True)

    @staticmethod
    def _compute_investigation_time(haz_calc):
        """
        Helper method for :meth:`initialize_complete_lt_ses_db_records` and
        :meth:`initialize_complete_lt_gmf_db_records` to compute the
        investigation time for a given set of results.

        :param haz_calc:
            :class:`openquake.db.models.HazardCalculation` object for the
            current job.
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
        Create :class:`~openquake.db.models.Output`,
        :class:`~openquake.db.models.GmfCollection` and
        :class:`~openquake.db.models.GmfSet` "container" records for a single
        realization.

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
        Do pre-execution work. At the moment, this work entails: parsing and
        initializing sources, parsing and initializing the site model (if there
        is one), and generating logic tree realizations. (The latter piece
        basically defines the work to be done in the `execute` phase.)
        """

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

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
        logs.LOG.debug('> starting post processing')

        if self.hc.hazard_curves_from_gmfs:
            post_processing.do_post_process(self.job)

            # If `mean_hazard_curves` is True and/or `quantile_hazard_curves`
            # has some value (not an empty list), do this additional
            # post-processing.
            if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
                tasks = cls_post_processing.setup_tasks(
                    self.job, self.job.hazard_calculation,
                    curve_finder=models.HazardCurveData.objects,
                    writers=dict(mean_curves=MeanCurveWriter,
                                 quantile_curves=QuantileCurveWriter))

                utils_tasks.distribute(
                        cls_post_processing.do_post_process,
                        ("post_processing_task", tasks),
                        tf_args=dict(job_id=self.job.id))

        logs.LOG.debug('< done with post processing')
