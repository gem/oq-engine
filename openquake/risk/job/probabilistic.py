# -*- coding: utf-8 -*-

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

# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Probabilistic Event Mixin: defines the behaviour of a Job. Calls the
compute_risk task
"""

from numpy import zeros

from celery.exceptions import TimeoutError

from openquake import kvs
from openquake import logs
from openquake import shapes

from openquake.risk import common
from openquake.risk import probabilistic_event_based as prob
from openquake.parser import vulnerability

from openquake.risk.job import aggregate_loss_curve
from openquake.risk.job import general

from openquake.db import models

LOGGER = logs.LOG
DEFAULT_CONDITIONAL_LOSS_POE = 0.01


class ProbabilisticEventMixin(): # pylint: disable=W0232,W0201
    """Mixin for Probalistic Event Risk Job."""

    @general.preload
    @general.output
    def execute(self):
        """Execute the job."""

        aggregate_curve = prob.AggregateLossCurve()

        tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("Starting task block, block_id = %s of %s"
                    % (block_id, len(self.blocks_keys)))

            tasks.append(general.compute_risk.delay(self.job_id, block_id))

        for task in tasks:
            try:
                # TODO (chris): Figure out where to put that timeout
                task.wait(timeout=None)

                aggregate_curve.append(task.result)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return

        curve = aggregate_curve.compute(self._tses(), self._time_span())
        aggregate_loss_curve.plot_aggregate_curve(self, curve)

    def _tses(self):
        """Return the time representative of the Stochastic Event Set
        specified for this job."""

# TODO (ac): Confirm this works regardless of the method of hazard calc
        histories = int(self["NUMBER_OF_SEISMICITY_HISTORIES"])
        realizations = int(self["NUMBER_OF_LOGIC_TREE_SAMPLES"])
        num_ses = histories * realizations

        return num_ses * self._time_span()

    def _time_span(self):
        """Return the time span specified for this job."""
        return float(self["INVESTIGATION_TIME"])

    def _gmf_db_list(self, job_id):  # pylint: disable=R0201
        """Returns a list of the output IDs of all computed GMFs"""

        ids = models.Output.objects.filter(
            oq_job=job_id, output_type='gmf').values_list('id', flat=True)

        return list(ids)

    def _get_db_gmf(self, gmf_id):
        """Returns a field for the given GMF"""
        grid = self.region.grid
        field = zeros((grid.rows, grid.columns))

        gmf_sites = models.GmfData.objects.filter(output=gmf_id)

        for gmf_site in gmf_sites:
            loc = gmf_site.location
            site = shapes.Site(loc.x, loc.y)
            grid_point = grid.point_at(site)

            field[grid_point.row][grid_point.column] = gmf_site.ground_motion

        return shapes.Field(field)

    def _sites_to_gmf_keys(self, sites):
        """Returns the GMF keys "row!col" for the given site list"""
        keys = []

        for site in sites:
            risk_point = self.region.grid.point_at(site)
            key = "%s!%s" % (risk_point.row, risk_point.column)
            keys.append(key)

        return keys

    def _get_db_gmfs(self, sites, job_id):
        """Aggregates GMF data from the DB by site"""
        all_gmfs = self._gmf_db_list(job_id)
        gmf_keys = self._sites_to_gmf_keys(sites)
        gmfs = dict((k, []) for k in gmf_keys)

        for gmf_id in all_gmfs:
            field = self._get_db_gmf(gmf_id)

            for key in gmfs.keys():
                (row, col) = key.split("!")
                gmfs[key].append(field.get(int(row), int(col)))

        return gmfs

    def _get_kvs_gmfs(self, sites, histories, realizations):
        """Aggregates GMF data from the KVS by site"""
        gmf_keys = self._sites_to_gmf_keys(sites)
        gmfs = dict((k, []) for k in gmf_keys)

        for i in range(0, histories):
            for j in range(0, realizations):
                key = kvs.tokens.stochastic_set_key(self.job_id, i, j)
                fieldset = shapes.FieldSet.from_json(kvs.get(key),
                    self.region.grid)

                for field in fieldset:
                    for key in gmfs.keys():
                        (row, col) = key.split("!")
                        gmfs[key].append(field.get(int(row), int(col)))

        return gmfs

    def slice_gmfs(self, block_id):
        """Load and collate GMF values for all sites in this block. """
        block = general.Block.from_kvs(block_id)
        gmfs = self._get_db_gmfs(block.sites, self.job_id)

        for key, gmf_slice in gmfs.items():
            (row, col) = key.split("!")
            key_gmf = kvs.tokens.gmf_set_key(self.job_id, col, row)
            LOGGER.debug("GMF_SLICE for %s X %s : \n\t%s" % (
                    col, row, gmf_slice))
            gmf = {"IMLs": gmf_slice, "TSES": self._tses(),
                    "TimeSpan": self._timespan()}
            kvs.set_value_json_encoded(key_gmf, gmf)

    def compute_risk(self, block_id, **kwargs):  # pylint: disable=W0613
        """Compute risk for a block of sites, that means:

        * loss ratio curves
        * loss curves
        * conditional losses
        * (partial) aggregate loss curve
        """

        self.slice_gmfs(block_id)

        self.vuln_curves = vulnerability.load_vuln_model_from_kvs(
            self.job_id)

        block = general.Block.from_kvs(block_id)

        # aggregate the losses for this block
        aggregate_curve = prob.AggregateLossCurve()

        for point in block.grid(self.region):
            key = kvs.tokens.gmf_set_key(self.job_id, point.column, point.row)
            gmf_slice = kvs.get_value_json_decoded(key)

            asset_key = kvs.tokens.asset_key(
                self.job_id, point.row, point.column)

            for asset in kvs.get_list_json_decoded(asset_key):
                LOGGER.debug("Processing asset %s" % (asset))

                # loss ratios, used both to produce the curve
                # and to aggregate the losses
                loss_ratios = self.compute_loss_ratios(asset, gmf_slice)

                loss_ratio_curve = self.compute_loss_ratio_curve(
                    point.column, point.row, asset, gmf_slice, loss_ratios)

                aggregate_curve.append(loss_ratios * asset["assetValue"])

                if loss_ratio_curve is not None:
                    loss_curve = self.compute_loss_curve(
                        point.column, point.row, loss_ratio_curve, asset)

                    for loss_poe in self._conditional_loss_poes():
                        self.compute_conditional_loss(point.column, point.row,
                                loss_curve, asset, loss_poe)

        return aggregate_curve.losses

    def _conditional_loss_poes(self):
        """Return the PoE(s) specified in the configuration file used to
        compute the conditional loss."""

        return [float(x) for x in self.params.get(
            "CONDITIONAL_LOSS_POE", "0.01").split()]

    def compute_loss_ratios(self, asset, gmf_slice):
        """For a given asset and ground motion field, computes
        the loss ratios used to obtain the related loss ratio curve
        and aggregate loss curve."""

        epsilon_provider = general.EpsilonProvider(self.params)

        vuln_function = self.vuln_curves.get(
            asset["vulnerabilityFunctionReference"], None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"], asset["assetID"]))

            return None

        return prob.compute_loss_ratios(
            vuln_function, gmf_slice, epsilon_provider, asset)

    def compute_conditional_loss(self, col, row, loss_curve, asset, loss_poe):
        """Compute the conditional loss for a loss curve and Probability of
        Exceedance (PoE)."""

        loss_conditional = common.compute_conditional_loss(
            loss_curve, loss_poe)

        key = kvs.tokens.loss_key(
                self.job_id, row, col, asset["assetID"], loss_poe)

        LOGGER.debug("Conditional loss is %s, write to key %s" %
                (loss_conditional, key))

        kvs.set(key, loss_conditional)

    def compute_loss_ratio_curve(
            self, col, row, asset, gmf_slice, loss_ratios):
        """Compute the loss ratio curve for a single asset."""

        vuln_function = self.vuln_curves.get(
            asset["vulnerabilityFunctionReference"], None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"], asset["assetID"]))

            return None

        epsilon_provider = general.EpsilonProvider(self.params)

        loss_ratio_curve = prob.compute_loss_ratio_curve(
                vuln_function, gmf_slice, epsilon_provider, asset,
                self._get_number_of_samples(), loss_ratios=loss_ratios)

        # NOTE (jmc): Early exit if the loss ratio is all zeros
        if not False in (loss_ratio_curve.ordinates == 0.0):
            return None

        key = kvs.tokens.loss_ratio_key(
            self.job_id, row, col, asset["assetID"])

        kvs.set(key, loss_ratio_curve.to_json())

        LOGGER.debug("Loss ratio curve is %s, write to key %s" %
                (loss_ratio_curve, key))

        return loss_ratio_curve

    def _get_number_of_samples(self):
        """Return the number of samples used to compute the loss ratio
        curve specified by the PROB_NUM_OF_SAMPLES parameter.

        Return None if the parameter is not specified, or empty or
        the value can't be casted to int.
        """

        number_of_samples = None
        raw_value = getattr(self, "PROB_NUM_OF_SAMPLES", None)

        if raw_value:
            try:
                number_of_samples = int(raw_value)
            except ValueError:
                LOGGER.error("PROB_NUM_OF_SAMPLES %s can't be converted "
                             "to int, using default value..." % raw_value)

        return number_of_samples

    def compute_loss_curve(self, column, row, loss_ratio_curve, asset):
        """Compute the loss curve for a single asset."""

        if asset is None:
            return None

        loss_curve = loss_ratio_curve.rescale_abscissae(asset["assetValue"])

        key = kvs.tokens.loss_curve_key(
            self.job_id, row, column, asset["assetID"])

        LOGGER.debug("Loss curve is %s, write to key %s" % (loss_curve, key))
        kvs.set(key, loss_curve.to_json())

        return loss_curve


general.RiskJobMixin.register("Event Based", ProbabilisticEventMixin)
