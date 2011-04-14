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

        LOGGER.debug("Executing deterministic risk computation.")
        LOGGER.debug("This will calculate mean and standard deviation loss"
            "values for the region defined in the job config.")

        block_losses = []
        tasks = []

        vuln_model = \
            vulnerability.load_vuln_model_from_kvs(self.job_id)

        epsilon_provider = risk_job.EpsilonProvider(self.params)

        for block_id in self.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s"
                % (block_id, len(self.blocks_keys)))
            a_task = risk_job.compute_risk.delay(
                self.id, block_id, vuln_model=vuln_model,
                epsilon_provider=epsilon_provider)
            tasks.append(a_task)

        for task in tasks:
            task.wait()
            if not task.successful():
                raise Exception(task.result)

            block_loss = task.result

            # do some basic validation on our results
            assert block_loss is not None, "Expected a result != None"
            assert isinstance(block_loss, numpy.ndarray), \
                "Expected a numpy array"

            # our result should be a 1-dimensional numpy.array of loss values
            block_losses.append(task.result)

        # combine the block losses to get losses for the whole region
        region_losses = sum(block_losses)

        mean_region_loss = numpy.mean(region_losses)
        stddev_region_loss = numpy.std(region_losses)

        # For now, just print these values.
        # These are not debug statements; please don't remove them!
        print "Mean region loss value: %s" % mean_region_loss
        print "Standard deviation region loss value: %s" % stddev_region_loss
        return [True]

    def compute_risk(self, block_id, **kwargs):
        """
        For a given block of sites, compute loss values for all assets in the
        block. This computation will yield a single loss value per realization
        for the region block.

        The GMF data for each realization is stored in the KVS by the preceding
        deterministic hazard calculation.

        :param block_id: id of the region block data we need to pull from the
            KVS
        :type block_id: str
        :keyword vuln_model:
            dict of :py:class:`openquake.shapes.VulnerabilityFunction` objects,
            keyed by the vulnerability function name as a string
        :keyword epsilon_provider:
            :py:class:`openquake.risk.job.EpsilonProvider` object

        :returns: 1-dimensional :py:class:`numpy.array` of loss values for this
            region block (again, 1 value per realization)
        """
        vuln_model = kwargs['vuln_model']
        epsilon_provider = kwargs['epsilon_provider']

        block = job.Block.from_kvs(block_id)

        # this a numpy.array
        # 1 value to represent block losses for each realization
        block_losses = self._compute_loss_for_block(
            block, vuln_model, epsilon_provider)

        return block_losses

    def _compute_loss_for_block(self, block, vuln_model, epsilon_provider):
        """
        Compute the sum of losses for a block of a region. The result is a
        :py:class:`numpy.array` of loss values (floats), 1 per realization of
        the calculation.

        :param block: a block of sites represented by a
            :py:class:`openquake.job.Block` object
        :param vuln_model:
            dict of :py:class:`openquake.shapes.VulnerabilityFunction` objects,
            keyed by the vulnerability function name as a string
        :param epsilon_provider:
            :py:class:`openquake.risk.job.EpsilonProvider` object

        """
        sum_per_gmf = det.SumPerGroundMotionField(vuln_model, epsilon_provider)
        for point in block.grid(self.region):
            gmvs = load_gmvs_for_point(self.id, point)
            assets_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = [json.JSONDecoder().decode(x) for x in \
                kvs.get_client().lrange(assets_key, 0, -1)]
            for asset in asset_list:
                # the SumPerGroundMotionField add() method expects a dict
                # with a single key ('IMLs') and value set to the sequence of
                # GMVs
                sum_per_gmf.add({'IMLs': gmvs}, asset)
        return sum_per_gmf.losses


def load_gmvs_for_point(job_id, point):
    """
    From the KVS, load all the ground motion values for the given point. We
    expect one ground motion value per realization of the calculation.
    Since there can be tens of thousands of realizations, this could return a
    large list.

    Note(LB): In the future, we may want to refactor this (and the code which
    uses the values) to use a generator instead.

    :param point: :py:class:`openquake.shapes.GridPoint` object
    :returns: List of ground motion values (as floats). Each value represents a
        realization of the calculation for a single point.
    """
    gmfs_key = kvs.tokens.ground_motion_value_key(job_id, point)
    gmfs = kvs.get_client().lrange(gmfs_key, 0, -1)
    return [float(json.JSONDecoder().decode(x)['mag']) for x in gmfs]


RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
