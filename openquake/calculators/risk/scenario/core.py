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


LOGGER = logs.LOG


class ScenarioRiskCalculator(general.BaseRiskCalculator):
    """Scenario method for performing risk calculations."""

    # pylint: disable=R0914
    def execute(self):
        """Entry point for triggering the computation."""
        LOGGER.debug("Executing scenario risk computation.")
        LOGGER.debug("This will calculate mean and standard deviation loss"
            "values for the region defined in the job config.")

        tasks = []

        vuln_model = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)

        sum_per_gmf = SumPerGroundMotionField(vuln_model, epsilon_provider)

        region_loss_map_data = {}

        for block_id in self.job_ctxt.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s"
                % (block_id, len(self.job_ctxt.blocks_keys)))
            a_task = general.compute_risk.delay(
                self.job_ctxt.job_id, block_id, vuln_model=vuln_model)
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
        if self.job_ctxt.params.insured_losses:
            output_filename= 'insured-loss-map%s.xml'
        else:
            output_filename = 'loss-map-%s.xml'
        loss_map_path = os.path.join(
            self.job_ctxt['BASE_PATH'],
            self.job_ctxt['OUTPUT_DIR'],
            output_filename % self.job_ctxt.job_id)
        loss_map_writer = risk_output.create_loss_map_writer(
            self.job_ctxt.job_id, self.job_ctxt.serialize_results_to,
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

        vuln_model = kwargs['vuln_model']
        epsilon_provider = general.EpsilonProvider(self.job_ctxt.params)
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        loss_data = {}

        # used to sum the losses for the whole block
        sum_per_gmf = SumPerGroundMotionField(vuln_model, epsilon_provider)

        if self.job_ctxt.params.get("INSURED_LOSSES"):
            compute_losses = compute_insured_losses
        else:
            compute_losses = compute_uninsured_losses

        for site in block.sites:
            # the scientific functions used below
            # require the gmvs to be wrapped in a dict with a single key, IMLs
            gmvs = {'IMLs': general.load_gmvs_at(
                    self.job_ctxt.job_id, general.hazard_input_site(
                    self.job_ctxt, site))}

            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            for asset in assets:

                vuln_function = vuln_model[asset.taxonomy]
                losses = compute_losses(
                        vuln_function, gmvs, epsilon_provider, asset)
                mean_loss = numpy.mean(losses)
                stddev_loss = numpy.std(losses, ddof=1)
                asset_site = shapes.Site(asset.site.x, asset.site.y)
                loss = ({
                    'mean_loss': mean_loss,
                    'stddev_loss': stddev_loss}, {
                    'assetID': asset.asset_ref
                })

                sum_per_gmf.add(gmvs, asset)
                collect_block_data(loss_data, asset_site, loss)

        return sum_per_gmf.losses, loss_data


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

def compute_uninsured_losses(vuln_function, gmf_set, epsilon_provider, asset):
    loss_ratios = general.compute_loss_ratios(
        vuln_function, gmf_set, epsilon_provider, asset)
    losses = loss_ratios * asset.value

    return losses

def insurance_boundaries_defind(asset):
    if (asset.ins_limit >=0 and asset.deductible >= 0):
        return True
    else:
        raise RuntimeError('Insurance boundaries for asset %s are not defined'
            % asset.asset_ref)

def compute_insured_losses(vuln_function, gmf_set, epsilon_provider, asset):
    losses = compute_uninsured_losses(vuln_function, gmf_set,
                epsilon_provider, asset)

    if insurance_boundaries_defind(asset):
        for i, value in enumerate(losses):
            if value < asset.deductible:
                losses[i] = 0
            else:
                if value > asset.ins_limit:
                    losses[i] = asset.ins_limit

    return losses



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

    def add(self, gmf_set, asset):
        """Compute the losses for the given ground motion field set, and
        sum those to the current sum of the losses.

        If the asset refers to a vulnerability function that is not
        supported by the vulnerability model, the distribution
        of the losses is discarded.

        :param gmf_set: ground motion fields used to compute the loss ratios
        :type gmf_set: :py:class:`dict` with the following
            keys:
            **IMLs** - tuple of ground motion fields (float)
        :param asset: the asset used to compute the loss ratios and losses.
        :type asset: an :py:class:`openquake.db.model.ExposureData` instance
        """

        if asset.taxonomy not in self.vuln_model:
            LOGGER.debug("Unknown vulnerability function %s, asset %s will "
                         "not be included in the aggregate computation"
                         % (asset.taxonomy, asset.asset_ref))
            return

        vuln_function = self.vuln_model[asset.taxonomy]

        loss_ratios = self.lr_calculator(vuln_function, gmf_set,
                                         self.epsilon_provider, asset)

        losses = numpy.array(loss_ratios) * asset.value

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
