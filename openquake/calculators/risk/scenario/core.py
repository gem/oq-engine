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
This module performs risk calculations using the scenario
event based approach.
"""


import numpy
import os

from openquake import kvs
from openquake import logs
from openquake import shapes

from openquake.output import risk as risk_output
from openquake.parser import vulnerability
from openquake.calculators.risk import general


LOGGER = logs.LOG


class ScenarioRiskCalculator(general.BaseRiskCalculator):
    """Scenario method for performing risk calculations."""

    # pylint: disable=R0914
    def execute(self):
        """Entry point for triggering the computation."""
        general.preload(self)

        LOGGER.debug("Executing scenario risk computation.")
        LOGGER.debug("This will calculate mean and standard deviation loss"
            "values for the region defined in the job config.")

        tasks = []

        vuln_model = \
            vulnerability.load_vuln_model_from_kvs(self.calc_proxy.job_id)

        epsilon_provider = general.EpsilonProvider(self.calc_proxy.params)

        sum_per_gmf = SumPerGroundMotionField(vuln_model,
                                                       epsilon_provider)

        region_loss_map_data = {}

        for block_id in self.calc_proxy.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s"
                % (block_id, len(self.calc_proxy.blocks_keys)))
            a_task = general.compute_risk.delay(
                self.calc_proxy.job_id, block_id, vuln_model=vuln_model,
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
            self.calc_proxy['BASE_PATH'],
            self.calc_proxy['OUTPUT_DIR'],
            'loss-map-%s.xml' % self.calc_proxy.job_id)
        loss_map_writer = risk_output.create_loss_map_writer(
            self.calc_proxy.job_id, self.calc_proxy.serialize_results_to,
            loss_map_path, True)

        if loss_map_writer:
            LOGGER.debug("Starting serialization of the loss map...")

            # Add a metadata dict in the first list position
            # Note: the metadata is still incomplete (see bug 809410)
            loss_map_metadata = {'scenario': True}
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
        scenario hazard calculation.

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

        block = general.Block.from_kvs(self.calc_proxy.job_id, block_id)

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
        sum_per_gmf = SumPerGroundMotionField(vuln_model,
                                                       epsilon_provider)
        for point in block.grid(self.calc_proxy.region):
            gmvs = load_gmvs_for_point(self.calc_proxy.job_id, point)
            assets = load_assets_for_point(self.calc_proxy.job_id, point)
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

        for point in block.grid(self.calc_proxy.region):
            # the mean and stddev calculation functions used below
            # require the gmvs to be wrapped in a dict with a single key:
            # 'IMLs'
            gmvs = {'IMLs': load_gmvs_for_point(self.calc_proxy.job_id,
                                                point)}
            assets = load_assets_for_point(self.calc_proxy.job_id, point)
            for asset in assets:
                vuln_function = \
                    vuln_model[asset['taxonomy']]

                asset_mean_loss = compute_mean_loss(
                    vuln_function, gmvs, epsilon_provider, asset)

                asset_stddev_loss = compute_stddev_loss(
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
            {u'assetValue': 124.27, u'taxonomy': u'ID'}
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


def _mean_loss_from_loss_ratios(loss_ratios, asset):
    """Compute the mean loss using the set of loss ratios given.

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param asset: the asset used to compute the losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    losses = loss_ratios * asset["assetValue"]
    return numpy.mean(losses)


def _stddev_loss_from_loss_ratios(loss_ratios, asset):
    """Compute the standard deviation of the losses
    using the set of loss ratios given.

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param asset: the asset used to compute the losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    losses = loss_ratios * asset["assetValue"]
    return numpy.std(losses, ddof=1)


def compute_mean_loss(vuln_function, ground_motion_field_set,
                      epsilon_provider, asset):
    """Compute the mean loss for the given asset using the
    related ground motion field set and vulnerability function.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    loss_ratios = general.compute_loss_ratios(
        vuln_function, ground_motion_field_set, epsilon_provider, asset)

    return _mean_loss_from_loss_ratios(loss_ratios, asset)


def compute_stddev_loss(vuln_function, ground_motion_field_set,
                        epsilon_provider, asset):
    """Compute the standard deviation of the losses for the given asset
    using the related ground motion field set and vulnerability function.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    loss_ratios = general.compute_loss_ratios(
        vuln_function, ground_motion_field_set, epsilon_provider, asset)

    return _stddev_loss_from_loss_ratios(loss_ratios, asset)


class SumPerGroundMotionField(object):
    """This class computes the mean and the standard deviation of
    the sum of the losses per ground motion field set."""

    def __init__(self, vuln_model, epsilon_provider, lr_calculator=None):
        """Initialize an instance of this class.

        :param vuln_model: the vulnerability model used to lookup the
            functions referenced by each asset.
        :type vuln_model: :py:class:`dict` where each key is the id
            of the function and the value is an instance of
            `openquake.shapes.VulnerabilityFunction`
        :param epsilon_provider: service used to get the epsilon when
            using the sampled based algorithm.
        :type epsilon_provider: object that defines
            an :py:method:`epsilon` method
        :param lr_calculator: service used to compute the loss ratios.
            For the list of parameters, see
    :py:function:`openquake.calculators.risk.general.compute_loss_ratios`
        :type lr_calculator: object that defines an :py:meth:`epsilon` method
        """
        self.vuln_model = vuln_model
        self.lr_calculator = lr_calculator
        self.epsilon_provider = epsilon_provider

        self.losses = numpy.array([])

        if lr_calculator is None:
            self.lr_calculator = general.compute_loss_ratios

    def add(self, ground_motion_field_set, asset):
        """Compute the losses for the given ground motion field set, and
        sum those to the current sum of the losses.

        If the asset refers to a vulnerability function that is not
        supported by the vulnerability model, the distribution
        of the losses is discarded.

        :param ground_motion_field_set: the set of ground motion
            fields used to compute the loss ratios.
        :type ground_motion_field_set: :py:class:`dict` with the following
            keys:
            **IMLs** - tuple of ground motion fields (float)
        :param asset: the asset used to compute the loss ratios and losses.
        :type asset: :py:class:`dict` as provided by
            :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
        """

        if asset["taxonomy"] not in self.vuln_model:
            LOGGER.debug("Unknown vulnerability function %s, asset %s will " \
                      "not be included in the aggregate computation"
                      % (asset["taxonomy"],
                      asset["assetID"]))

            return

        vuln_function = self.vuln_model[
            asset["taxonomy"]]

        loss_ratios = self.lr_calculator(
            vuln_function, ground_motion_field_set,
            self.epsilon_provider, asset)

        losses = numpy.array(loss_ratios) * asset["assetValue"]

        self.sum_losses(losses)

    def sum_losses(self, losses):
        """
        Accumulate losses into a single sum.

        :param losses: an array of loss values (1 per realization)
        :type losses: 1-dimensional :py:class:`numpy.ndarray`

        The `losses` arrays passed to this function must be empty or
        all the same lenght.
        """
        if len(self.losses) == 0:
            self.losses = losses
        elif len(losses) > 0:
            self.losses = self.losses + losses

    @property
    def mean(self):
        """Return the mean of the current sum of the losses.

        :returns: the mean of the current sum of the losses
        :rtype: numpy.float64
        """
        return numpy.mean(self.losses)

    @property
    def stddev(self):
        """Return the standard deviation of the sum of the losses.

        :returns: the standard deviation of the current sum of the losses
        :rtype: numpy.float64
        """
        return numpy.std(self.losses, ddof=1)
