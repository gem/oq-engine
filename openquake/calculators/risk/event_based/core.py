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
from celery.exceptions import TimeoutError

from openquake import kvs
from openquake import logs
from openquake.db import models
from openquake.parser import vulnerability
from openquake.calculators.risk import general
from openquake.utils.tasks import distribute

LOGGER = logs.LOG


# Too many public methods
# pylint: disable=R0904

class EventBasedRiskCalculator(general.ProbabilisticRiskCalculator):
    """Calculator for Event-Based Risk computations."""

    def __init__(self, job_ctxt):
        super(EventBasedRiskCalculator, self).__init__(job_ctxt)
        self.vulnerability_curves = None
        self.agg_curve = None

    def execute(self):
        """Execute the job."""

        aggregate_curve = general.AggregateLossCurve()

        region_losses = distribute(general.compute_risk,
                           ("block_id", self.job_ctxt.blocks_keys),
                             tf_args=dict(job_id=self.job_ctxt.job_id))

        [aggregate_curve.append(losses) for losses in region_losses]

        self.agg_curve = aggregate_curve.compute(
            self._tses(), self._time_span(),
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

        # TODO (ac): Confirm this works regardless of the method of hazard calc
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

        self.vulnerability_curves = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        # aggregate the losses for this block
        aggregate_curve = general.AggregateLossCurve()

        for site in block.sites:
            point = self.job_ctxt.region.grid.point_at(site)
            gmf = self._load_ground_motion_field(site)
            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            for asset in assets:
                # loss ratios, used both to produce the curve
                # and to aggregate the losses
                loss_ratios = self._compute_loss_ratios(asset, gmf)

                loss_ratio_curve = self._compute_loss_ratio_curve(
                    asset, gmf, loss_ratios)

                self._store_loss_ratio_curve(
                    point.column, point.row, loss_ratio_curve, asset)

                losses = loss_ratios * asset.value

                aggregate_curve.append(losses)

                if loss_ratio_curve:
                    loss_curve = self._compute_loss_curve(
                        loss_ratio_curve, asset)

                    self._store_loss_curve(point.column, point.row,
                        loss_curve, asset)

                    for loss_poe in general.conditional_loss_poes(
                        self.job_ctxt.params):
                        LOGGER.debug("HERE")
                        LOGGER.debug(loss_poe)
                        general.compute_conditional_loss(
                                self.job_ctxt.job_id, point.column,
                                point.row, loss_curve, asset, loss_poe)

                    if self.job_ctxt.params.get("INSURED_LOSSES"):
                        insured_losses = general.compute_insured_losses(
                            asset, losses)

                        insured_loss_ratio_curve = (
                            self._compute_insured_loss_ratio_curve(
                                insured_losses, asset, gmf))

                        self._store_insured_loss_ratio_curve(point.column,
                            point.row, insured_loss_ratio_curve, asset)

                        insured_loss_curve = self._compute_loss_curve(
                            insured_loss_ratio_curve, asset)

                        self._store_insured_loss_curve(point.column, point.row,
                            insured_loss_curve, asset)

        return aggregate_curve.losses

    def _compute_bcr(self, block_id):
        """
        Calculate and store in the kvs the benefit-cost ratio data for block.

        A value is stored with key :func:`openquake.kvs.tokens.bcr_block_key`.
        See :func:`openquake.risk.job.general.compute_bcr_for_block` for result
        data structure spec.
        """

        # aggregate the losses for this block
        aggregate_curve = general.AggregateLossCurve()
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)
        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)

        def get_loss_curve(site, vuln_function, asset):
            "Compute loss curve basing on GMF data"
            gmvs = self._get_gmvs_at(general.hazard_input_site(
                    self.job_ctxt, site))

            gmf_slice = {"IMLs": gmvs, "TSES": self._tses(),
                    "TimeSpan": self._time_span()}

            loss_ratios = general.compute_loss_ratios(
                vuln_function, gmf_slice, epsilon_provider, asset)
            loss_ratio_curve = general.compute_loss_ratio_curve(
                vuln_function, gmf_slice, epsilon_provider, asset,
                self.job_ctxt.oq_job_profile.loss_histogram_bins,
                loss_ratios=loss_ratios)

            aggregate_curve.append(loss_ratios * asset.value)

            return loss_ratio_curve.rescale_abscissae(asset.value)

        result = general.compute_bcr_for_block(self.job_ctxt, block.sites,
            get_loss_curve, float(self.job_ctxt.params['INTEREST_RATE']),
            float(self.job_ctxt.params['ASSET_LIFE_EXPECTANCY']))

        bcr_block_key = kvs.tokens.bcr_block_key(
            self.job_ctxt.job_id, block_id)

        kvs.set_value_json_encoded(bcr_block_key, result)
        LOGGER.debug('bcr result for block %s: %r', block_id, result)

        return aggregate_curve.losses

    def _load_ground_motion_field(self, site):
        ground_motion_values = self._get_gmvs_at(general.hazard_input_site(
                    self.job_ctxt, site))
        return {"IMLs": ground_motion_values, "TSES": self._tses(),
                "TimeSpan": self._time_span()}

    def _store_insured_loss_curve(self, column, row,
                                  insured_loss_curve, asset):
        key_ic = kvs.tokens.insured_loss_curve_key(
            self.job_ctxt.job_id, row, column, asset.asset_ref)
        kvs.get_client().set(key_ic, insured_loss_curve.to_json())

    def _store_insured_loss_ratio_curve(self, column, row,
                                        insured_loss_ratio_curve, asset):
        key = kvs.tokens.insured_loss_ratio_curve_key(self.job_ctxt.job_id,
            row, column, asset.asset_ref)

        kvs.get_client().set(key, insured_loss_ratio_curve.to_json())

    def _compute_insured_loss_ratio_curve(self, insured_losses, asset, gmf):
        insured_loss_ratio_curve = self._compute_loss_ratio_curve(
            asset, gmf, insured_losses)
        insured_loss_ratio_curve.x_values = (
            insured_loss_ratio_curve.x_values / asset.value)

        return insured_loss_ratio_curve

    def _compute_loss_ratios(self, asset, gmf):
        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)
        vulnerability_function = self.vulnerability_curves.get(
                                                        asset.taxonomy, None)

        if not vulnerability_function:
            LOGGER.error("Unknown vulnerability function %s for asset %s"
                         % (asset.taxonomy, asset.asset_ref))
            return None

        return general.compute_loss_ratios(vulnerability_function, gmf,
            epsilon_provider, asset)

    def _store_loss_ratio_curve(self, column, row, loss_ratio_curve, asset):
        key = kvs.tokens.loss_ratio_key(self.job_ctxt.job_id,
            row, column, asset.asset_ref)
        kvs.get_client().set(key, loss_ratio_curve.to_json())

        LOGGER.debug("Loss ratio curve is %s, write to key %s" %
                     (loss_ratio_curve, key))

    def _compute_loss_ratio_curve(self, asset, gmf, loss_ratios):
        vulnerability_function = self.vulnerability_curves.get(
                    asset.taxonomy, None)

        if not vulnerability_function:
            LOGGER.error("Unknown vulnerability function %s for asset %s"
                         % (asset.taxonomy, asset.asset_ref))

            return None

        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)
        loss_histogram_bins = self.job_ctxt.oq_job_profile.loss_histogram_bins

        loss_ratio_curve = general.compute_loss_ratio_curve(
            vulnerability_function, gmf, epsilon_provider, asset,
            loss_histogram_bins, loss_ratios=loss_ratios)

        return loss_ratio_curve

    def _compute_loss_curve(self, loss_ratio_curve, asset):
        if asset is None:
            return None
        return loss_ratio_curve.rescale_abscissae(asset.value)

    def _store_loss_curve(self, column, row, loss_curve, asset):
        key = kvs.tokens.loss_curve_key(
            self.job_ctxt.job_id, row, column, asset.asset_ref)

        kvs.get_client().set(key, loss_curve.to_json())

        LOGGER.debug("Loss curve is %s, write to key %s" %
                     (loss_curve, key))
