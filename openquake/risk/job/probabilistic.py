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
from openquake.risk import probabilistic_event_based
from openquake.parser import vulnerability

from openquake.risk.job import aggregate_loss_curve
from openquake.risk.job import general

from openquake.db.alchemy.db_utils import get_db_session
from openquake.db.alchemy import models
from sqlalchemy import func as sqlfunc

LOGGER = logs.LOG
DEFAULT_CONDITIONAL_LOSS_POE = 0.01


class ProbabilisticEventMixin():
    # TODO (al-maisan) Consider refactoring our job system to make use of
    # dependency injection techniques as opposed to monkey patching python's
    # internal class structures. See also:
    #       https://github.com/gem/openquake/issues/56
    # pylint: disable=W0232,W0201
    """Mixin for Probalistic Event Risk Job"""

    @general.preload
    @general.output
    def execute(self):
        """ Execute a ProbabilisticLossRatio Job """

        tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            tasks.append(general.compute_risk.delay(self.job_id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs)
        for task in tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait(timeout=None)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return

        # the aggregation must be computed after the slicing
        # of the gmfs has been completed
        aggregate_loss_curve.compute_aggregate_curve(self)

        # TODO(jmc): Move output from being a decorator

    def _gmf_db_list(self, job_id):  # pylint: disable=R0201
        """Returns a list of the output IDs of all computed GMFs"""
        session = get_db_session("reslt", "reader")

        ids = session.query(models.Output.id) \
            .filter(models.Output.oq_job_id == job_id) \
            .filter(models.Output.output_type == 'gmf')

        return [row[0] for row in ids]

    def _get_db_gmf(self, gmf_id):
        """Returns a field for the given GMF"""
        session = get_db_session("reslt", "reader")
        grid = self.region.grid
        field = zeros((grid.rows, grid.columns))

        sites = session.query(
                sqlfunc.ST_X(models.GMFData.location),
                sqlfunc.ST_Y(models.GMFData.location),
                models.GMFData.ground_motion) \
            .filter(models.GMFData.output_id == gmf_id)

        for x, y, value in sites:
            site = shapes.Site(x, y)
            grid_point = grid.point_at(site)

            field[grid_point.row][grid_point.column] = value

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
        # TODO(JMC): Confirm this works regardless of the method of haz calc.
        histories = int(self['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self['NUMBER_OF_LOGIC_TREE_SAMPLES'])
        num_ses = histories * realizations

        block = general.Block.from_kvs(block_id)

        gmfs = self._get_db_gmfs(block.sites, self.job_id)

        for key, gmf_slice in gmfs.items():
            (row, col) = key.split("!")
            key_gmf = kvs.tokens.gmf_set_key(self.job_id, col, row)
            LOGGER.debug("GMF_SLICE for %s X %s : \n\t%s" % (
                    col, row, gmf_slice))
            timespan = float(self['INVESTIGATION_TIME'])
            gmf = {"IMLs": gmf_slice, "TSES": num_ses * timespan,
                    "TimeSpan": timespan}
            kvs.set_value_json_encoded(key_gmf, gmf)

    def compute_risk(self, block_id, **kwargs):  # pylint: disable=W0613
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in kvs:
         1) list of sites
         2) gmfs
         3) exposure portfolio (=assets)
         4) vulnerability

        TODO(fab): make conditional_loss_poe (set of probabilities of
        exceedance for which the loss computation is done)
        a list of floats, and read it from the job configuration.
        """

        conditional_loss_poes = [float(x) for x in self.params.get(
                    'CONDITIONAL_LOSS_POE', "0.01").split()]
        self.slice_gmfs(block_id)

        #pylint: disable=W0201
        self.vuln_curves = \
                vulnerability.load_vuln_model_from_kvs(self.job_id)

        # TODO(jmc): DONT assumes that hazard and risk grid are the same
        block = general.Block.from_kvs(block_id)

        for point in block.grid(self.region):
            key = kvs.tokens.gmf_set_key(self.job_id, point.column, point.row)
            gmf_slice = kvs.get_value_json_decoded(key)

            asset_key = kvs.tokens.asset_key(
                self.job_id, point.row, point.column)
            for asset in kvs.get_list_json_decoded(asset_key):
                LOGGER.debug("processing asset %s" % (asset))
                loss_ratio_curve = self.compute_loss_ratio_curve(
                        point.column, point.row, asset, gmf_slice)
                if loss_ratio_curve is not None:

                    # compute loss curve
                    loss_curve = self.compute_loss_curve(
                            point.column, point.row,
                            loss_ratio_curve, asset)

                    for loss_poe in conditional_loss_poes:
                        self.compute_conditional_loss(point.column, point.row,
                                loss_curve, asset, loss_poe)

        return True

    def compute_conditional_loss(self, col, row, loss_curve, asset, loss_poe):
        """ Compute the conditional loss for a loss curve and probability of
        exceedance """

        loss_conditional = common.compute_conditional_loss(
                loss_curve, loss_poe)

        key = kvs.tokens.loss_key(
                self.job_id, row, col, asset["assetID"], loss_poe)

        LOGGER.debug("RESULT: conditional loss is %s, write to key %s" % (
            loss_conditional, key))
        kvs.set(key, loss_conditional)

    def compute_loss_ratio_curve(self, col, row, asset, gmf_slice):
        """Compute the loss ratio curve for a single site."""

        # fail if the asset has an unknown vulnerability code
        vuln_function = self.vuln_curves.get(
                asset["vulnerabilityFunctionReference"], None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"], asset["assetID"]))

            return None

        epsilon_provider = general.EpsilonProvider(self.params)
        loss_ratio_curve = probabilistic_event_based.compute_loss_ratio_curve(
                vuln_function, gmf_slice, epsilon_provider, asset,
                self._get_number_of_samples())

        # NOTE(JMC): Early exit if the loss ratio is all zeros
        if not False in (loss_ratio_curve.ordinates == 0.0):
            return None

        key = kvs.tokens.loss_ratio_key(
            self.job_id, row, col, asset["assetID"])
        kvs.set(key, loss_ratio_curve.to_json())

        LOGGER.warn("RESULT: loss ratio curve is %s, write to key %s" % (
                loss_ratio_curve, key))

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
        """Compute the loss curve for a single site."""
        if asset is None:
            return None

        loss_curve = loss_ratio_curve.rescale_abscissae(asset["assetValue"])
        key = kvs.tokens.loss_curve_key(
            self.job_id, row, column, asset["assetID"])

        LOGGER.warn("RESULT: loss curve is %s, write to key %s" % (
                loss_curve, key))
        kvs.set(key, loss_curve.to_json())
        return loss_curve


general.RiskJobMixin.register("Event Based", ProbabilisticEventMixin)
