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
event based approach.
"""


import numpy
import os

from openquake import logs
from openquake import shapes

from openquake.output import risk as risk_output
from openquake.parser import vulnerability
from openquake.calculators.risk import general
from openquake.utils.tasks import distribute

LOGGER = logs.LOG


class ScenarioRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario method for performing risk calculations.
    """

    def __init__(self, job_ctxt):
        general.BaseRiskCalculator.__init__(self, job_ctxt)

        self._output_filename = "loss-map-%s.xml"

        # sum of the assets losses of the
        # whole computation
        self._sum_region_losses = None

        # mean and standard deviation
        # loss of each asset
        self._loss_map_data = None

        # algorithm used to compute the losses
        # (standard or insured)
        self._loss_ratios_calculator = compute_uninsured_losses

    def pre_execute(self):
        super(ScenarioRiskCalculator, self).pre_execute()

        if self.job_ctxt.params.get("INSURED_LOSSES"):
            self._output_filename = "insured-loss-map%s.xml"
            self._loss_ratios_calculator = compute_insured_losses

    def post_execute(self):
        loss_map_path = os.path.join(
            self.job_ctxt["BASE_PATH"],
            self.job_ctxt["OUTPUT_DIR"],
            self._output_filename % self.job_ctxt.job_id)

        loss_map_writer = risk_output.create_loss_map_writer(
            self.job_ctxt.job_id, self.job_ctxt.serialize_results_to,
            loss_map_path, True)

        if loss_map_writer:
            LOGGER.debug("Starting serialization of the loss map...")

            # Add a metadata dict in the first list position
            # Note: the metadata is still incomplete (see bug 809410)
            loss_map_metadata = {"scenario": True}
            self._loss_map_data.insert(0, loss_map_metadata)
            loss_map_writer.serialize(self._loss_map_data)

        # For now, just print these values.
        # These are not debug statements; please don't remove them!
        print "Mean region loss value: %s" % numpy.mean(
            self._sum_region_losses)

        print "Standard deviation region loss value: %s" % numpy.std(
            self._sum_region_losses, ddof=1)

    def execute(self):
        """
        Entry point for triggering the computation.
        """

        LOGGER.debug("Executing scenario risk computation.")
        LOGGER.debug("This will calculate mean and standard deviation loss"
            "values for the region defined in the job config.")

        vuln_model = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        region_losses = []
        region_loss_map_data = {}

        region_data = distribute(
            general.compute_risk, ("block_id", self.job_ctxt.blocks_keys),
            tf_args=dict(job_id=self.job_ctxt.job_id,
            vuln_model=vuln_model, calculator=self._loss_ratios_calculator))

        for block_data in region_data:
            region_losses.append(block_data[0])
            collect_region_data(block_data[1], region_loss_map_data)

        self._sum_region_losses = reduce(lambda x, y: x + y, region_losses)

        self._loss_map_data = [(site, data)
                for site, data in region_loss_map_data.iteritems()]

    def compute_risk(self, block_id, **kwargs):
        """
        This method will perform two distinct (but similar) computations and
        return a result for each computation. The computations are as follows:

        First:

        For a given block of sites, compute loss values for all assets in the
        block. This computation will yield a single loss value per realization
        for the region block.

        Second:

        For each asset in the given block of sites, we need compute loss
        (where loss = loss_ratio * asset_value) for each realization. This
        gives 1 loss value _per_ asset _per_ realization. We then need to take
        the mean & standard deviation.

        Other info:

        The GMF data for each realization is stored in the KVS by the preceding
        scenario hazard job.

        :param block_id: id of the region block data we need to pull from the
            KVS
        :type block_id: str
        :keyword vuln_model:
            dict of :py:class:`openquake.shapes.VulnerabilityFunction` objects,
            keyed by the vulnerability function name as a string
        :keyword epsilon_provider:
            :py:class:`openquake.risk.job.EpsilonProvider` object

        :returns: 2-tuple of the following data:
            * 1-dimensional :py:class:`numpy.ndarray` of loss values for this
                region block (again, 1 value per realization)

            * list of 2-tuples containing site, loss, and asset
                information.

                The first element of each 2-tuple shall be a
                :py:class:`openquake.shapes.Site` object, which represents the
                geographical location of the asset loss.

                The second element shall be a list of
                2-tuples of dicts representing the loss and asset data (in that
                order).

                Example::

                    [(<Site(-117.0, 38.0)>, [
                        ({'mean_loss': 200.0, 'stddev_loss': 100},
                            {'assetID': 'a171'}),
                        ({'mean_loss': 200.0, 'stddev_loss': 100},
                            {'assetID': 'a187'})
                    ]),
                     (<Site(-118.0, 39.0)>, [
                        ({'mean_loss': 50, 'stddev_loss': 50.0},
                            {'assetID': 'a192'})
                    ])]
        """

        vuln_model = kwargs["vuln_model"]
        compute_losses = kwargs["calculator"]
        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        block_losses = []
        loss_map_data = {}

        for site in block.sites:
            gmvs = {"IMLs": general.load_gmvs_at(
                    self.job_ctxt.job_id, general.hazard_input_site(
                    self.job_ctxt, site))}

            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            for asset in assets:
                vuln_function = vuln_model[asset.taxonomy]

                losses = compute_losses(
                        vuln_function, gmvs, epsilon_provider, asset)

                asset_site = shapes.Site(asset.site.x, asset.site.y)

                loss = ({
                    "mean_loss": numpy.mean(losses),
                    "stddev_loss": numpy.std(losses, ddof=1)}, {
                    "assetID": asset.asset_ref
                })

                block_losses.append(losses)
                collect_block_data(loss_map_data, asset_site, loss)

        sum_block_losses = reduce(lambda x, y: x + y, block_losses)
        return sum_block_losses, loss_map_data


