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
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.imt import from_string
import openquake.hazardlib.gsim

from openquake.commonlib.general import SequenceSplitter, distinct
from openquake.commonlib import source

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine import writer
from openquake.engine.performance import EnginePerformanceMonitor

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
def gmfs(job_id, ses_ruptures, sitecol, gmf_id, task_no):
    """
    :param int job_id: the current job ID
    :param ses_ruptures: a set of `SESRupture` instances
    :param sitecol: a `SiteCollection` instance
    :param int gmf_id: the ID of a `Gmf` instance
    :param int task_no: the task number
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    # distinct is here to make sure that IMTs such as
    # SA(0.8) and SA(0.80) are considered the same
    imts = distinct(from_string(x) for x in hc.intensity_measure_types)
    gsim = AVAILABLE_GSIMS[hc.gsim]()  # instantiate the GSIM class
    realizations = 1  # one realization for each seed
    correlation_model = haz_general.get_correl_model(hc)

    cache = collections.defaultdict(list)  # {site_id, imt -> gmvs}
    inserter = writer.CacheInserter(models.GmfData, 1000)
    # insert GmfData in blocks of 1000 sites

    rupture = ses_ruptures[0].rupture  # ProbabilisticRupture instance
    with EnginePerformanceMonitor('computing gmfs', job_id, gmfs):
        gmf = GmfComputer(rupture, sitecol, imts, gsim, hc.truncation_level,
                          correlation_model)
        for ses_rup in ses_ruptures:
            gmf_dict = gmf.compute(ses_rup.seed)
            for imt in imts:
                for site_id, gmv in zip(sitecol.sids, gmf_dict[imt]):
                    # float may be needed below to convert 1x1 matrices
                    cache[site_id, imt].append((float(gmv), ses_rup.id))

    with EnginePerformanceMonitor('saving gmfs', job_id, gmfs):
        for (site_id, imt), data in cache.iteritems():
            gmvs, rup_ids = zip(*data)
            inserter.add(
                models.GmfData(
                    gmf_id=gmf_id,
                    task_no=task_no,
                    imt=imt[0],
                    sa_period=imt[1],
                    sa_damping=imt[2],
                    site_id=site_id,
                    rupture_ids=rup_ids,
                    gmvs=gmvs))
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
        self.create_ruptures()

    def create_ruptures(self):
        # check filtering
        hc = self.hc
        if hc.maximum_distance:
            self.sites = filters.filter_sites_by_distance_to_rupture(
                self.rupture, hc.maximum_distance, hc.site_collection)
            if self.sites is None:
                raise RuntimeError(
                    'All sites where filtered out! '
                    'maximum_distance=%s km' % hc.maximum_distance)

        # create ses output
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name='SES Collection',
            output_type='ses')
        self.ses_coll = models.SESCollection.objects.create(
            output=output, lt_model=None, ordinal=0)

        # create gmf output
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name="GMF",
            output_type="gmf_scenario")
        self.gmf = models.Gmf.objects.create(output=output)

        # creating seeds
        rnd = random.Random()
        rnd.seed(self.hc.random_seed)
        all_seeds = [
            rnd.randint(0, models.MAX_SINT_32)
            for _ in xrange(self.hc.number_of_ground_motion_fields)]

        with self.monitor('saving ruptures'):
            prob_rup = models.ProbabilisticRupture.create(
                self.rupture, self.ses_coll)
            inserter = writer.CacheInserter(models.SESRupture, 100000)
            for ses_idx, seed in enumerate(all_seeds):
                inserter.add(
                    models.SESRupture(
                        ses_id=1, rupture=prob_rup,
                        tag='scenario-%010d' % ses_idx,  seed=seed))
            inserter.flush()

    def task_arg_gen(self):
        """
        Yield a tuple of the form (job_id, sitecol, rupture_id, gmf_id,
        task_seed, num_realizations). `task_seed` will be used to seed
        numpy for temporal occurence sampling. Only a single task
        will be generated which is fine since the computation is fast
        anyway.
        """
        ses_ruptures = models.SESRupture.objects.filter(
            rupture__ses_collection=self.ses_coll.id)
        ss = SequenceSplitter(self.concurrent_tasks())
        for task_no, ruptures in enumerate(ss.split(ses_ruptures)):
            yield self.job.id, ruptures, self.sites, self.gmf.id, task_no
