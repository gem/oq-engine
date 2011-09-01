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


import numpy
import os

from openquake import kvs
from openquake import shapes

from openquake.output import risk as risk_output
from openquake.parser import vulnerability
from openquake.risk import deterministic_event_based as det
from openquake.risk.job import general


class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing risk calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    @general.preload
    def execute(self):
        """Entry point for triggering the computation."""

        self.logger.debug("Executing deterministic risk computation.")
        self.logger.debug("This will calculate mean and standard "
                          "deviation loss values for the region "
                          "defined in the job config.")

        tasks = []

        vuln_model = \
            vulnerability.load_vuln_model_from_kvs(self.job_id)

        epsilon_provider = general.EpsilonProvider(self.params)

        sum_per_gmf = det.SumPerGroundMotionField(vuln_model, epsilon_provider,
                                                  logger=self.logger)

        region_loss_map_data = {}

        for block_id in self.blocks_keys:
            self.logger.debug("Dispatching task for block %s of %s",
                              block_id, len(self.blocks_keys))
            a_task = general.compute_risk.delay(
                self.job_id, block_id, vuln_model=vuln_model,
                epsilon_provider=epsilon_provider)
            tasks.append(a_task)

        for task in tasks:
            task.wait()
            if not task.successful():
                raise Exception(task.result)

            block_loss, block_loss_map_data = task.result

            # do some basic validation on our results
            assert block_loss is not None, "Expected a result != None"
            assert isinstance(block_loss, numpy.ndarray), \
                "Expected a numpy array"

            # our result should be a 1-dimensional numpy.array of loss values
            sum_per_gmf.sum_losses(block_loss)

            collect_region_data(
                block_loss_map_data, region_loss_map_data)

        loss_map_data = [(site, data)
                for site, data in region_loss_map_data.iteritems()]

        # serialize the loss map data to XML
        loss_map_path = os.path.join(
            self['BASE_PATH'],
            self['OUTPUT_DIR'],
            'loss-map-%s.xml' % self.job_id)
        loss_map_writer = risk_output.create_loss_map_writer(
            self.job_id, self.serialize_results_to, loss_map_path, True)

        if loss_map_writer:
            self.logger.debug("Starting serialization of the loss map...")

            # Add a metadata dict in the first list position
            # Note: the metadata is still incomplete (see bug 809410)
            loss_map_metadata = {'deterministic': True}
            loss_map_data.insert(0, loss_map_metadata)
            loss_map_writer.serialize(loss_map_data)

        # For now, just print these values.
        # These are not debug statements; please don't remove them!
        print "Mean region loss value: %s" % sum_per_gmf.mean
        print "Standard deviation region loss value: %s" % sum_per_gmf.stddev

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
        deterministic hazard calculation.

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

            * list of 2-tuples containing Site, Loss, and Asset
                information.

                The first element of each 2-tuple shall be a
                :py:class:`openquake.shapes.Site` object, which represents the
                geographical location of the asset loss.

                The second element shall be a list of
                2-tuples of dicts representing the Loss and Asset data (in that
                order).

                Example::

                    [(<Site(-117.0, 38.0)>,
                     [({'mean_loss': 200.0, 'stddev_loss': 100},
                      {'assetID': 'a171'}), ({'mean_loss': 200.0,
                      'stddev_loss': 100}, {'assetID': 'a187'})]),
                     (<Site(-117.0, 38.0)>,
                     ({'mean_loss': 200, 'stddev_loss': 100.0},
                      {'assetID': 'a172'})),
                     ...
                     (<Site(-118.0, 39.0)>,
                     ({'mean_loss': 50, 'stddev_loss': 50.0},
                      {'assetID': 'a192'}))]

        """
        vuln_model = kwargs['vuln_model']
        epsilon_provider = kwargs['epsilon_provider']

        block = general.Block.from_kvs(block_id)

        block_losses = self._compute_loss_for_block(
            block, vuln_model, epsilon_provider)

        asset_losses = self._compute_asset_losses_for_block(
            block, vuln_model, epsilon_provider)

        return block_losses, asset_losses

    def _compute_loss_for_block(self, block, vuln_model, epsilon_provider):
        """
        Compute the sum of all asset losses for the given region block.

        :param block: a block of sites represented by a
            :py:class:`openquake.job.Block` object
        :param vuln_model:
            dict of :py:class:`openquake.shapes.VulnerabilityFunction` objects,
            keyed by the vulnerability function name as a string
        :param epsilon_provider:
            :py:class:`openquake.risk.job.EpsilonProvider` object

        :returns: 1-dimensional :py:class:`numpy.ndarray` of floats
            representing loss values for this block. There will be one value
            per realization.

        """
        sum_per_gmf = det.SumPerGroundMotionField(vuln_model, epsilon_provider)
        for point in block.grid(self.region):
            gmvs = load_gmvs_for_point(self.job_id, point)
            assets = load_assets_for_point(self.job_id, point)
            for asset in assets:
                # the SumPerGroundMotionField add() method expects a dict
                # with a single key ('IMLs') and value set to the sequence of
                # GMVs
                sum_per_gmf.add({'IMLs': gmvs}, asset)
        return sum_per_gmf.losses

    def _compute_asset_losses_for_block(
        self, block, vuln_model, epsilon_provider):
        """
        Compute the mean & standard deviation loss values for each asset in the
        given block.

        :param block: a block of sites represented by a
            :py:class:`openquake.job.Block` object
        :param vuln_model:
            dict of :py:class:`openquake.shapes.VulnerabilityFunction` objects,
            keyed by the vulnerability function name as a string
        :param epsilon_provider:
            :py:class:`openquake.risk.job.EpsilonProvider` object

        :returns: list of 2-tuples containing Site, Loss, and Asset
            information.

            The first element of each 2-tuple shall be a
            :py:class:`openquake.shapes.Site` object, which represents the
            geographical location of the asset loss.

            The second element shall be a list of
            2-tuples of dicts representing the Loss and Asset data (in that
            order).

            Example::

                [(<Site(-117.0, 38.0)>,
                 [({'mean_loss': 200.0, 'stddev_loss': 100},
                  {'assetID': 'a171'}), ({'mean_loss': 200.0,
                  'stddev_loss': 100}, {'assetID': 'a187'})]),
                 (<Site(-117.0, 38.0)>,
                 ({'mean_loss': 200, 'stddev_loss': 100.0},
                  {'assetID': 'a172'})),
                 ...
                 (<Site(-118.0, 39.0)>,
                 ({'mean_loss': 50, 'stddev_loss': 50.0},
                  {'assetID': 'a192'}))]
        """
        loss_data = {}

        for point in block.grid(self.region):
            # the mean and stddev calculation functions used below
            # require the gmvs to be wrapped in a dict with a single key:
            # 'IMLs'
            gmvs = {'IMLs': load_gmvs_for_point(self.job_id, point)}
            assets = load_assets_for_point(self.job_id, point)
            for asset in assets:
                vuln_function = \
                    vuln_model[asset['vulnerabilityFunctionReference']]

                asset_mean_loss = det.compute_mean_loss(
                    vuln_function, gmvs, epsilon_provider, asset)

                asset_stddev_loss = det.compute_stddev_loss(
                    vuln_function, gmvs, epsilon_provider, asset)

                asset_site = shapes.Site(asset['lon'], asset['lat'])

                loss = ({'mean_loss': asset_mean_loss,
                         'stddev_loss': asset_stddev_loss},
                        {'assetID': asset['assetID']})

                collect_block_data(loss_data, asset_site, loss)

        return loss_data


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
    gmfs_key = kvs.tokens.ground_motion_values_key(job_id, point)
    return [float(x['mag']) for x in kvs.get_list_json_decoded(gmfs_key)]


def load_assets_for_point(job_id, point):
    """
    From the KVS, load all assets for the given point.

    :param point: :py:class:`openquake.shapes.GridPoint` object

    :returns: List of asset dicts at the given location (point) in the
        following form::
            {u'assetValue': 124.27, u'vulnerabilityFunctionReference': u'ID'}
    """
    assets_key = kvs.tokens.asset_key(job_id, point.row, point.column)
    return kvs.get_list_json_decoded(assets_key)


def collect_region_data(block_loss_map_data, region_loss_map_data):
    """Collect the loss map data for all the region."""
    for site, data in block_loss_map_data.iteritems():
        if site in region_loss_map_data:
            region_loss_map_data[site].extend(data)
        else:
            region_loss_map_data[site] = data


def collect_block_data(loss_data, asset_site, asset_data):
    """Collect the loss map map for a single block."""
    data = loss_data.get(asset_site, [])
    data.append(asset_data)
    loss_data[asset_site] = data


general.RiskJobMixin.register("Deterministic", DeterministicEventBasedMixin)
