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
from django.db import transaction
import numpy

from openquake.nrmllib.hazard.parsers import RuptureModelParser

# HAZARDLIB
from openquake.hazardlib.calc import ground_motion_fields
import openquake.hazardlib.gsim

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators import base
from openquake.engine.utils import tasks, stats
from openquake.engine.db import models
from openquake.engine.input import source
from openquake.engine import writer
from openquake.engine.utils.general import block_splitter
from openquake.engine.performance import EnginePerformanceMonitor


BLOCK_SIZE = 1000  # TODO: decide where to put this parameter

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
@stats.count_progress('h')
def gmfs(job_id, sites, rupture_id, gmfcoll_id, task_seed, realizations):
    """
    A celery task wrapper function around :func:`compute_gmfs`.
    See :func:`compute_gmfs` for parameter definitions.
    """
    numpy.random.seed(task_seed)
    compute_gmfs(job_id, sites, rupture_id, gmfcoll_id, realizations)
    base.signal_task_complete(job_id=job_id, num_items=len(sites))


def compute_gmfs(job_id, sites, rupture_id, gmfcoll_id, realizations):
    """
    Compute ground motion fields and store them in the db.

    :param job_id:
        ID of the currently running job.
    :param sites:
        The subset of the full SiteCollection scanned by this task
    :param rupture_id:
        The parsed rupture model from which we will generate
        ground motion fields.
    :param gmfcoll_id:
        the id of a :class:`openquake.engine.db.models.Gmf` record
    :param realizations:
        Number of realizations to create.
    """

    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    rupture_mdl = source.nrml_to_hazardlib(
        models.ParsedRupture.objects.get(id=rupture_id).nrml,
        hc.rupture_mesh_spacing, None, None)
    imts = [haz_general.imt_to_hazardlib(x)
            for x in hc.intensity_measure_types]
    gsim = AVAILABLE_GSIMS[hc.gsim]()  # instantiate the GSIM class
    correlation_model = haz_general.get_correl_model(hc)

    with EnginePerformanceMonitor('computing gmfs', job_id, gmfs):
        gmf = ground_motion_fields(
            rupture_mdl, sites, imts, gsim,
            hc.truncation_level, realizations=realizations,
            correlation_model=correlation_model)
    with EnginePerformanceMonitor('saving gmfs', job_id, gmfs):
        save_gmf(gmfcoll_id, gmf, sites)


@transaction.commit_on_success(using='reslt_writer')
def save_gmf(gmfcoll_id, gmf_dict, sites):
    """
    Helper method to save computed GMF data to the database.

    :param int gmfcoll_id:
        the id of a :class:`openquake.engine.db.models.Gmf` record
    :param dict gmf_dict:
        The GMF results during the calculation
    :param sites:
        An :class:`openquake.engine.models.SiteCollection`
        object
    """
    inserter = writer.CacheInserter(models.GmfData, 100)
    # NB: GmfData may contain large arrays and the cache may become large

    for imt, gmfs_ in gmf_dict.iteritems():
        # ``gmfs`` comes in as a numpy.matrix
        # we want it is an array; it handles subscripting
        # in the way that we want
        gmfarray = numpy.array(gmfs_)

        sa_period = None
        sa_damping = None
        if isinstance(imt, openquake.hazardlib.imt.SA):
            sa_period = imt.period
            sa_damping = imt.damping
        imt_name = imt.__class__.__name__

        for i, site in enumerate(sites):
            inserter.add(models.GmfData(
                gmf_id=gmfcoll_id,
                ses_id=None,
                imt=imt_name,
                sa_period=sa_period,
                sa_damping=sa_damping,
                site_id=site.id,
                rupture_ids=None,
                gmvs=gmfarray[i].tolist()))

    inserter.flush()


class ScenarioHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Scenario hazard calculator. Computes ground motion fields.
    """

    core_calc_task = gmfs
    output = None  # defined in pre_execute

    def __init__(self, *args, **kwargs):
        super(ScenarioHazardCalculator, self).__init__(*args, **kwargs)
        self.gmfcoll = None

    def initialize_sources(self):
        """
        Get the rupture_model file from the job.ini file, and store a
        parsed version of it in the database (see
        :class:`openquake.engine.db.models.ParsedRupture``) in pickle format.
        """

        # Get the rupture model in input
        src_db_writer = source.RuptureDBWriter(
            self.job, RuptureModelParser(
                self.hc.inputs['rupture_model']).parse())
        src_db_writer.serialize()

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

        # Create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        self.progress['total'] = len(self.hc.site_collection)

        # create a record in the output table
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name="gmf_scenario",
            output_type="gmf_scenario")

        # create an associated gmf record
        self.gmfcoll = models.Gmf.objects.create(output=output)

    def task_arg_gen(self, block_size):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        Yielded results are 6-uples of the form (job_id,
        sites, rupture_id, gmfcoll_id, task_seed, realizations)
        (task_seed will be used to seed numpy for temporal occurence sampling).

        :param int block_size:
            The number of work items for each task. Fixed to 1.
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)

        rupture_id = self.job.parsedrupture.id

        for sites in block_splitter(self.hc.site_collection, BLOCK_SIZE):
            task_seed = rnd.randint(0, models.MAX_SINT_32)
            yield (self.job.id, models.SiteCollection(sites),
                   rupture_id, self.gmfcoll.id, task_seed,
                   self.hc.number_of_ground_motion_fields)
