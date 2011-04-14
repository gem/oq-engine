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

        self.vuln_model = \
            vulnerability.load_vuln_model_from_kvs(self.job_id)

        epsilon_provider = risk_job.EpsilonProvider(self.params)
        # A copy of this object will be passed to each task.
        # Note: Each task needs to return the loss values tracked by this
        # object; then we need to combine the results for our final
        # calculation.
        sum_per_gmf = det.SumPerGroundMotionField(
            self.vuln_model, epsilon_provider)

        for block_id in self.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s"
                % (block_id, len(self.blocks_keys)))
            a_task = risk_job.compute_risk.delay(
                self.id, block_id, sum_per_gmf=sum_per_gmf)
            a_task = risk_job.computE_risk.delay(
                self.id, block_id, vuln_model=self.vuln_model,
                epsilon_provider=epsilon_provider)
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
        print "Loss Map XML file: %s" % xml_output_path
        print "Mean loss value", sum_per_gmf.mean
        print "Standard deviation loss value: %s" % sum_per_gmf.stddev
        return [True]


    def compute_risk(self, block_id, **kwargs):
        """
        """
        vuln_model = kwargs['vuln_model']
        epsilon_provider = kwargs['epsilon_provider']

        block = job.Block.from_kvs(block_id)
        horizontal = self._compute_loss_per_realization(
            block, vuln_model, epsilon_provider)
        # for point in block.grid(self.region):
        #     # each 'point' is a GridPoint object

        
    def _compute_loss_per_realization(block, vuln_model, epsilon_provider):
        # HORIZONTAL
        pass
        sum_per_gmf = det.SumPerGroundMotionField(vuln_model, epsilon_provider)
        """
 
        realization_loss_sums = []
        for each realization:
            realization_loss_sum = 0
            for each point in block:
                for each asset at point:
                    vuln_function = vuln_model[asset['vulnFunctionReference']]
                    location_iml = *get it*
                    loss_ratio = vuln_function.get loss ratio(location_iml)
                    loss = loss_ration * asset['value']
                    realization_loss_sum += loss
            realization_loss_sums.append(loss)
        
       
        :param block_id: ID for retrieving a the site block from the kvs for this task
        :type block_id: str

        :returns:
            * the losses for this block (as a 1d numpy.array)
            * a list of loss map node data (which can be serialized to various
              kinds of output)
        """


    def compute_risk_old(self, block_id, **kwargs):
        """
       
        :param block_id: ID for retrieving a the site block from the kvs for this task
        :type block_id: str
        :keyword vuln_model:
        :keyword epsilon_provider:

        :returns:
            * the losses for this block (as a 1d numpy.array)
            * a list of loss map node data (which can be serialized to various
              kinds of output)
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
                # this stores mean & stddev loss values for each asset
                loss = {'mean_loss': float(), 'stddev': float()}

                sum_per_gmf.add(gmf_mags, asset)

        return sum_per_gmf.losses

    def _compute_loss_per_asset(self):
        # VERTICAL
        pass
                asset_dict = dict()
                asset_dict['assetID'] = asset['assetID']
                if asset.has_key('assetValueUnit'):
                    asset_dict['unit'] = asset['assetValueUnit']

                site = self.region.grid.site_at(point)
                loss['mean_loss'] = sum_per_gmf.mean
                loss['stddev'] = sum_per_gmf.stddev

                loss_map_node_data.append((site, (loss, asset_dict)))

        return sum_per_gmf.losses, loss_map_node_data


RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
