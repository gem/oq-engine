# -*- coding: utf-8 -*-
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
Scenario calculator core functionality
"""
import random
from cStringIO import StringIO
from django.db import transaction
import numpy

from nrml.hazard.parsers import RuptureModelParser

# NHLIB
from nhlib.calc import ground_motion_fields
import nhlib.gsim

from openquake.calculators.hazard import general as haz_general
from openquake.calculators import base
from openquake import utils, logs
from openquake.db import models
from openquake.input import source
from openquake import writer
from openquake.job.validation import MAX_SINT_32


AVAILABLE_GSIMS = nhlib.gsim.get_available_gsims()


def gmf_realiz_per_task(num_realizations, num_concur_task):
    """
    Realizations per task return a tuple in the format
    (spare : bool, realizations : int list) where spare
    represents if there are spare realizations
    and realizations the number of realizations for
    each task.
    """

    realiz_per_task, spare_realizations = divmod(
                                  num_realizations, num_concur_task)
    result = [realiz_per_task for _ in xrange(num_concur_task)]
    if spare_realizations:
        result.append(spare_realizations)
    return spare_realizations > 0, result


@utils.tasks.oqtask
@utils.stats.count_progress('h')
def gmfs(job_id, rupture_ids, output_id, task_seed, task_no, realizations):
    """
    A celery task wrapper function around :func:`compute_gmfs`.
    See :func:`compute_gmfs` for parameter definitions.

    :param task_seed:
        Value for seeding numpy/scipy in the computation of
        ground motion fields.
    :param realizations:
        Number of ground motion field realizations which are
        going to be created by the task.
    """

    logs.LOG.debug('> starting task: job_id=%s, task_no=%s'
                   % (job_id, task_no))

    numpy.random.seed(task_seed)
    compute_gmfs(job_id, rupture_ids, output_id, task_no, realizations)

    # Last thing, signal back the control node to indicate the completion of
    # task. The control node needs this to manage the task distribution and
    # keep track of progress.
    logs.LOG.debug('< task complete, signalling completion')
    base.signal_task_complete(job_id=job_id, num_items=realizations)


# NB: get_site_collection is called for each task;
# this could be a performance bottleneck, potentially
def compute_gmfs(job_id, rupture_ids, output_id, task_no, realizations):
    """
    Compute ground motion fields and store them in the db.

    :param job_id:
        ID of the currently running job.
    :param rupture_ids:
        List of ids of parsed rupture model from which we will generate
        ground motion fields.
    :param output_id:
        output_id idenfitifies the reference to the output record.
    :param task_no:
        The task_no in which the calculation results will be placed.
        This ID basically corresponds to the sequence number of the task,
        in the context of the entire calculation.
    :param realizations:
        Number of realizations which are going to be created.
    """

    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    rupture_mdl = source.nrml_to_nhlib(
        models.ParsedRupture.objects.get(id=rupture_ids[0]).nrml,
        hc.rupture_mesh_spacing, None, None)
    imts = [haz_general.imt_to_nhlib(x) for x in hc.intensity_measure_types]
    gsim = AVAILABLE_GSIMS[hc.gsim]
    correlation_model = haz_general.get_correl_model(hc)
    gmf = ground_motion_fields(
        rupture_mdl, sites, imts, gsim(),
        hc.truncation_level, realizations=realizations,
        correlation_model=correlation_model)

    save_gmf(output_id, gmf, hc.site_collection.mesh, task_no)


@transaction.commit_on_success(using='reslt_writer')
def save_gmf(output_id, gmf_dict, points_to_compute, result_grp_ordinal):
    """
    Helper method to save computed GMF data to the database.

    :param int output_id:
        Output_id identifies the reference to the output record.
    :param dict gmf_dict:
        The GMF results during the calculation.
    :param points_to_compute:
        An :class:`nhlib.geo.mesh.Mesh` object, representing all of the points
        of interest for a calculation.
    :param int result_grp_ordinal:
        The sequence number (1 to N) of the task which computed these results.

        A calculation consists of N tasks, so this tells us which task computed
        the data.
    """
    inserter = writer.BulkInserter(models.GmfScenario)

    for imt, gmfs_ in gmf_dict.iteritems():
        # ``gmfs`` comes in as a numpy.matrix
        # we want it is an array; it handles subscripting
        # in the way that we want
        gmfarray = numpy.array(gmfs_)

        sa_period = None
        sa_damping = None
        if isinstance(imt, nhlib.imt.SA):
            sa_period = imt.period
            sa_damping = imt.damping
        imt_name = imt.__class__.__name__

        for i, location in enumerate(points_to_compute):
            inserter.add_entry(
                output_id=output_id,
                imt=imt_name,
                sa_period=sa_period,
                sa_damping=sa_damping,
                location=location.wkt2d,
                gmvs=gmfarray[i].tolist(),
                result_grp_ordinal=result_grp_ordinal,
            )

    inserter.flush()


class ScenarioHazardCalculator(haz_general.BaseHazardCalculatorNext):
    """
    Scenario hazard calculator. Computes ground motion fields.
    """

    core_calc_task = gmfs
    output = None  # defined in pre_execute

    def initialize_sources(self):
        """
        Get the rupture_model file from the job.ini file, and store a
        parsed version of it in the database (see
        :class:`openquake.db.models.ParsedRupture``) in pickle format.
        """

        # Get the rupture model in input
        [inp] = models.inputs4hcalc(self.hc.id, input_type='rupture_model')

        # Associate the source input to the calculation:
        models.Input2hcalc.objects.get_or_create(
            input=inp, hazard_calculation=self.hc)

        # Store the ParsedRupture record
        src_content = StringIO(inp.model_content.raw_content)
        rupt_parser = RuptureModelParser(src_content)
        src_db_writer = source.RuptureDBWriter(inp, rupt_parser.parse())
        src_db_writer.serialize()

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails: parsing and
        initializing sources, parsing and initializing the site model (if there
        is one), and generating logic tree realizations. (The latter piece
        basically defines the work to be done in the `execute` phase.)
        """

        # Create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        # Once the site model is init'd, create and cache the site collection;
        self.hc.init_site_collection()

        self.progress['total'] = self.hc.number_of_ground_motion_fields

        # Store a record in the output table.
        self.output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="gmf_scenario",
            output_type="gmf_scenario")
        self.output.save()

    def task_arg_gen(self, block_size):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        Yielded results are quadruples of (job_id, task_no,
        rupture_id, random_seed). (random_seed will be used to seed
        numpy for temporal occurence sampling.)

        :param int block_size:
            The number of work items for each task. Fixed to 1.
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)

        inp = models.inputs4hcalc(self.hc.id, 'rupture_model')[0]
        ruptures = models.ParsedRupture.objects.filter(input__id=inp.id)
        rupture_ids = [rupture.id for rupture in ruptures]
        num_concurrent_tasks = self.concurrent_tasks()

        spare_realizations, realiz_per_task = gmf_realiz_per_task(
                self.hc.number_of_ground_motion_fields, num_concurrent_tasks)

        num_tasks = (num_concurrent_tasks + 1 if spare_realizations
                    else num_concurrent_tasks)

        for task_no in range(num_tasks):
            task_seed = rnd.randint(0, MAX_SINT_32)
            task_args = (self.job.id, rupture_ids,
                         self.output.id, task_seed, task_no,
                         realiz_per_task[task_no])
            yield task_args
