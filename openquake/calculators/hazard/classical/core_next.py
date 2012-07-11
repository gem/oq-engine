# Copyright (c) 2010-2012, GEM Foundation.
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
Core functionality for the classical PSHA hazard calculator.
"""

import numpy
import os
import random
import re
import StringIO

import kombu
import nhlib
import nhlib.calc
import nhlib.imt
import nhlib.site

from django.db import transaction
from nrml import parsers as nrml_parsers

from openquake import engine2
from openquake import logs
from openquake import writer
from openquake.calculators import base
from openquake.calculators.hazard import general
from openquake.db import models
from openquake.input import logictree
from openquake.input import source
from openquake.job.validation import MAX_SINT_32
from openquake.job.validation import MIN_SINT_32
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

#: Default Spectral Acceleration damping. At the moment, this is not
#: configurable.
DEFAULT_SA_DAMPING = 5.0
# Routing key format string for communication between tasks and the control
# node.
_ROUTING_KEY_FMT = 'oq.job.%(job_id)s.htasks'


class ClassicalHazardCalculator(base.CalculatorNext):
    """
    Classical PSHA hazard calculator. Computes hazard curves for a given set of
    points.

    For each realization of the calculation, we randomly sample source models
    and GMPEs (Ground Motion Prediction Equations) from logic trees.
    """

    def initialize_site_model(self):
        """
        If a site model is specified in the calculation configuration. parse
        it and load it into the `hzrdi.site_model` table. This includes a
        validation step to ensure that the area covered by the site model
        completely envelops the calculation geometry. (If this requirement is
        not satisfied, an exception will be raised. See
        :func:`openquake.calculators.hazard.general.validate_site_model`.)

        Then, take all of the points/locations of interest defined by the
        calculation geometry. For each point, do distance queries on the site
        model and get the site parameters which are closest to the point of
        interest. This aggregation of points to the closest site parameters
        is what we store in `htemp.site_data`. (Computing this once prior to
        starting the calculation is optimal, since each task will need to
        consider all sites.)
        """
        hc_id = self.job.hazard_calculation.id

        site_model_inp = general.get_site_model(hc_id)
        if site_model_inp is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model_inp.model_content.raw_content)

            # Store `site_model` records:
            general.store_site_model(
                site_model_inp, StringIO.StringIO(site_model_content))

            mesh = self.job.hazard_calculation.points_to_compute()

            # Get the site model records we stored:
            site_model_data = models.SiteModel.objects.filter(
                input=site_model_inp)

            general.validate_site_model(site_model_data, mesh)

            general.store_site_data(hc_id, site_model_inp, mesh)

    def initialize_sources(self):
        """
        Parse and validation logic trees (source and gsim). Then get all
        sources referenced in the the source model logic tree, create
        :class:`~openquake.db.models.Input` records for all of them, parse
        then, and save the parsed sources to the `parsed_source` table
        (see :class:`openquake.db.models.ParsedSource`).
        """
        hc = self.job.hazard_calculation

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')
        [gsimlt] = models.inputs4hcalc(hc.id, input_type='lt_gsim')
        source_paths = logictree.read_logic_trees(
            hc.base_path, smlt.path, gsimlt.path)

        src_inputs = []
        for src_path in source_paths:
            full_path = os.path.join(hc.base_path, src_path)

            # Get or reuse the 'source' Input:
            inp = engine2.get_input(
                full_path, 'source', hc.owner, hc.force_inputs)
            src_inputs.append(inp)

            # Associate the source input to the calculation:
            models.Input2hcalc.objects.get_or_create(
                input=inp, hazard_calculation=hc)

            # Associate the source input to the source model logic tree input:
            models.Src2ltsrc.objects.get_or_create(
                hzrd_src=inp, lt_src=smlt, filename=src_path)

        # Now parse the source models and store `pared_source` records:
        for src_inp in src_inputs:
            src_content = StringIO.StringIO(src_inp.model_content.raw_content)
            sm_parser = nrml_parsers.SourceModelParser(src_content)
            src_db_writer = source.SourceDBWriter(
                src_inp, sm_parser.parse(), hc.rupture_mesh_spacing,
                hc.width_of_mfd_bin, hc.area_source_discretization)
            src_db_writer.serialize()

    # Silencing 'Too many local variables'
    # pylint: disable=R0914
    @transaction.commit_on_success(using='reslt_writer')
    def initialize_realizations(self):
        """
        Create records for the `hzrdr.lt_realization` and
        `htemp.source_progress` records. To do this, we sample the source model
        logic tree to choose a source model for the realization, then we sample
        the GSIM logic tree. We record the logic tree paths for both trees in
        the `lt_realization` record.

        Then we create `htemp.source_progress` records for each source in the
        source model chosen for each realization.
        """
        hc = self.job.hazard_calculation

        # Each realization will have two seeds:
        # One for source model logic tree, one for GSIM logic tree.
        rnd = random.Random()
        seed = hc.random_seed
        rnd.seed(seed)

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')

        ltp = logictree.LogicTreeProcessor(hc.id)

        # The first realization gets the seed we specified in the config file.
        for i in xrange(hc.number_of_logic_tree_samples):
            lt_rlz = models.LtRealization(hazard_calculation=hc)
            lt_rlz.ordinal = i
            lt_rlz.seed = seed

            # Sample source model logic tree branch paths:
            sm_name, _, sm_lt_branch_ids = ltp.sample_source_model_logictree(
                rnd.randint(MIN_SINT_32, MAX_SINT_32))
            lt_rlz.sm_lt_path = sm_lt_branch_ids

            # Sample GSIM logic tree branch paths:
            _, gsim_branch_ids = ltp.sample_gmpe_logictree(
                rnd.randint(MIN_SINT_32, MAX_SINT_32))
            lt_rlz.gsim_lt_path = gsim_branch_ids

            # Get the source model for this sample:
            hzrd_src = models.Src2ltsrc.objects.get(
                lt_src=smlt.id, filename=sm_name).hzrd_src
            parsed_sources = models.ParsedSource.objects.filter(input=hzrd_src)

            lt_rlz.total_sources = len(parsed_sources)
            lt_rlz.save()

            # Create source_progress for this realization
            # A bulk insert is more efficient because there could be lots of
            # of individual sources.
            sp_inserter = writer.BulkInserter(models.SourceProgress)
            for ps in parsed_sources:
                sp_inserter.add_entry(
                    lt_realization_id=lt_rlz.id, parsed_source_id=ps.id)
            sp_inserter.flush()

            # Now stub out the curve result records for this realization:
            self.initialize_hazard_curve_progress(lt_rlz)

            # update the seed for the next realization
            seed = rnd.randint(MIN_SINT_32, MAX_SINT_32)
            rnd.seed(seed)

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
            :class:`openquake.db.models.LtRealization` object to associate
            with these inital hazard curve values.
        """
        hc = self.job.hazard_calculation

        num_points = len(hc.points_to_compute())

        im_data = hc.intensity_measure_types_and_levels
        for imt, imls in im_data.items():
            hc_prog = models.HazardCurveProgress()
            hc_prog.lt_realization = lt_rlz
            hc_prog.imt = imt
            hc_prog.result_matrix = numpy.zeros((num_points, len(imls)))
            hc_prog.save()

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
        # (if a site model was specified, that is).
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        # This will also stub out hazard curve result records. Workers will
        # update these periodically with partial results (partial meaning,
        # result curves for just a subset of the overall sources) when some
        # work is complete.
        self.initialize_realizations()

    def execute(self):
        """
        Calculation work is parallelized over sources, which means that each
        task will compute hazard for all sites but only with a subset of the
        seismic sources defined in the input model.

        The general workflow is as follows:

        1. Fill the queue with an initial set of tasks. The number of initial
        tasks is configurable using the `concurrent_tasks` parameter in the
        `[hazard]` section of the OpenQuake config file.

        2. Wait for tasks to signal completion (via AMQP message) and enqueue a
        new task each time another completes. Once all of the job work is
        enqueued, we just wait until all of the tasks conclude.
        """
        # TODO: unittest
        # TODO: Fix deadlocking of execute method when tasks encounter
        # exceptions. Perhaps put in a try/except in the task and signal back
        # the failure (via amqp)?
        job = self.job
        hc = job.hazard_calculation
        sources_per_task = int(config.get('hazard', 'block_size'))
        concurrent_tasks = int(config.get('hazard', 'concurrent_tasks'))

        # The following two counters are dicts so that we can use them in the
        # closures below:
        total_sources_to_compute = dict(value=0)
        # When `sources_computed` becomes equal to `total_sources_to_compute`,
        # `execute` can conclude.
        sources_computed = dict(value=0)

        def task_complete_callback(body, message):
            """
            :param dict body:
                ``body`` is the message sent by the task. The dict should
                contain 2 keys: `job_id` and `num_sources` (to indicate the
                number of sources computed).

                Both values are `int`.
            :param message:
                A :class:`kombu.transport.pyamqplib.Message`, which contains
                metadata about the message (including content type, channel,
                etc.). See kombu docs for more details.
            """
            job_id = body['job_id']
            num_sources = body['num_sources']

            assert job_id == job.id
            sources_computed['value'] += num_sources

            # TODO: do we actually need the ack?
            message.ack()

        def task_arg_gen():
            """
            Loop through realizations and sources to generate a sequence of
            task arg tuples. Each tuple of args applies to a single task.

            Yielded results are triples of (job_id, realization_id,
            source_id_list).
            """
            realizations = models.LtRealization.objects.filter(
                    hazard_calculation=hc, is_complete=False)

            for lt_rlz in realizations:
                source_progress = models.SourceProgress.objects.filter(
                        is_complete=False, lt_realization=lt_rlz)
                source_ids = source_progress.values_list('parsed_source_id',
                                                         flat=True)
                total_sources_to_compute['value'] += len(source_ids)

                for offset in xrange(0, len(source_ids), sources_per_task):
                    task_args = (job.id, lt_rlz.id,
                                 source_ids[offset:offset + sources_per_task])
                    yield task_args

        task_gen = task_arg_gen()
        # First: Queue up the initial tasks.
        for _ in xrange(concurrent_tasks):
            try:
                hazard_curves.apply_async(task_gen.next())
            except StopIteration:
                # If we get a `StopIteration` here, that means we have a number
                # of tasks < concurrent_tasks.
                # This basically just means that we could be under-utilizing
                # worker node resources.
                break

        exchange = kombu.Exchange(
            config.get_section('hazard')['task_exchange'], type='direct')

        routing_key = _ROUTING_KEY_FMT % dict(job_id=job.id)
        task_signal_queue = kombu.Queue(
            'htasks.job.%s' % job.id, exchange=exchange,
            routing_key=routing_key)

        amqp_cfg = config.get_section('amqp')
        conn_args = {
            'hostname': amqp_cfg['host'],
            'userid': amqp_cfg['user'],
            'password': amqp_cfg['password'],
            'virtual_host': amqp_cfg['vhost'],
        }

        while (sources_computed['value']
               < total_sources_to_compute['value']):

            with kombu.BrokerConnection(**conn_args) as conn:
                task_signal_queue(conn.channel()).declare()
                with conn.Consumer(task_signal_queue,
                                   callbacks=[task_complete_callback]):
                    # This blocks until a message is received.
                    conn.drain_events()

                    # Once we receive a completion signal, enqueue the next
                    # piece of work (if there's anything left to be done).
                    try:
                        hazard_curves.apply_async(task_gen.next())
                    except StopIteration:
                        # There are no more tasks to dispatch; now we just need
                        # to wait until all tasks signal completion.
                        pass

    def post_execute(self):
        """
        Create the final output records for
        """
        # TODO: better doc
        hc = self.job.hazard_calculation
        im = hc.intensity_measure_types_and_levels
        points = hc.points_to_compute()

        realizations = models.LtRealization.objects.filter(
            hazard_calculation=hc.id)

        for rlz in realizations:
            # create a new `HazardCurve` 'container' record for each
            # realization for each intensity measure type
            for imt, imls in im.items():
                sa_period = None
                sa_damping = None
                if 'SA' in imt:
                    match = re.match(r'^SA\((.+?)\)$', imt)
                    sa_period = float(match.group(1))
                    sa_damping = DEFAULT_SA_DAMPING
                    hc_im_type = 'SA'  # don't include the period
                else:
                    hc_im_type = imt

                # TODO: create an `Output` record here as well
                # with type == 'hazard_curve'
                hco = models.Output(
                    owner=hc.owner,
                    oq_job=self.job,
                    display_name="",  # TODO: good display name
                    output_type='hazard_curve',
                )
                hco.save()

                haz_curve = models.HazardCurve(
                    output=hco,
                    lt_realization=rlz,
                    investigation_time=hc.investigation_time,
                    imt=hc_im_type,
                    imls=imls,
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                )
                haz_curve.save()

                [hc_progress] = models.HazardCurveProgress.objects.filter(
                    lt_realization=rlz.id, imt=imt)

                for i, poes in enumerate(hc_progress.result_matrix):
                    # TODO: Bulk insert HazardCurveData
                    [location] = points[i:i + 1]
                    haz_curve_data = models.HazardCurveData(
                        hazard_curve=haz_curve,
                        poes=poes,
                        location=location.wkt2d
                    )
                    haz_curve_data.save()


