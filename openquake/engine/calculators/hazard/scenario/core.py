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
from openquake.hazardlib.imt import from_string
import openquake.hazardlib.gsim

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine.input import source
from openquake.engine import writer
from openquake.engine.performance import EnginePerformanceMonitor

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
def gmfs(job_id, sites, rupture, gmf_id, task_seed, realizations, task_no):
    """
    A celery task wrapper function around :func:`compute_gmfs`.
    See :func:`compute_gmfs` for parameter definitions.
    """
    numpy.random.seed(task_seed)
    gmf_dict = compute_gmfs(job_id, sites, rupture, gmf_id, realizations)
    with EnginePerformanceMonitor('saving gmfs', job_id, gmfs):
        save_gmf(gmf_id, gmf_dict, sites, task_no)


def compute_gmfs(job_id, sites, rupture, gmf_id, realizations):
    """
    Compute ground motion fields and store them in the db.

    :param job_id:
        ID of the currently running job.
    :param sites:
        The subset of the full SiteCollection scanned by this task
    :param rupture:
        The hazardlib rupture from which we will generate
        ground motion fields.
    :param gmf_id:
        the id of a :class:`openquake.engine.db.models.Gmf` record
    :param realizations:
        Number of realizations to create.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    imts = [from_string(x) for x in hc.intensity_measure_types]
    gsim = AVAILABLE_GSIMS[hc.gsim]()  # instantiate the GSIM class
    correlation_model = haz_general.get_correl_model(hc)

    with EnginePerformanceMonitor('computing gmfs', job_id, gmfs):
        return ground_motion_fields(
            rupture, sites, imts, gsim,
            hc.truncation_level, realizations=realizations,
            correlation_model=correlation_model)


@transaction.commit_on_success(using='job_init')
def save_gmf(gmf_id, gmf_dict, sites, task_no):
    """
    Helper method to save computed GMF data to the database.

    :param int gmf_id:
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
        imt_name, sa_period, sa_damping = imt
        for i, site in enumerate(sites):
            inserter.add(models.GmfData(
                gmf_id=gmf_id,
                task_no=task_no,
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
        self.gmf = None
        self.rupture = None

    def initialize_sources(self):
        """
        Get the rupture_model file from the job.ini file, and set the
        attribute self.rupture.
        """
        nrml = RuptureModelParser(self.hc.inputs['rupture_model']).parse()
        rms = self.job.hazard_calculation.rupture_mesh_spacing
        self.rupture = source.nrml_to_hazardlib(nrml, rms, None, None)

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """
        self.parse_risk_models()
        self.initialize_sources()
        self.initialize_site_model()

        # create a record in the output table
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name="GMF",
            output_type="gmf_scenario")

        # create an associated gmf record
        self.gmf = models.Gmf.objects.create(output=output)

    def _get_realizations(self):
        return range(self.hc.number_of_ground_motion_fields)

    def task_arg_gen(self):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        Yielded results are 6-uples of the form (job_id,
        sites, rupture_id, gmf_id, task_seed, realizations, task_no)
        (task_seed will be used to seed numpy for temporal occurence sampling).
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        # TODO: fix the block size dependency
        blocks = self.block_split(self.hc.site_collection)
        for task_no, sites in enumerate(blocks):
            task_seed = rnd.randint(0, models.MAX_SINT_32)
            yield (self.job.id, models.SiteCollection(sites),
                   self.rupture, self.gmf.id, task_seed,
                   self.hc.number_of_ground_motion_fields, task_no)