def collect_region_data(block_loss_map_data, region_loss_map_data):
    """
    Collect the loss map data for all the region.
    """

    for site, data in block_loss_map_data.iteritems():
        if site in region_loss_map_data:
            region_loss_map_data[site].extend(data)
        else:
            region_loss_map_data[site] = data


def collect_block_data(loss_data, asset_site, asset_data):
    """
    Collect the loss map map for a single block.
    """

    data = loss_data.get(asset_site, [])
    data.append(asset_data)
    loss_data[asset_site] = data


def compute_uninsured_losses(vuln_function, gmvs, epsilon_provider, asset):
    """
    Compute losses for the given asset using the related set of ground
    motion values and vulnerability function.

    :param vuln_function: the vulnerability function used to compute the loss
        ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmvs: the set of ground motion values used to compute the loss
        ratios.
    :type gmvs: :py:class:`dict` with the following keys: **IMLs** - tuple
        of ground motion values (float).
    :param epsilon_provider: service used to get the epsilon when using the
        sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    loss_ratios = general.compute_loss_ratios(
        vuln_function, gmvs, epsilon_provider, asset)

    losses = loss_ratios * asset.value

    return losses


def insurance_boundaries_defind(asset):
    """
    Check if limit and deductibles values have been defined for the asset.

    :param asset: the asset used to compute the losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    if (asset.ins_limit >= 0 and asset.deductible >= 0):
        return True
    else:
        raise RuntimeError('Insurance boundaries for asset %s are not defined'
            % asset.asset_ref)


def compute_insured_losses(vuln_function, gmvs, epsilon_provider, asset):
    """
    Compute insured losses for the given asset using the related set of ground
    motion values and vulnerability function.

    :param vuln_function: the vulnerability function used to compute the loss
        ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmvs: the set of ground motion values used to compute the loss
        ratios.
    :type gmvs: :py:class:`dict` with the following keys: **IMLs** - tuple
        of ground motion values (float).
    :param epsilon_provider: service used to get the epsilon when using the
        sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    losses = compute_uninsured_losses(vuln_function, gmvs,
                epsilon_provider, asset)

    if insurance_boundaries_defind(asset):
        for i, value in enumerate(losses):
            if value < asset.deductible:
                losses[i] = 0
            else:
                if value > asset.ins_limit:
                    losses[i] = asset.ins_limit
    return losses
