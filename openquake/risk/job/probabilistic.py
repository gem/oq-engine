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

import json

from celery.exceptions import TimeoutError

from openquake import job
from openquake import kvs
from openquake import logs
from openquake import shapes

from openquake.risk import common
from openquake.risk import probabilistic_event_based as prob
from openquake.parser import vulnerability

from openquake.risk.job import aggregate_loss_curve
from openquake.risk.job import general


LOGGER = logs.LOG
DEFAULT_CONDITIONAL_LOSS_POE = 0.01


class ProbabilisticEventMixin(): # pylint: disable=W0232,W0201
    """Mixin for Probalistic Event Risk Job."""

# TODO (ac): Improve doc!
    @general.preload
    @general.output
    def execute(self):
        """Execute the job."""

        aggregate_curve = prob.AggregateLossCurve()

        results = []
        tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("Starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))

            tasks.append(general.compute_risk.delay(self.id, block_id))

        for task in tasks:
            try:
                # TODO (chris): Figure out where to put that timeout
                task.wait(timeout=None)

                aggregate_curve.append(task.result)
            except TimeoutError:
                # TODO (jmc): Cancel and respawn this task
                return []

# TODO (ac): Extract in a method! And test it!
        time_span = float(self['INVESTIGATION_TIME'])
        histories = int(self["NUMBER_OF_SEISMICITY_HISTORIES"])
        realizations = int(self["NUMBER_OF_LOGIC_TREE_SAMPLES"])

        num_ses = histories * realizations
        tses = num_ses * time_span

        curve = aggregate_curve.compute(tses, time_span)
        aggregate_loss_curve.compute_aggregate_curve(self, curve)

        return results

    def slice_gmfs(self, block_id):
        """Load and collate GMF values for all sites in this block. """
        # TODO(JMC): Confirm this works regardless of the method of haz calc.
        histories = int(self['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self['NUMBER_OF_LOGIC_TREE_SAMPLES'])
        num_ses = histories * realizations

        block = job.Block.from_kvs(block_id)
        sites_list = block.sites
        gmfs = {}
        for site in sites_list:
            risk_point = self.region.grid.point_at(site)
            key = "%s!%s" % (risk_point.row, risk_point.column)
            gmfs[key] = []

        for i in range(0, histories):
            for j in range(0, realizations):
                key = kvs.generate_product_key(
                        self.id, kvs.tokens.STOCHASTIC_SET_TOKEN, "%s!%s" %
                            (i, j))
                fieldset = shapes.FieldSet.from_json(kvs.get(key),
                    self.region.grid)

                for field in fieldset:
                    for key in gmfs.keys():
                        (row, col) = key.split("!")
                        gmfs[key].append(field.get(int(row), int(col)))

        for key, gmf_slice in gmfs.items():
            (row, col) = key.split("!")
            key_gmf = kvs.tokens.gmfs_key(self.id, col, row)
            LOGGER.debug("GMF_SLICE for %s X %s : \n\t%s" % (
                    col, row, gmf_slice))
            timespan = float(self['INVESTIGATION_TIME'])
            gmf = {"IMLs": gmf_slice, "TSES": num_ses * timespan,
                    "TimeSpan": timespan}
            kvs.set_value_json_encoded(key_gmf, gmf)

# TODO (ac): Improve doc!
    def compute_risk(self, block_id, **kwargs):  # pylint: disable=W0613
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in kvs:
         1) list of sites
         2) gmfs
         3) exposure portfolio (=assets)
         4) vulnerability
        """

        conditional_loss_poes = [float(x) for x in self.params.get(
                "CONDITIONAL_LOSS_POE", "0.01").split()]

        self.slice_gmfs(block_id)

        self.vuln_curves = vulnerability.load_vuln_model_from_kvs(
            self.job_id)

        # TODO (jmc): DONT assume that hazard and risk grid are the same
        block = job.Block.from_kvs(block_id)

        # aggregate the losses for this block
        aggregate_curve = prob.AggregateLossCurve()

        for point in block.grid(self.region):
            key = kvs.generate_product_key(self.job_id,
                    kvs.tokens.GMF_KEY_TOKEN, point.column, point.row)

            gmf_slice = kvs.get_value_json_decoded(key)
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                LOGGER.debug("Processing asset %s" % (asset))

                # loss ratios, used both to produce the curve
                # and to aggregate the losses
                loss_ratios = self.compute_loss_ratios(asset, gmf_slice)

                loss_ratio_curve = self.compute_loss_ratio_curve(
                    point.column, point.row, asset, gmf_slice, loss_ratios)

                aggregate_curve.append(loss_ratios * asset["assetValue"])

                if loss_ratio_curve is not None:
                    # compute loss curve
                    loss_curve = self.compute_loss_curve(
                        point.column, point.row, loss_ratio_curve, asset)

                    for loss_poe in conditional_loss_poes:
                        self.compute_conditional_loss(point.column, point.row,
                                loss_curve, asset, loss_poe)

        return aggregate_curve.losses

    def compute_loss_ratios(self, asset, gmf_slice):
# TODO (ac): Add documentation!
        epsilon_provider = general.EpsilonProvider(self.params)

# TODO (ac): Extract to a method, and test it!
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
                self.id, row, col, asset["assetID"], loss_poe)

        LOGGER.debug("Conditional loss is %s, write to key %s" %
                (loss_conditional, key))

        kvs.set(key, loss_conditional)

    def compute_loss_ratio_curve(self, col, row, asset, gmf_slice, loss_ratios):
        """Compute the loss ratio curve for a single asset."""

        # fail if the asset has an unknown vulnerability code
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

        key = kvs.tokens.loss_ratio_key(self.id, row, col, asset["assetID"])
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
        key = kvs.tokens.loss_curve_key(self.id, row, column, asset["assetID"])

        LOGGER.debug("Loss curve is %s, write to key %s" % (loss_curve, key))
        kvs.set(key, loss_curve.to_json())

        return loss_curve


general.RiskJobMixin.register("Event Based", ProbabilisticEventMixin)
