# -*- coding: utf-8 -*-
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

"""
Scenario calculator core functionality
"""
import collections
import random
import numpy

from openquake.nrmllib.hazard.parsers import RuptureModelParser

# HAZARDLIB
from openquake.hazardlib.calc import ground_motion_fields, filters
from openquake.hazardlib.imt import from_string
import openquake.hazardlib.gsim

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.utils import tasks, general
from openquake.engine.db import models
from openquake.engine.input import source
from openquake.engine import writer
from openquake.engine.performance import EnginePerformanceMonitor

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
def gmfs(job_id, seeds, sitecol, rupture, gmf_id, task_no):
    """
    A celery task wrapper function around :func:`compute_gmfs`.
    See :func:`compute_gmfs` for parameter definitions.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    imts = [from_string(x) for x in hc.intensity_measure_types]
    gsim = AVAILABLE_GSIMS[hc.gsim]()  # instantiate the GSIM class
    realizations = 1  # one realization for each seed
    correlation_model = haz_general.get_correl_model(hc)
    rup_filter = filters.rupture_site_distance_filter(hc.maximum_distance)

    cache = collections.defaultdict(list)  # {site_id, imt -> gmvs}
    inserter = writer.CacheInserter(models.GmfData, 1000)
    # insert GmfData in blocks of 1000 sites

    with EnginePerformanceMonitor('computing gmfs', job_id, gmfs):
        for task_seed in seeds:
            numpy.random.seed(task_seed)
            gmf_dict = ground_motion_fields(
                rupture, sitecol, imts, gsim, hc.truncation_level,
                realizations, correlation_model, rup_filter)
            for imt in imts:
                for site_id, gmv in zip(sitecol.sids, gmf_dict[imt]):
                    # float is needed below to convert 1x1 matrices
                    cache[site_id, imt].append(float(gmv))

    with EnginePerformanceMonitor('saving gmfs', job_id, gmfs):
        for site_id, imt in cache:
            inserter.add(
                models.GmfData(
                    gmf_id=gmf_id,
                    task_no=task_no,
                    imt=imt[0],
                    sa_period=imt[1],
                    sa_damping=imt[2],
                    site_id=site_id,
                    rupture_ids=None,
                    gmvs=cache[site_id, imt]))
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
        self.rupture = source.NrmlHazardlibConverter(self.hc)(nrml)

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

    def task_arg_gen(self):
        """
        Yield a tuple of the form (job_id, sitecol, rupture_id, gmf_id,
        task_seed, num_realizations). `task_seed` will be used to seed
        numpy for temporal occurence sampling. Only a single task
        will be generated which is fine since the computation is fast
        anyway.
        """
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        all_seeds = [rnd.randint(0, models.MAX_SINT_32)
                     for _ in xrange(self.hc.number_of_ground_motion_fields)]
        ss = general.SequenceSplitter(self.concurrent_tasks())
        for task_no, task_seeds in enumerate(ss.split(all_seeds)):
            yield (self.job.id, task_seeds, self.hc.site_collection,
                   self.rupture, self.gmf.id, task_no)
