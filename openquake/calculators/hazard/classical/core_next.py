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
import StringIO

from django.db import transaction
from celery.task import task
from nrml import parsers as nrml_parsers
import nhlib

from openquake import engine2
from openquake import writer
from openquake.utils import config
from openquake.utils import tasks as utils_tasks
from openquake.calculators import base
from openquake.calculators.hazard import general
from openquake.db import models
from openquake.input import logictree
from openquake.input import source
from openquake.job.validation import MIN_SINT_32
from openquake.job.validation import MAX_SINT_32


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
        Distribute work among workers.
        """
        # TODO: better documentation
        # TODO: unittest
        job = self.job
        hc = job.hazard_calculation
        sources_per_task = config.get('hazard', 'block_size')

        total_sources_to_compute = 0

        realizations = models.LtRealization.objects.filter(
                hazard_calculation=hc, is_complete=False)

        for lt_rlz in realizations:
            source_progress = models.SourceProgress.objects.filter(
                    is_complete=False, lt_realization=lt_rlz)
            source_ids = source_progress.values_list('parsed_source_id',
                                                     flat=True)
            total_sources_to_compute += len(source_ids)

            for offset in xrange(0, len(source_ids), sources_per_task):
                hazard_curves.apply_async(job.id, lt_rlz.id,
                        source_ids[offset:offset + sources_per_task])

        # TODO: create a queue for this job for workers to report progress
        # and listen on events on that queue, counting computed sources
        # and comparing it with total_sources_to_compute. exit when two
        # are equal


@task(ignore_result=True)
def hazard_curves(job_id, lt_rlz_id, src_ids):
    """
    Celery task for hazard curve calculator.

    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param src_ids:
        List of ids of parsed source models to take into account.
    """
    # TODO: better documentation
    # TODO: unittest
    # make sure the job is not yet finished and set up logging
    utils_tasks.get_running_job(job_id)

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
            nrml_source = models.ParsedSource.objects.get(pk=src_id)
            nhlib_source = source.nrml_to_nhlib(nrml_source)
            apply_uncertainties(nhlib_source)
            yield nhlib_source

    # TODO: convert here string ids of IMTs to nhlib objects (see nhlib.imt)
    imts = hc.intensity_measure_types_and_levels

    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': gen_sources(),
                   'imts': imts,
                   'sites': 'TODO: load sites collection'}

    if hc.maximum_distance:
        dist = hc.maximum_distance
        calc_kwargs['source_site_filter'] = (
                nhlib.calc.filters.source_site_distance_filter(dist))
        calc_kwargs['rupture_site_filter'] = (
                nhlib.calc.filters.rupture_site_distance_filter(dist))

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    matrices = nhlib.calc.hazard_curve.hazard_curves_poissonian(**calc_kwargs)

    with transaction.commit_on_success():
        for imt in hc.intensity_measure_types_and_levels.keys():
            hc_progress = models.HazardCurveProgress.objects \
                         .select_for_update() \
                         .get(lt_realization=lt_rlz, imt=imt)

            # TODO: check here if any of records in source progress model
            # with parsed_source_id from src_ids are marked as complete,
            # and rollback and abort if there is at least one

            hc_progress.result_matrix = (
                1 - (1 - hc_progress.result_matrix) * (1 - matrices[imt]))
            hc_progress.save()

            models.SourceProgress.objects.filter(lt_realization=lt_rlz,
                                                 parsed_source__in=src_ids) \
                                         .update(is_complete=True)

            lt_rlz.completed_sources += len(src_ids)
            if lt_rlz.completed_sources == lt_rlz.total_sources:
                lt_rlz.is_complete = True

            lt_rlz.save()

    # TODO: signal back to calculator
