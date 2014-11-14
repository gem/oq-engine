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
import random
import numpy

# HAZARDLIB
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.imt import from_string
import openquake.hazardlib.gsim

from openquake.commonlib.readinput import get_rupture

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators import calculators
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine import logs, writer
from openquake.engine.performance import EnginePerformanceMonitor

from django.db import transaction

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
def calc_gmfs(job_id, tag_seed_pairs, computer):
    """
    Computes several GMFs in parallel, one for each tag and seed.

    :param int job_id:
        the current job ID
    :param tag_seed_pairs:
        list of pairs (rupture tag, rupture seed)
    :param computer:
        :class:`openquake.hazardlib.calc.gmf.GMFComputer` instance
    :returns:
        a dictionary tag -> {imt: gmf}
    """
    return {tag: dict(computer.compute(seed)) for tag, seed in tag_seed_pairs}


def create_db_ruptures(rupture, ses_coll, tags, seed):
    """
    Insert the SESRuptures associated to the given rupture and
    SESCollection.

    :param rupture: hazardlib rupture
    :param ses_coll: SESCollection instance
    :param tags: tags of the ruptures to insert
    :seed: a random seed
    :returns: the IDs of the inserted ProbabilisticRupture and SESRuptures
    """
    prob_rup = models.ProbabilisticRupture.create(rupture, ses_coll)
    inserter = writer.CacheInserter(models.SESRupture, max_cache_size=100000)
    rnd = random.Random()
    rnd.seed(seed)
    seeds = []
    sesrupts = []
    for tag in tags:
        s = rnd.randint(0, models.MAX_SINT_32)
        seeds.append(s)
        sesrupts.append(
            models.SESRupture(ses_id=1, rupture=prob_rup, tag=tag, seed=s))
    return prob_rup.id, inserter.saveall(sesrupts), seeds


@calculators.add('scenario')
class ScenarioHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Scenario hazard calculator. Computes ground motion fields.
    """

    core_calc_task = calc_gmfs
    output = None  # defined in pre_execute

    def __init__(self, *args, **kwargs):
        super(ScenarioHazardCalculator, self).__init__(*args, **kwargs)
        self.gmf = None
        self.rupture = None

    def initialize_realizations(self):
        """There are no realizations for the scenario calculator"""
        pass

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files, and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.)
        """
        # if you don't use an explicit transaction, errors will be masked
        # the problem is that Django by default performs implicit transactions
        # without rollback, see
        # https://docs.djangoproject.com/en/1.3/topics/db/transactions/
        with transaction.commit_on_success(using='job_init'):
            self.parse_risk_model()
        with transaction.commit_on_success(using='job_init'):
            self.initialize_site_collection()

        hc = self.hc
        n_sites = len(self.site_collection)
        n_gmf = hc.number_of_ground_motion_fields
        n_imts = len(hc.intensity_measure_types_and_levels)
        output_weight = n_sites * n_imts * n_gmf
        logs.LOG.info('Expected output size=%s', output_weight)
        models.JobInfo.objects.create(
            oq_job=self.job,
            num_sites=n_sites,
            num_realizations=1,
            num_imts=n_imts,
            num_levels=0,
            input_weight=0,
            output_weight=output_weight)
        self.check_limits(input_weight=0, output_weight=output_weight)
        self.create_ruptures()
        return 0, output_weight

    def create_ruptures(self):
        oqparam = models.oqparam(self.job.id)
        self.imts = map(
            from_string, sorted(oqparam.intensity_measure_types_and_levels))
        self.rupture = get_rupture(oqparam)

        # check filtering
        trunc_level = getattr(oqparam, 'truncation_level', None)
        maximum_distance = oqparam.maximum_distance
        self.sites = filters.filter_sites_by_distance_to_rupture(
            self.rupture, maximum_distance, self.site_collection)
        if self.sites is None:
            raise RuntimeError(
                'All sites where filtered out! '
                'maximum_distance=%s km' % maximum_distance)

        # create ses output
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name='SES Collection',
            output_type='ses')
        self.ses_coll = models.SESCollection.create(output=output)

        # create gmf output
        output = models.Output.objects.create(
            oq_job=self.job,
            display_name="GMF",
            output_type="gmf_scenario")
        self.gmf = models.Gmf.objects.create(output=output)

        with self.monitor('saving ruptures'):
            self.tags = ['scenario-%010d' % i for i in xrange(
                oqparam.number_of_ground_motion_fields)]
            _, self.rupids, self.seeds = create_db_ruptures(
                self.rupture, self.ses_coll, self.tags,
                self.hc.random_seed)

        correlation_model = models.get_correl_model(
            models.OqJob.objects.get(pk=self.job.id))
        gsim = AVAILABLE_GSIMS[oqparam.gsim]()
        self.computer = GmfComputer(
            self.rupture, self.site_collection, self.imts, gsim,
            trunc_level, correlation_model)

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Run :function:`openquake.engine.calculators.hazard.scenario.core.gmfs`
        in parallel.
        """
        self.acc = tasks.apply_reduce(
            self.core_calc_task,
            (self.job.id, zip(self.tags, self.seeds), self.computer))

    @EnginePerformanceMonitor.monitor
    def post_execute(self):
        """
        Saving the GMFs in the database
        """
        gmf_id = self.gmf.id
        inserter = writer.CacheInserter(models.GmfData, max_cache_size=1000)
        for imt in self.imts:
            gmfs = numpy.array([self.acc[tag][str(imt)]
                                for tag in self.tags]).transpose()
            for site_id, gmvs in zip(self.site_collection.sids, gmfs):
                inserter.add(
                    models.GmfData(
                        gmf_id=gmf_id,
                        task_no=0,
                        imt=imt[0],
                        sa_period=imt[1],
                        sa_damping=imt[2],
                        site_id=site_id,
                        rupture_ids=self.rupids,
                        gmvs=list(gmvs)))
        inserter.flush()