@utils_tasks.oqtask
@stats.progress_indicator('h')
def hazard_curves(job_id, lt_rlz_id, src_ids):
    """
    Celery task for hazard curve calculator.

    Samples logic trees, gathers site parameters, and calls the hazard curve
    calculator.

    Once hazard curve data is computed, result progress updated (within a
    transaction, to prevent race conditions) in the
    `htemp.hazard_curve_progress` table.

    Once all of this work is complete, a signal will be sent via AMQP to let
    the control node know that the work is complete. (If there is any work left
    to be dispatched, this signal will indicate to the control node that more
    work can be enqueued.)

    :param int job_id:
        ID of the currently running job.
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param src_ids:
        List of ids of parsed source models to take into account.
    """
    logs.LOG.debug('> starting task: job_id=%s, lt_realization_id=%s'
                   % (job_id, lt_rlz_id))

    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    lt_rlz = models.LtRealization.objects.get(pk=lt_rlz_id)
    ltp = logictree.LogicTreeProcessor(hc.id)

    # it is important to maintain the same way logic tree processor
    # random generators are seeded here exactly the same as it is
    # done in ClassicalHazardCalculator.initialize_realizations()
    rnd = random.Random(lt_rlz.seed)
    _, apply_uncertainties, _ = ltp.sample_source_model_logictree(
            rnd.randint(MIN_SINT_32, MAX_SINT_32))
    gsims, _ = ltp.sample_gmpe_logictree(
            rnd.randint(MIN_SINT_32, MAX_SINT_32))

    def gen_sources():
        """
        Nhlib source objects generator for a given set of sources.

        Performs lazy loading, converting and processing of sources.
        """
        for src_id in src_ids:
            parsed_source = models.ParsedSource.objects.get(pk=src_id)

            nhlib_source = source.nrml_to_nhlib(
                parsed_source.nrml, hc.rupture_mesh_spacing,
                hc.width_of_mfd_bin, hc.area_source_discretization)

            apply_uncertainties(nhlib_source)
            yield nhlib_source

    imts = im_dict_to_nhlib(hc.intensity_measure_types_and_levels)

    # Now initialize the site collection for use in the calculation.
    # If there is no site model defined, we will use the same reference
    # parameters (defined in the HazardCalculation) for every site.
    logs.LOG.debug('> creating site collection')
    site_data = models.SiteData.objects.filter(hazard_calculation=hc.id)
    if len(site_data) > 0:
        site_data = site_data[0]
        sites = zip(site_data.lons, site_data.lats, site_data.vs30s,
                    site_data.vs30_measured, site_data.z1pt0s,
                    site_data.z2pt5s)
        sites = [nhlib.site.Site(
            nhlib.geo.Point(lon, lat), vs30, vs30m, z1pt0, z2pt5)
            for lon, lat, vs30, vs30m, z1pt0, z2pt5 in sites]
    else:
        # Use the calculation reference parameters to make a site collection.
        points = hc.points_to_compute()
        measured = hc.reference_vs30_type == 'measured'
        sites = [
            nhlib.site.Site(pt, hc.reference_vs30_value, measured,
                            hc.reference_depth_to_2pt5km_per_sec,
                            hc.reference_depth_to_1pt0km_per_sec)
            for pt in points]
    site_coll = nhlib.site.SiteCollection(sites)
    logs.LOG.debug('< done creating site collection')

    # Prepare args for the calculator.
    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': gen_sources(),
                   'imts': imts,
                   'sites': site_coll}

    if hc.maximum_distance:
        dist = hc.maximum_distance
        calc_kwargs['source_site_filter'] = (
                nhlib.calc.filters.source_site_distance_filter(dist))
        calc_kwargs['rupture_site_filter'] = (
                nhlib.calc.filters.rupture_site_distance_filter(dist))

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    logs.LOG.debug('> computing hazard matrices')
    matrices = nhlib.calc.hazard_curve.hazard_curves_poissonian(**calc_kwargs)
    logs.LOG.debug('< done computing hazard matrices')

    logs.LOG.debug('> starting transaction')
    with transaction.commit_on_success():
        logs.LOG.debug('looping over IMTs')
        for imt in hc.intensity_measure_types_and_levels.keys():
            logs.LOG.debug('> updating hazard for IMT=%s' % imt)
            nhlib_imt = _imt_to_nhlib(imt)
            query = """
            SELECT * FROM htemp.hazard_curve_progress
            WHERE lt_realization_id = %s
            AND imt = %s
            FOR UPDATE"""
            [hc_progress] = models.HazardCurveProgress.objects.raw(
                query, [lt_rlz.id, imt])

            # TODO: check here if any of records in source progress model
            # with parsed_source_id from src_ids are marked as complete,
            # and rollback and abort if there is at least one

            hc_progress.result_matrix = (
                1 - (1 - hc_progress.result_matrix)
                * (1 - matrices[nhlib_imt]))
            hc_progress.save()

            models.SourceProgress.objects.filter(lt_realization=lt_rlz,
                                                 parsed_source__in=src_ids) \
                                         .update(is_complete=True)

            lt_rlz.completed_sources += len(src_ids)
            if lt_rlz.completed_sources == lt_rlz.total_sources:
                lt_rlz.is_complete = True

            lt_rlz.save()
            logs.LOG.debug('< done updating hazard for IMT=%s' % imt)
    logs.LOG.debug('< transaction complete')

    # Last thing, signal back the control node to indicate the completion of
    # task. The control node needs this to manage the task distribution and
    # keep track of progress.
    logs.LOG.debug('< task complete, signalling completion')
    signal_task_complete(job_id, len(src_ids))


