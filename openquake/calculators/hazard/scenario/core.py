# -*- coding: utf-8 -*-
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
Disaggregation calculator core functionality
"""
import os
import random
from cStringIO import StringIO

from nrml.hazard.parsers import RuptureModelParser

# NHLIB
from nhlib.calc import ground_motion_fields
from nhlib import correlation
import nhlib.gsim

from openquake.calculators.hazard import general as haz_general
from openquake import utils, logs, engine2
from openquake.db import models
from openquake.input import source
from openquake.job.validation import MAX_SINT_32

# FIXME! Duplication in EventBased Hazard Calculator
#: Ground motion correlation model map
GM_CORRELATION_MODEL_MAP = {
    'JB2009': correlation.JB2009CorrelationModel,
}

AVAILABLE_GSIMS = nhlib.gsim.get_available_gsims()


@utils.tasks.oqtask
@utils.stats.count_progress('h')
def gmfs(job_id, rupture_ids, task_seed, task_no):
    """
    A celery task wrapper function around :func:`compute_gmfs`.
    See :func:`compute_gmfs` for parameter definitions.
    """
    logs.LOG.debug('> starting task: job_id=%s, task_no=%s'
                   % (job_id, task_no))

    compute_gmfs(job_id, rupture_ids, task_seed, task_no)
    # Last thing, signal back the control node to indicate the completion of
    # task. The control node needs this to manage the task distribution and
    # keep track of progress.
    logs.LOG.debug('< task complete, signalling completion')
    haz_general.signal_task_complete(job_id=job_id, num_items=1)


# Silencing 'Too many local variables'
# pylint: disable=R0914
def compute_gmfs(job_id, rupture_ids, task_seed, task_no):
    print job_id, rupture_ids, task_seed, task_no, '***********************'

    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    rupture_mdl = source.nrml_to_nhlib(
        models.ParsedRupture.objects.get(id=rupture_ids[0]).nrml,
        hc.rupture_mesh_spacing, None, None)
    sites = haz_general.get_site_collection(hc)
    imts = [haz_general.imt_to_nhlib(x) for x in hc.intensity_measure_types]
    GSIM = AVAILABLE_GSIMS[hc.gsim]

    print ground_motion_fields(
        rupture_mdl, sites, imts, GSIM(),
        hc.truncation_level, realizations=1,
        correlation_model=GM_CORRELATION_MODEL_MAP['JB2009'](True))


class ScenarioHazardCalculator(haz_general.BaseHazardCalculatorNext):

    core_calc_task = gmfs

    def initialize_sources(self):
        """
        """
        logs.log_progress("initializing sources", 2)

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

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()
        self.progress['total'] = self.hc.number_of_ground_motion_fields

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
        for task_no in range(self.hc.number_of_ground_motion_fields):
            task_seed = rnd.randint(0, MAX_SINT_32)
            task_args = (self.job.id, rupture_ids, task_seed, task_no)
            yield task_args