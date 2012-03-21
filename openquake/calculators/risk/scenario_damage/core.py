# Copyright (c) 2010-2012, GEM Foundation.
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

# pylint: disable=W0232

"""
This module performs risk calculations using the scenario
damage assessment approach.
"""

from openquake import logs
from openquake.calculators.risk import general


LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """Scenario Damage method for performing risk calculations."""

    def pre_execute(self):
        """
        Load and store the fragility model
        """
        pass

    def execute(self):
        """
        Dispatch the computation into multiple tasks.
        """

        LOGGER.debug("Executing scenario damage risk computation.")
        tasks = []

        # TODO: Load the fragility model

        for block_id in self.job_ctxt.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s" % (
                    block_id, len(self.job_ctxt.blocks_keys)))

            # TODO: Pass the fragility model to tasks
            task = general.compute_risk.delay(self.job_ctxt.job_id, block_id, fmodel=None)
            tasks.append(a_task)

        for task in tasks:
            task.wait()

            if not task.successful():
                raise Exception(task.result)

        LOGGER.debug("Scenario damage risk computation completed.")

    def compute_risk(self, block_id, **kwargs):
        """
        Compute the results for a single block.
        """

        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        for site in block.sites:
            point = self.job_ctxt.region.grid.point_at(site)
            gmvs = gmvs(self.job_ctxt.job_id, point)

            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            # 0. lookup the correct functions (asset.taxonomy)

            for asset in assets:
                for gmv in gmvs:
                    # 1. compute the damage states for a single gmv
                    # 2. sum the results
                
                    pass
                
                # 3. mean and stddev
                # 4. serialization

    def post_execute(self):
        """
        Export the results to file if the `output-type`
        parameter is set to `xml`.
        """
        pass


def gmvs(job_id, point):
    key = kvs.tokens.ground_motion_values_key(job_id, point)
    return [float(x["mag"]) for x in kvs.get_list_json_decoded(key)]
