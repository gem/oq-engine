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

"""Mixin proxy for risk jobs, and associated Risk Job Mixin decorators."""

from collections import defaultdict
import json
import os

from scipy.stats import norm

from openquake import job
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.job import config as job_config
from openquake.job import mixins
from openquake.output import risk as risk_output
from openquake.parser import exposure
from openquake.parser import vulnerability
from openquake.risk import common
from openquake.utils.tasks import check_job_status

from celery.task import task

LOG = logs.LOG
BLOCK_SIZE = 100


def preload(mixin):
    """
    Define some preliminary steps needed before starting
    the risk processing.

    * read and store in KVS the assets
    * read and store in KVS the vulnerability model
    * split into blocks and store in KVS the exposure sites
    """
    mixin.store_exposure_assets()
    mixin.store_vulnerability_model()
    mixin.partition()


def write_output(mixin):
    """
    Write the output of a block to db/xml.
    """
    for block_id in mixin.blocks_keys:
        #pylint: disable=W0212
        mixin._write_output_for_block(mixin.job_id, block_id)

    for loss_poe in conditional_loss_poes(mixin.params):
        path = os.path.join(mixin.base_path,
                            mixin.params['OUTPUT_DIR'],
                            "losses_at-%s.xml" % loss_poe)
        writer = risk_output.create_loss_map_writer(
            mixin.job_id, mixin.serialize_results_to, path, False)

        if writer:
            metadata = {
                "scenario": False,
                "timeSpan": mixin.params["INVESTIGATION_TIME"],
                "poE": loss_poe,
            }

            writer.serialize(
                [metadata]
                + mixin.asset_losses_per_site(
                    loss_poe,
                    mixin.grid_assets_iterator(mixin.region.grid)))
            LOG.info('Loss Map is at: %s' % path)


def write_output_bcr(mixin):
    """
    Write BCR map in NRML format.
    """
    # TODO: unittest
    path = os.path.join(mixin.base_path,
                        mixin.params['OUTPUT_DIR'],
                        "bcr-map.xml")
    writer = risk_output.create_bcr_map_writer(
        mixin.job_id, mixin.serialize_results_to, path)

    metadata = {
        'interestRate': mixin.params['INTEREST_RATE'],
        'assetLifeExpectancy': mixin.params['ASSET_LIFE_EXPECTANCY'],
    }

    writer.serialize([metadata] + mixin.asset_bcr_per_site())
    LOG.info('BCR Map is at: %s' % path)


def conditional_loss_poes(params):
    """Return the PoE(s) specified in the configuration file used to
    compute the conditional loss."""

    return [float(x) for x in params.get(
        "CONDITIONAL_LOSS_POE", "").split()]


def compute_conditional_loss(job_id, col, row, loss_curve, asset, loss_poe):
    """Compute the conditional loss for a loss curve and Probability of
    Exceedance (PoE)."""

    loss_conditional = common.compute_conditional_loss(
        loss_curve, loss_poe)

    key = kvs.tokens.loss_key(
            job_id, row, col, asset["assetID"], loss_poe)

    LOG.debug("Conditional loss is %s, write to key %s" %
            (loss_conditional, key))

    kvs.get_client().set(key, loss_conditional)


@task
def compute_risk(job_id, block_id, **kwargs):
    """ A task for computing risk, calls the mixed in compute_risk method """
    check_job_status(job_id)
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin) as mixed:
        return mixed.compute_risk(block_id, **kwargs)