def signal_task_complete(job_id, num_sources):
    """
    Send a signal back through a dedicated queue to the 'control node' to
    notify of task completion and the number of sources computed.

    Signalling back this metric is needed to tell the control node when it can
    conclude its `execute` phase.

    :param int job_id:
        ID of a currently running :class:`~openquake.db.models.OqJob`.
    :param int num_sources:
        Number of sources computed in the completed task.
    """
    # TODO: The job ID may be redundant (since it's in the routing key), but
    # we can put this here for a sanity check on the receiver side.
    # Maybe we can remove this.
    msg = dict(job_id=job_id, num_sources=num_sources)

    exchange = kombu.Exchange(
        config.get_section('hazard')['task_exchange'], type='direct')

    amqp_cfg = config.get_section('amqp')
    conn_args = {
        'hostname': amqp_cfg['host'],
        'userid': amqp_cfg['user'],
        'password': amqp_cfg['password'],
        'virtual_host': amqp_cfg['vhost'],
    }

    routing_key = _ROUTING_KEY_FMT % dict(job_id=job_id)

    with kombu.BrokerConnection(**conn_args) as conn:
        with conn.Producer(exchange=exchange,
                           routing_key=routing_key) as producer:
            producer.publish(msg)


def im_dict_to_nhlib(im_dict):
    """
    Given the dict of intensity measure types and levels, convert them to a
    dict with the same values, except create :mod:`mhlib.imt` objects for the
    new keys.

    :returns:
        A dict of intensity measure level lists, keyed by an IMT object. See
        :mod:`nhlib.imt` for more information.
    """
    # TODO: file a bug about  SA periods in nhlib imts.
    # Why are values of 0.0 not allowed?
    nhlib_im = {}

    for imt, imls in im_dict.items():
        nhlib_imt = _imt_to_nhlib(imt)
        nhlib_im[nhlib_imt] = imls

    return nhlib_im


def _imt_to_nhlib(imt):
    """Covert an IMT string to an nhlib object.

    :param str imt:
        Given the IMT string (defined in the job config file), convert it to
        equivlent nhlib object. See :mod:`nhlib.imt`.
    """
    if 'SA' in imt:
        match = re.match(r'^SA\((.+?)\)$', imt)
        period = float(match.group(1))
        return nhlib.imt.SA(period, DEFAULT_SA_DAMPING)
    else:
        imt_class = getattr(nhlib.imt, imt)
        return imt_class()
