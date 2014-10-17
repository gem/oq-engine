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

# HAZARDLIB
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.imt import from_string
import openquake.hazardlib.gsim

from openquake.commonlib.node import read_nodes
from openquake.commonlib.general import split_in_blocks
from openquake.commonlib.readinput import get_rupture

from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine import logs, writer
from openquake.engine.performance import EnginePerformanceMonitor

from django.db import transaction

AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims()


@tasks.oqtask
def gmfs(job_id, ses_ruptures, sitecol, imts, gmf_id):
    """
    :param int job_id: the current job ID
    :param ses_ruptures: a set of `SESRupture` instances
    :param sitecol: a `SiteCollection` instance
    :param imts: a list of hazardlib IMT instances
    :param int gmf_id: the ID of a `Gmf` instance
    """
    hc = models.oqparam(job_id)
    gsim = AVAILABLE_GSIMS[hc.gsim]()  # instantiate the GSIM class
    correlation_model = models.get_correl_model(
        models.OqJob.objects.get(pk=job_id))

    cache = collections.defaultdict(list)  # {site_id, imt -> gmvs}
    inserter = writer.CacheInserter(models.GmfData, 1000)
    # insert GmfData in blocks of 1000 sites

    # NB: ses_ruptures a non-empty list produced by the block_splitter
    rupture = ses_ruptures[0].rupture  # ProbabilisticRupture instance
    with EnginePerformanceMonitor('computing gmfs', job_id, gmfs):
        gmf = GmfComputer(rupture, sitecol, imts, [gsim],
                          getattr(hc, 'truncation_level', None),
                          correlation_model)
        gname = gsim.__class__.__name__
        for ses_rup in ses_ruptures:
            for (gname, imt), gmvs in gmf.compute(ses_rup.seed):
                for site_id, gmv in zip(sitecol.sids, gmvs):
                    cache[site_id, imt].append((gmv, ses_rup.id))

    with EnginePerformanceMonitor('saving gmfs', job_id, gmfs):
        for (site_id, imt_str), data in cache.iteritems():
            imt = from_string(imt_str)
            gmvs, rup_ids = zip(*data)
            inserter.add(
                models.GmfData(
                    gmf_id=gmf_id,
                    task_no=0,
                    imt=imt[0],
                    sa_period=imt[1],
                    sa_damping=imt[2],
                    site_id=site_id,
                    rupture_ids=rup_ids,
                    gmvs=gmvs))
        inserter.flush()


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
    sesrupts = [
        models.SESRupture(
            ses_id=1, rupture=prob_rup, tag=tag,
            seed=rnd.randint(0, models.MAX_SINT_32))
        for tag in tags]
    return prob_rup.id, inserter.saveall(sesrupts)


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
            self.parse_risk_models()
        with transaction.commit_on_success(using='job_init'):
            self.initialize_site_collection()

        self.create_ruptures()
        hc = self.job.get_oqparam()

        self.imts = imts = map(
            from_string, sorted(hc.intensity_measure_types_and_levels))
        n_sites = len(self.site_collection)
        n_gmf = hc.number_of_ground_motion_fields
        output_weight = n_sites * len(imts) * n_gmf
        logs.LOG.info('Expected output size=%s', output_weight)
        models.JobInfo.objects.create(
            oq_job=self.job,
            num_sites=n_sites,
            num_realizations=1,
            num_imts=len(imts),
            num_levels=0,
            input_weight=0,
            output_weight=output_weight)
        self.check_limits(input_weight=0, output_weight=output_weight)
        return 0, output_weight

    def create_ruptures(self):
        self.rupture = get_rupture(models.oqparam(self.job.id))

        # check filtering
        hc = self.hc
        self.sites = filters.filter_sites_by_distance_to_rupture(
            self.rupture, hc.maximum_distance, self.site_collection)
        if self.sites is None:
            raise RuntimeError(
                'All sites where filtered out! '
                'maximum_distance=%s km' % hc.maximum_distance)

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
            tags = ['scenario-%010d' % i for i in xrange(
                    self.hc.number_of_ground_motion_fields)]
            create_db_ruptures(self.rupture, self.ses_coll, tags,
                               self.hc.random_seed)

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
        for ruptures in split_in_blocks(ses_ruptures, self.concurrent_tasks):
            yield self.job.id, ruptures, self.sites, self.imts, self.gmf.id

    def task_completed(self, result):
        """Do nothing"""
