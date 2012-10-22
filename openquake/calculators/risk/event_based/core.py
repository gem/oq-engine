# -*- coding: utf-8 -*-

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

# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""Core functionality for Event-Based Risk calculations."""

import geohash
from collections import defaultdict

from openquake.db import models
from openquake import logs, shapes, kvs
from openquake.parser import vulnerability
from openquake.utils.tasks import distribute
from openquake.calculators.risk import general
from risklib import event_based, api

LOGGER = logs.LOG


class EventBasedRiskCalculator(general.ProbabilisticRiskCalculator):
    """Calculator for Event-Based Risk computations."""

    def __init__(self, job_ctxt):
        super(EventBasedRiskCalculator, self).__init__(job_ctxt)
        self.vulnerability_model = None
        self.agg_curve = None

    def execute(self):
        """Execute the job."""

        region_losses = distribute(
            general.compute_risk, ("block_id", self.job_ctxt.blocks_keys),
            tf_args=dict(job_id=self.job_ctxt.job_id))

        if not self.is_benefit_cost_ratio_mode():
            self.agg_curve = event_based.aggregate_loss_curve(
                region_losses, self._tses(), self._time_span(),
                self.job_ctxt.oq_job_profile.loss_histogram_bins)

    def post_execute(self):
        """Perform the following post-execution actions:

        * Write loss curves to XML
        * Save the aggregate loss curve to the database
        * Write BCR output (NOTE: If BCR mode, none of the other artifacts will
          be written.

        Not all of these actions will be executed; this depends on the
        configuration of the job.
        """

        if self.is_benefit_cost_ratio_mode():
            self.write_output_bcr()
            return

        self.write_output()

        # Save the aggregate loss curve to the database:
        job = self.job_ctxt.oq_job

        agg_lc_display_name = (
            'Aggregate Loss Curve for calculation %s' % job.id)
        output = models.Output(
            oq_job=job, owner=job.owner,
            display_name=agg_lc_display_name, db_backed=True,
            output_type='agg_loss_curve')
        output.save()

        loss_curve = models.LossCurve(output=output, aggregate=True)
        loss_curve.save()

        agg_lc_data = models.AggregateLossCurveData(
            loss_curve=loss_curve, losses=self.agg_curve.x_values,
            poes=self.agg_curve.y_values)
        agg_lc_data.save()

    def _tses(self):
        """Return the time representative of the Stochastic Event Set
        specified for this job."""

        histories = int(
            self.job_ctxt.params["NUMBER_OF_SEISMICITY_HISTORIES"])
        realizations = int(
            self.job_ctxt.params["NUMBER_OF_LOGIC_TREE_SAMPLES"])
        num_ses = histories * realizations

        return num_ses * self._time_span()

    def _time_span(self):
        """Return the time span specified for this job."""
        return float(self.job_ctxt.params["INVESTIGATION_TIME"])

    def _get_gmvs_at(self, site):
        """
        Return the ground motion values defined at the given site.

        :param site: location where to load the values.
        :type site: instance of :py:class:`openquake.shapes.Site`
        """

        output_ids = models.Output.objects.filter(
            oq_job=self.job_ctxt.job_id, output_type="gmf")

        gh = geohash.encode(site.latitude, site.longitude, precision=12)
        ground_motion_values = models.GmfData.objects.filter(
                output__in=output_ids).extra(
                where=["ST_GeoHash(location, 12) = %s"],
                params=[gh]).order_by("output")

        return [gmv.ground_motion for gmv in ground_motion_values]

    def _compute_loss(self, block_id):
        """Compute risk for a block of sites, that means:

        * loss ratio curves
        * loss curves
        * conditional losses
        * (partial) aggregate loss curve
        """

        self.vulnerability_model = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        seed, correlation_type = self._get_correlation_type()
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)
        loss_histogram_bins = self.job_ctxt.oq_job_profile.loss_histogram_bins

        def hazard_getter(site):
            gmvs = self._get_gmvs_at(general.hazard_input_site(
                self.job_ctxt, site))

            return {"IMLs": gmvs, "TSES": self._tses(),
                "TimeSpan": self._time_span()}

        assets_getter = lambda site: general.BaseRiskCalculator.assets_at(
            self.job_ctxt.job_id, site)

        probabilistic_event_based_calculator = api.probabilistic_event_based(
            self.vulnerability_model, loss_histogram_bins,
            seed, correlation_type)

        calculator = api.conditional_losses(general.conditional_loss_poes(
            self.job_ctxt.params), probabilistic_event_based_calculator)

        if self.job_ctxt.params.get("INSURED_LOSSES"):
            calculator = api.insured_curves(self.vulnerability_model,
                loss_histogram_bins, seed, correlation_type,
                api.insured_losses(calculator))

        for asset_output in api.compute_on_sites(block.sites,
            assets_getter, hazard_getter, calculator):

            location = asset_output.asset.site

            point = self.job_ctxt.region.grid.point_at(
                shapes.Site(location.x, location.y))

            self._loss_ratio_curve_on_kvs(
                point.column, point.row, asset_output.loss_ratio_curve,
                asset_output.asset)

            self._loss_curve_on_kvs(
                point.column, point.row, asset_output.loss_curve,
                asset_output.asset)

            for poe, loss in asset_output.conditional_losses.items():
                key = kvs.tokens.loss_key(
                    self.job_ctxt.job_id, point.row, point.column,
                    asset_output.asset.asset_ref, poe)

                kvs.get_client().set(key, loss)

            if self.job_ctxt.params.get("INSURED_LOSSES"):
                self._insured_loss_curve_on_kvs(
                    point.column, point.row,
                    asset_output.insured_loss_curve, asset_output.asset)

                self._insured_loss_ratio_curve_on_kvs(
                    point.column, point.row,
                    asset_output.insured_loss_ratio_curve, asset_output.asset)

        return probabilistic_event_based_calculator.aggregate_losses

    def _compute_bcr(self, block_id):
        """
        Calculate and store in the kvs the benefit-cost ratio data for block.

        A value is stored with key :func:`openquake.kvs.tokens.bcr_block_key`.
        See :func:`openquake.risk.job.general.compute_bcr_for_block` for result
        data structure spec.
        """

        result = defaultdict(list)
        seed, correlation_type = self._get_correlation_type()
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)
        loss_histogram_bins = self.job_ctxt.oq_job_profile.loss_histogram_bins

        vulnerability_model_original = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        vulnerability_model_retrofitted = (
            vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id, retrofitted=True))

        assets_getter = lambda site: general.BaseRiskCalculator.assets_at(
            self.job_ctxt.job_id, site)

        def hazard_getter(site):
            gmvs = self._get_gmvs_at(general.hazard_input_site(
                self.job_ctxt, site))

            return {"IMLs": gmvs, "TSES": self._tses(),
                "TimeSpan": self._time_span()}

        bcr = api.bcr(api.probabilistic_event_based(
            vulnerability_model_original, loss_histogram_bins, seed,
            correlation_type), api.probabilistic_event_based(
            vulnerability_model_retrofitted, loss_histogram_bins,seed,
            correlation_type), float(self.job_ctxt.params["INTEREST_RATE"]),
            float(self.job_ctxt.params["ASSET_LIFE_EXPECTANCY"]))

        for asset_output in api.compute_on_sites(
            block.sites, assets_getter, hazard_getter, bcr):

            asset = asset_output.asset

            result[(asset.site.x, asset.site.y)].append(({
                "bcr": asset_output.bcr,
                "eal_original": asset_output.eal_original,
                "eal_retrofitted": asset_output.eal_retrofitted},
                asset.asset_ref))

        bcr_block_key = kvs.tokens.bcr_block_key(
            self.job_ctxt.job_id, block_id)

        result = result.items()
        kvs.set_value_json_encoded(bcr_block_key, result)
        LOGGER.debug("bcr result for block %s: %r", block_id, result)

    def _loss_ratio_curve_on_kvs(self, column, row, loss_ratio_curve, asset):
        """
        Put the loss ratio curve on kvs.
        """

        key = kvs.tokens.loss_ratio_key(self.job_ctxt.job_id,
            row, column, asset.asset_ref)
        kvs.get_client().set(key, loss_ratio_curve.to_json())

        LOGGER.debug("Loss ratio curve is %s, write to key %s" %
                     (loss_ratio_curve, key))

    def _loss_curve_on_kvs(self, column, row, loss_curve, asset):
        """
        Put the loss curve on kvs.
        """

        key = kvs.tokens.loss_curve_key(
            self.job_ctxt.job_id, row, column, asset.asset_ref)

        kvs.get_client().set(key, loss_curve.to_json())

        LOGGER.debug("Loss curve is %s, write to key %s" %
                     (loss_curve, key))

    def _insured_loss_curve_on_kvs(self, column, row,
                                       insured_loss_curve, asset):
        """
        Put the insured loss curve on kvs.
        """

        key_ic = kvs.tokens.insured_loss_curve_key(
            self.job_ctxt.job_id, row, column, asset.asset_ref)
        kvs.get_client().set(key_ic, insured_loss_curve.to_json())

    def _insured_loss_ratio_curve_on_kvs(self, column, row,
                                            insured_loss_ratio_curve, asset):
        """
        Put the insured loss ratio curve on kvs.
        """
        key = kvs.tokens.insured_loss_ratio_curve_key(self.job_ctxt.job_id,
                row, column, asset.asset_ref)

        kvs.get_client().set(key, insured_loss_ratio_curve.to_json())