class RiskJobMixin(mixins.Mixin):
    """A mixin proxy for Risk jobs."""
    mixins = {}

    def is_benefit_cost_ratio_mode(self):
        """
        Return True if current calculation mode is Benefit-Cost Ratio.
        """
        return self.params[job_config.CALCULATION_MODE] in (
            job_config.BCR_CLASSICAL_MODE,
            job_config.BCR_EVENT_BASED_MODE
        )

    def partition(self):
        """Split the sites to compute in blocks and store
        them in the underlying KVS system."""

        sites = []
        self.blocks_keys = []  # pylint: disable=W0201
        sites = job.read_sites_from_exposure(self)

        block_count = 0

        for block in split_into_blocks(self.job_id, sites):
            self.blocks_keys.append(block.id)
            block.to_kvs()

            block_count += 1

        LOG.info("Job has partitioned %s sites into %s blocks",
                len(sites), block_count)

    def store_exposure_assets(self):
        """Load exposure assets and write them to KVS."""

        exposure_parser = exposure.ExposurePortfolioFile(
            os.path.join(self.base_path, self.params[job_config.EXPOSURE]))

        for site, asset in exposure_parser.filter(self.region):
# TODO(ac): This is kludgey (?)
            asset["lat"] = site.latitude
            asset["lon"] = site.longitude
            gridpoint = self.region.grid.point_at(site)

            asset_key = kvs.tokens.asset_key(
                self.job_id, gridpoint.row, gridpoint.column)

            kvs.get_client().rpush(asset_key, json.JSONEncoder().encode(asset))

    def store_vulnerability_model(self):
        """ load vulnerability and write to kvs """
        path = os.path.join(self.base_path, self.params["VULNERABILITY"])
        vulnerability.load_vulnerability_model(self.job_id, path)

        if self.is_benefit_cost_ratio_mode():
            path = os.path.join(self.base_path,
                                self.params["VULNERABILITY_RETROFITTED"])
            vulnerability.load_vulnerability_model(self.job_id, path,
                                                   retrofitted=True)

    def _serialize(self, block_id, **kwargs):
        """
        Build filename/paths for serializing and call _serialize

        Return the list of filenames. The list will be empty if nothing was
        actually serialized.
        """

        if kwargs['curve_mode'] == 'loss_ratio':
            serialize_filename = "%s-block-%s.xml" % (
                                     self.params["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)
        elif kwargs['curve_mode'] == 'loss':
            serialize_filename = "%s-loss-block-%s.xml" % (
                                     self.params["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)

        serialize_path = os.path.join(self.base_path,
                                      self.params['OUTPUT_DIR'],
                                      serialize_filename)

        LOG.debug("Serializing %s" % kwargs['curve_mode'])
        writer = risk_output.create_loss_curve_writer(self.job_id,
            self.serialize_results_to, serialize_path, kwargs['curve_mode'])
        if writer:
            writer.serialize(kwargs['curves'])

            return [serialize_path]
        else:
            return []

    def grid_assets_iterator(self, grid):
        """
        Generates the tuples (point, asset) for all assets known to this job
        that are contained in grid.

        :returns: tuples (point, asset) where:
            * point is a :py:class:`openquake.shapes.GridPoint` on the grid

            * asset is a :py:class:`dict` representing an asset
        """

        for point in grid:
            asset_key = kvs.tokens.asset_key(
                self.job_id, point.row, point.column)
            for asset in kvs.get_list_json_decoded(asset_key):
                yield point, asset

    def _write_output_for_block(self, job_id, block_id):
        """ Given a job and a block, write out a plotted curve """
        loss_ratio_curves = []
        loss_curves = []
        block = Block.from_kvs(block_id)
        for point, asset in self.grid_assets_iterator(
                block.grid(self.region)):
            site = shapes.Site(asset['lon'], asset['lat'])

            loss_curve = kvs.get_client().get(
                kvs.tokens.loss_curve_key(
                    job_id, point.row, point.column, asset["assetID"]))
            loss_ratio_curve = kvs.get_client().get(
                kvs.tokens.loss_ratio_key(
                    job_id, point.row, point.column, asset["assetID"]))

            if loss_curve:
                loss_curve = shapes.Curve.from_json(loss_curve)
                loss_curves.append((site, (loss_curve, asset)))

            if loss_ratio_curve:
                loss_ratio_curve = shapes.Curve.from_json(loss_ratio_curve)
                loss_ratio_curves.append((site, (loss_ratio_curve, asset)))

        results = self._serialize(block_id,
                                           curves=loss_ratio_curves,
                                           curve_mode='loss_ratio')
        if loss_curves:
            results.extend(
                self._serialize(
                    block_id, curves=loss_curves, curve_mode='loss',
                    curve_mode_prefix='loss_curve', render_multi=True))
        return results

    def asset_losses_per_site(self, loss_poe, assets_iterator):
        """
        For each site in the region of this job, returns a list of assets and
        their losses at a given probability of exceedance.

        :param:loss_poe: the probability of exceedance
        :type:loss_poe: float
        :param:assets_iterator: an iterator over the assets, returning (point,
            asset) tuples. See
            :py:class:`openquake.risk.job.general.grid_assets_iterator`.

        :returns: A list of tuples in the form expected by the
        :py:class:`LossMapWriter.serialize` method:

           (site, [(loss, asset), ...])

           Where:

            :py:class:`openquake.shapes.Site` the site
            :py:class:`dict` the asset dict
            :py:class:`dict` (loss dict) with the following key:
                ***value*** - the value of the loss for the asset
        """
        result = defaultdict(list)

        for point, asset in assets_iterator:
            key = kvs.tokens.loss_key(self.job_id, point.row, point.column,
                    asset["assetID"], loss_poe)

            loss_value = kvs.get_client().get(key)

            LOG.debug("Loss for asset %s at %s %s is %s" %
                (asset["assetID"], asset['lon'], asset['lat'], loss_value))

            if loss_value:
                risk_site = shapes.Site(asset['lon'], asset['lat'])
                loss = {
                    "value": loss_value,
                }
                result[risk_site].append((loss, asset))

        return result.items()

    def asset_bcr_per_site(self):
        """
        Fetch and return Benefit-Cost Ratio results computed by workers.

        :return:
            List of two-item tuples: site object and lists of BCR values per
            asset in that site. See :func:`compute_bcr_for_block`.
        """
        data = []
        for block_id in self.blocks_keys:
            key = kvs.tokens.bcr_block_key(self.job_id, block_id)
            block_data = kvs.get_value_json_decoded(key)
            data += [(shapes.Site(latitude=lat, longitude=lon), payload)
                     for ((lat, lon), payload) in block_data]
        return data


class EpsilonProvider(object):
    """
    Simple class for combining job configuration parameters and an `epsilon`
    method. See :py:meth:`EpsilonProvider.epsilon` for more information.
    """

    def __init__(self, params):
        """
        :param params: configuration parameters from the job configuration
        :type params: dict
        """
        self.__dict__.update(params)
        self.samples = None

    def epsilon(self, asset):
        """Sample from the standard normal distribution for the given asset.

        For uncorrelated risk calculation jobs we sample the standard normal
        distribution for each asset.
        In the opposite case ("perfectly correlated" assets) we sample for each
        building typology i.e. two assets with the same typology will "share"
        the same standard normal distribution sample.

        Two assets are considered to be of the same building typology if their
        structure category is the same. The asset's `structureCategory` is
        only needed for correlated jobs and unlikely to be available for
        uncorrelated ones.
        """
        correlation = getattr(self, "ASSET_CORRELATION", None)
        if not correlation:
            # Sample per asset
            return norm.rvs(loc=0, scale=1)
        elif correlation != "perfect":
            raise ValueError('Invalid "ASSET_CORRELATION": %s' % correlation)
        else:
            # Sample per building typology
            samples = getattr(self, "samples", None)
            if samples is None:
                # These are two references for the same dictionary.
                samples = self.samples = dict()

            category = asset.get("structureCategory")
            if category is None:
                raise ValueError(
                    "Asset %s has no structure category" % asset["assetID"])

            if category not in samples:
                samples[category] = norm.rvs(loc=0, scale=1)
            return samples[category]


mixins.Mixin.register("Risk", RiskJobMixin, order=2)


class Block(object):
    """A block is a collection of sites to compute."""

    def __init__(self, sites, block_id):
        self.sites = tuple(sites)
        self.block_id = block_id

    def grid(self, region):
        """Provide an iterator across the unique grid points within a region,
         corresponding to the sites within this block."""

        used_points = []
        for site in self.sites:
            point = region.grid.point_at(site)
            if point not in used_points:
                used_points.append(point)
                yield point

    def __eq__(self, other):
        return self.sites == other.sites

    @classmethod
    def from_kvs(cls, block_id):
        """Return the block in the underlying KVS system with the given id."""

        raw_sites = kvs.get_value_json_decoded(block_id)

        sites = []

        for raw_site in raw_sites:
            sites.append(shapes.Site(raw_site[0], raw_site[1]))

        return Block(sites, block_id)

    def to_kvs(self):
        """Store this block into the underlying KVS system."""

        raw_sites = []

        for site in self.sites:
            raw_sites.append(site.coords)

        kvs.set_value_json_encoded(self.id, raw_sites)

    @property
    def id(self):  # pylint: disable=C0103
        """Return the id of this block."""
        return self.block_id


def split_into_blocks(job_id, sites, block_size=BLOCK_SIZE):
    """Split the set of sites into blocks. Provide an iterator
    to the blocks.

    :param job_id: the id for this job
    :param sites: the sites to be splitted.
    :type sites: :py:class:`list`
    :param sites_per_block: the number of sites per block.
    :type sites_per_block: integer
    :returns: for each call on this iterator, the next block is returned.
    :rtype: :py:class:`openquake.risk.general.Block`
    """

    block_sites = []
    block_count = 0

    for site in sites:
        block_sites.append(site)

        if len(block_sites) == block_size:
            block_id = kvs.tokens.risk_block_key(job_id, block_count)
            yield(Block(block_sites, block_id))

            block_sites = []
            block_count += 1

    if not block_sites:
        return

    block_id = kvs.tokens.risk_block_key(job_id, block_count)
    yield(Block(block_sites, block_id))


def compute_bcr_for_block(job_id, points, get_loss_curve,
                          interest_rate, asset_life_expectancy):
    """
    Compute and return Benefit-Cost Ratio data for a number of points.

    :param get_loss_curve:
        Function that takes three positional arguments: point object,
        vulnerability function object and asset object and is supposed
        to return a loss curve.
    :return:
        A list of tuples::

            [((site_lat, site_lon), [
                ({'value': bcr}, assetID),
                ({'value': bcr}, assetID),
                ...]),
             ...]
    """
    # too many local vars (16/15) -- pylint: disable=R0914
    result = defaultdict(list)

    vuln_curves = vulnerability.load_vuln_model_from_kvs(job_id)
    vuln_curves_retrofitted = vulnerability.load_vuln_model_from_kvs(
        job_id, retrofitted=True)

    for point in points:
        asset_key = kvs.tokens.asset_key(job_id, point.row, point.column)

        for asset in kvs.get_list_json_decoded(asset_key):
            vuln_function = vuln_curves[asset['taxonomy']]
            loss_curve = get_loss_curve(point, vuln_function, asset)
            eal_original = common.compute_mean_loss(loss_curve)

            vuln_function = vuln_curves_retrofitted[asset['taxonomy']]
            loss_curve = get_loss_curve(point, vuln_function, asset)
            eal_retrofitted = common.compute_mean_loss(loss_curve)

            bcr = common.compute_bcr(
                eal_original, eal_retrofitted,
                interest_rate, asset_life_expectancy,
                asset['retrofittingCost']
            )

            key = (asset['lat'], asset['lon'])
            result[key].append(({'value': bcr}, asset['assetID']))

    return result.items()
