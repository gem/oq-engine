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

"""Core functionality for Classical Risk calculations."""

import geohash
from collections import defaultdict
from celery.exceptions import TimeoutError

from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.db import models
from openquake.parser import vulnerability
from openquake.calculators.risk.general import (
    ProbabilisticRiskCalculator, compute_risk, Block,
    hazard_input_site, BaseRiskCalculator)

from risklib import api


LOGGER = logs.LOG


def conditional_loss_poes(params):
    """Return the PoE(s) specified in the configuration file used to
    compute the conditional loss."""

    return [float(x) for x in params.get(
        "CONDITIONAL_LOSS_POE", "").split()]


class ClassicalRiskCalculator(ProbabilisticRiskCalculator):
    """Calculator for Classical Risk computations."""

    def execute(self):
        """Core Classical Risk calculation starts here."""
        celery_tasks = []
        for block_id in self.job_ctxt.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.job_ctxt.blocks_keys)))
            celery_tasks.append(
                compute_risk.delay(self.job_ctxt.job_id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs).
        for task in celery_tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait()
                if not task.successful():
                    raise Exception(task.result)

            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return

        if self.is_benefit_cost_ratio_mode():
            self.write_output_bcr()
        else:
            self.write_output()

    def _get_db_curve(self, site):
        """Read hazard curve data from the DB"""
        gh = geohash.encode(site.latitude, site.longitude, precision=12)
        job = models.OqJob.objects.get(id=self.job_ctxt.job_id)
        hc = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job,
            hazard_curve__statistic_type='mean').extra(
            where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

        return zip(job.profile().imls, hc.poes)

    def _compute_loss(self, block_id):
        """
        Calculate and store in the kvs the loss data.
        """
        block = Block.from_kvs(self.job_ctxt.job_id, block_id)

        vulnerability_model = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        steps = self.job_ctxt.oq_job_profile.lrem_steps_per_interval

        assets_getter = lambda site: BaseRiskCalculator.assets_at(
            self.job_ctxt.job_id, site)

        hazard_getter = lambda site: (
            self._get_db_curve(hazard_input_site(self.job_ctxt, site)))

        calculator = api.conditional_losses(
            conditional_loss_poes(self.job_ctxt.params),
            api.classical(vulnerability_model, steps=steps))

        for asset_output in api.compute_on_sites(block.sites,
            assets_getter, hazard_getter, calculator):

            location = asset_output.asset.site

            point = self.job_ctxt.region.grid.point_at(
                shapes.Site(location.x, location.y))

            loss_key = kvs.tokens.loss_curve_key(
                self.job_ctxt.job_id, point.row,
                point.column, asset_output.asset.asset_ref)

            kvs.get_client().set(loss_key, asset_output.loss_curve.to_json())

            loss_ratio_key = kvs.tokens.loss_ratio_key(self.job_ctxt.job_id,
                point.row, point.column, asset_output.asset.asset_ref)

            kvs.get_client().set(loss_ratio_key,
                asset_output.loss_ratio_curve.to_json())

            for poe, loss in asset_output.conditional_losses.items():
                key = kvs.tokens.loss_key(
                    self.job_ctxt.job_id, point.row, point.column,
                    asset_output.asset.asset_ref, poe)

                kvs.get_client().set(key, loss)

    def _compute_bcr(self, block_id):
        """
        Calculate and store in the kvs the benefit-cost ratio data for block.

        A value is stored with key :func:`openquake.kvs.tokens.bcr_block_key`.
        See :func:`openquake.risk.job.general.compute_bcr_for_block` for result
        data structure spec.
        """

        result = defaultdict(list)
        block = Block.from_kvs(self.job_ctxt.job_id, block_id)

        vulnerability_model_original = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        vulnerability_model_retrofitted = (
            vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id, retrofitted=True))

        steps = self.job_ctxt.oq_job_profile.lrem_steps_per_interval

        assets_getter = lambda site: BaseRiskCalculator.assets_at(
            self.job_ctxt.job_id, site)

        hazard_getter = lambda site: (
            self._get_db_curve(hazard_input_site(self.job_ctxt, site)))

        bcr = api.bcr(api.classical(vulnerability_model_original, steps=steps),
            api.classical(vulnerability_model_retrofitted, steps=steps),
            float(self.job_ctxt.params["INTEREST_RATE"]),
            float(self.job_ctxt.params["ASSET_LIFE_EXPECTANCY"]))

        for asset_output in api.compute_on_sites(
            block.sites, assets_getter, hazard_getter, bcr):

            asset = asset_output.asset

            result[(asset.site.x, asset.site.y)].append(({
                "bcr": asset_output.bcr,
                "eal_original": asset_output.eal_original,
                "eal_retrofitted": asset_output.eal_retrofitted},
                asset.asset_ref))

        bcr = result.items()
        bcr_block_key = kvs.tokens.bcr_block_key(
            self.job_ctxt.job_id, block_id)

        kvs.set_value_json_encoded(bcr_block_key, bcr)
        LOGGER.debug("bcr result for block %s: %r", block_id, bcr)

        return True
