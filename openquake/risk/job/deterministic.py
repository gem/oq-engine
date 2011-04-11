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


import json
import numpy

from openquake import job
from openquake import kvs
from openquake import logs

from openquake.parser import vulnerability
from openquake.risk import deterministic_event_based as det
from openquake.risk import job as risk_job
from openquake.risk.job import preload, RiskJobMixin

LOGGER = logs.LOG


class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing risk calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    @preload
    def execute(self):
        """Entry point for triggering the computation."""

        loss_results = []
        tasks = []

        self.vuln_curves = \
            vulnerability.load_vuln_model_from_kvs(self.job_id)

        epsilon_provider = risk_job.EpsilonProvider(self.params)
        # A copy of this object will be passed to each task.
        # Note: Each task needs to return the loss values tracked by this
        # object; then we need to combine the results for our final
        # calculation.
        sum_per_gmf = det.SumPerGroundMotionField(
            self.vuln_curves, epsilon_provider)

        for block_id in self.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s"
                % (block_id, len(self.blocks_keys)))
            a_task = risk_job.compute_risk.delay(
                self.id, block_id, sum_per_gmf=sum_per_gmf)
            tasks.append(a_task)

        for task in tasks:
            task.wait()
            if not task.successful():
                raise Exception(task.result)
            # our result is a 1-dimensional numpy.array of loss values
            loss_results.append(task.result)

        # reduce the task results to a single result
        # Note: object state needs to updated with the task results
        sum_per_gmf.losses = numpy.array([])
        for result in loss_results:
            sum_per_gmf.losses = \
                numpy.concatenate((sum_per_gmf.losses, result))
            
        # For now, just print these values.
        # These are not debug statements; please don't remove them!
        print "Mean loss value", sum_per_gmf.mean
        print "Standard deviation loss value: %s" % sum_per_gmf.stddev
        return [True]

    def compute_risk(self, block_id, **kwargs):
        """
        
        :returns: the losses for this block (as a 1d numpy.array)
        """
        sum_per_gmf = kwargs['sum_per_gmf']
        assert isinstance(sum_per_gmf, det.SumPerGroundMotionField)

        block = job.Block.from_kvs(block_id)

        for point in block.grid(self.region):
            # load the gmf data for this site
            gmfs_key = kvs.tokens.ground_motion_value_key(self.id, point)
            gmf_mags = {'IMLs': None}
            # load raw json gmf values
            gmf_raw = kvs.get_client().lrange(gmfs_key, 0, -1)
            gmf_mags['IMLs'] = \
                [float(json.JSONDecoder().decode(x)['mag']) for x in gmf_raw]
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                sum_per_gmf.add(gmf_mags, asset)

        return sum_per_gmf.losses


RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
