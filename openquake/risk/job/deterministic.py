# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

# pylint: disable=W0232

"""
This module performs risk calculations using the deterministic
event based approach.
"""

from openquake import kvs

from openquake.parser import vulnerability
from openquake.risk import deterministic_event_based as det
from openquake.risk import job as risk_job
from openquake.risk.job import preload, RiskJobMixin

class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing risk calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    @preload
    def execute(self):
        """Entry point for triggering the computation."""
        results = []
        tasks = []

        return [True]
        # print "self", self
        # print "dir(self)", dir(self)
        # print "type(self.calculator)", type(self.calculator)
        # print "self.sites_for_region: ", self.sites_for_region()
        self.vuln_curves = \
            vulnerability.load_vuln_model_from_kvs(self.job_id)

        epsilon_provider = risk_job.EpsilonProvider(self.params)
        # This object will be passed to each task.
        # Each task will update the state of the object.
        # TODO: does this actually work with Celery??
        sum_per_gmf = det.SumPerGroundMotionField(self.vuln_curves, epsilon_provider)
       
        def load_gmf_mags(): 
            gmfs_keys = kvs.tokens.ground_motion_fields_keys(self.job_id)
            gmf_mags = {'IMLs': []}  # will contain all GMF magnitude values for the region
            for gmf_key in gmfs_keys:
                # get a list of the gmf values for a single site
                gmfs_for_site = kvs.get_client().lrange(gmf_key, 0, -1)
                gmf_values = [float(json.JSONDecoder().decode(x)['mag']) for x in gmfs_for_site]
                gmf_mags['IMLs'].extend(gmf_values)

            gmf_mags['IMLs'] = tuple(gmf_mags['IMLs'])
            return gmf_mags

        gmf_mags = load_gmf_mags()

        print "self.blocks_keys", self.blocks_keys
        for block_id in self.blocks_keys:
            # TODO: log message like prob. mixin?
            print "MAKING TASKS"
            print "eps provider",type(sum_per_gmf.epsilon_provider)
            print "self.params", self.params
            print "self", self
            print "dir(self)", dir(self)
            print "self.mixins", self.mixins
            for m in self.mixins: print "dir(m)", dir(m)
            a_task = risk_job.compute_risk.delay(
                self.id, block_id, sum_per_gmf=sum_per_gmf, gmf_mags=gmf_mags)
            tasks.append(a_task)

        for task in tasks:
            task.wait()
            print "task.status:", task.status
            if not task.sucessful():
                raise "Task failed"  # TODO: better error

        print "sum_per_gmf", sum_per_gmf
        print "sum_per_gmf.losses: %s" % sum_per_gmf.losses
        print "Mean loss value", sum_per_gmf.mean
        # print "Standard deviation loss value: %s" % sum_per_gmf.stddev
        return [True]

    def compute_risk(self, block_id, **kwargs):
        """
        """
        print "compute_risk"
        # need to pass this the SumPerGMF obj
        sum_per_gmf = kwargs['sum_per_gmf']
        gmf_mags = kwargs['gmf_mags']
        # TODO: test these assertions
        assert isinstance(sum_per_gmf, det.SumPerGroundMotionField)
        assert isinstance(gmf_mags, dict) 

        print "sum_per_gmf.losses: %s" % sum_per_gmf.losses
        block = job.Block.from_kvs(block_id)

        for point in block.grid(self.region):
            # TODO: get assets for point
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                sum_per_gmf.add(gmf_mags, asset)
            

RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
