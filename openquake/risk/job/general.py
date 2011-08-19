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
from openquake.job import mixins
from openquake import kvs
from openquake.job import config
from openquake import logs
from openquake import shapes
from openquake.output import curve
from openquake.output import risk as risk_output
from openquake.parser import exposure
from openquake.parser import vulnerability
from openquake.utils.tasks import check_job_status

from celery.decorators import task

LOG = logs.LOG
BLOCK_SIZE = 100


def preload(fn):
    """Preload decorator."""

    def preloader(self, *args, **kwargs):
        """Define some preliminary steps needed before starting
        the risk processing. The decorator:

        * reads and stores in KVS the assets
        * reads and stores in KVS the vulnerability model
        * splits into blocks and stores in KVS the exposure sites
        """

        self.store_exposure_assets()
        self.store_vulnerability_model()
        self.partition()

        return fn(self, *args, **kwargs)
    return preloader


def output(fn):
    """ Decorator for output """

    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to kvs. """
        fn(self, *args, **kwargs)
        conditional_loss_poes = [float(x) for x in self.params.get(
                    'CONDITIONAL_LOSS_POE', "0.01").split()]

        for block_id in self.blocks_keys:
            #pylint: disable=W0212
            self._write_output_for_block(self.job_id, block_id)

        for loss_poe in conditional_loss_poes:
            path = os.path.join(self.base_path,
                                self['OUTPUT_DIR'],
                                "losses_at-%s.xml" % loss_poe)
            writer = risk_output.create_loss_map_writer(
                self.job_id, self.serialize_results_to, path, False)

            if writer:
                metadata = {
                    "deterministic": False,
                    "poe": loss_poe,
                }

                writer.serialize(
                    [metadata]
                    + self.asset_losses_per_site(
                        loss_poe,
                        self.grid_assets_iterator(self.region.grid)))

    return output_writer


def _plot(curve_path, result_path, **kwargs):
    """
    Build a plotter, and then render the plot
    """
    LOG.debug("Plotting %s" % kwargs['curve_mode'])

    render_multi = kwargs.get("render_multi")
    autoscale = False if kwargs['curve_mode'] == 'loss_ratio' else True
    plotter = curve.RiskCurvePlotter(result_path,
                                     curve_path,
                                     mode=kwargs["curve_mode"],
                                     render_multi=render_multi)
    plotter.plot(autoscale_y=autoscale)
    return plotter.filenames()


@task
def compute_risk(job_id, block_id, **kwargs):
    """ A task for computing risk, calls the mixed in compute_risk method """
    check_job_status(job_id)
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin) as mixed:
        return mixed.compute_risk(block_id, **kwargs)


def read_sites_from_exposure(a_job):
    """
    Given the exposure model specified in the job config, read all sites which
    are located within the region of interest.

    :param a_job: a Job object with an EXPOSURE parameter defined
    :type a_job: :py:class:`openquake.job.Job`

    :returns: a list of :py:class:`openquake.shapes.Site` objects
    """

    sites = []
    path = os.path.join(a_job.base_path, a_job.params[config.EXPOSURE])

    reader = exposure.ExposurePortfolioFile(path)
    constraint = a_job.region

    LOG.debug(
        "Constraining exposure parsing to %s" % constraint)

    for site, _asset_data in reader.filter(constraint):

        # we don't want duplicates (bug 812395):
        if not site in sites:
            sites.append(site)

    return sites


class RiskJobMixin(mixins.Mixin):
    """A mixin proxy for Risk jobs."""
    mixins = {}

    def partition(self):
        """Split the sites to compute in blocks and store
        them in the underlying KVS system."""

        sites = []
        self.blocks_keys = []  # pylint: disable=W0201
        sites = read_sites_from_exposure(self)

        block_count = 0

        for block in split_into_blocks(sites):
            self.blocks_keys.append(block.id)
            block.to_kvs()

            block_count += 1

        LOG.debug("Job has partitioned %s sites into %s blocks" % (
                len(sites), block_count))

    def store_exposure_assets(self):
        """Load exposure assets and write them to KVS."""

        exposure_parser = exposure.ExposurePortfolioFile("%s/%s" %
            (self.base_path, self.params[config.EXPOSURE]))

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
        vulnerability.load_vulnerability_model(self.job_id,
            "%s/%s" % (self.base_path, self.params["VULNERABILITY"]))

    def _serialize(self, block_id, **kwargs):
        """
        Build filename/paths for serializing and call _serialize

        Return the list of filenames. The list will be empty if nothing was
        actually serialized.
        """

        if kwargs['curve_mode'] == 'loss_ratio':
            serialize_filename = "%s-block-%s.xml" % (
                                     self["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)
        elif kwargs['curve_mode'] == 'loss':
            serialize_filename = "%s-loss-block-%s.xml" % (
                                     self["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)

        serialize_path = os.path.join(self.base_path,
                                      self['OUTPUT_DIR'],
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

            loss_curve = kvs.get(
                            kvs.tokens.loss_curve_key(job_id,
                                                        point.row,
                                                        point.column,
                                                        asset["assetID"]))
            loss_ratio_curve = kvs.get(
                            kvs.tokens.loss_ratio_key(job_id,
                                                        point.row,
                                                        point.column,
                                                        asset["assetID"]))

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
            results.extend(self._serialize(block_id,
                                                curves=loss_curves,
                                                curve_mode='loss',
                                                curve_mode_prefix='loss_curve',
                                                render_multi=True))
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
            loss_value = kvs.get(key)
            LOG.debug("Loss for asset %s at %s %s is %s" %
                (asset["assetID"], asset['lon'], asset['lat'], loss_value))
            if loss_value:
                risk_site = shapes.Site(asset['lon'], asset['lat'])
                loss = {
                    "value": loss_value,
                }
                result[risk_site].append((loss, asset))

        return result.items()


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

    def __init__(self, sites, block_id=None):
        self.sites = tuple(sites)

        if not block_id:
            block_id = kvs.generate_block_id()

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


def split_into_blocks(sites, block_size=BLOCK_SIZE):
    """Split the set of sites into blocks. Provide an iterator
    to the blocks.

    :param sites: the sites to be splitted.
    :type sites: :py:class:`list`
    :param sites_per_block: the number of sites per block.
    :type sites_per_block: integer
    :returns: for each call on this iterator, the next block is returned.
    :rtype: :py:class:`openquake.risk.general.Block`
    """

    block_sites = []

    for site in sites:
        block_sites.append(site)

        if len(block_sites) == block_size:
            yield(Block(block_sites))
            block_sites = []

    if not block_sites:
        return

    yield(Block(block_sites))
