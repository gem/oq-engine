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

import json
import os

from scipy.stats import norm

from openquake.output import geotiff
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

        results = []
        for block_id in self.blocks_keys:
            #pylint: disable=W0212
            results.extend(self._write_output_for_block(self.job_id, block_id))
        for loss_poe in conditional_loss_poes:
            results.extend(self.write_loss_map(loss_poe))
        return results

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
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin) as mixed:
        return mixed.compute_risk(block_id, **kwargs)


class RiskJobMixin(mixins.Mixin):
    """A mixin proxy for Risk jobs."""
    mixins = {}

    def partition(self):
        """Split the sites to compute in blocks and store
        them in the underlying KVS system."""

        sites = []
        self.blocks_keys = [] # pylint: disable=W0201
        region_constraint = self.region
        sites = self._read_sites_from_exposure()

        block_count = 0

        for block in split_into_blocks(sites, region_constraint):
            self.blocks_keys.append(block.id)
            block.to_kvs()

            block_count += 1

        LOG.debug("Job has partitioned %s sites into %s blocks" % (
                len(sites), block_count))

    def _read_sites_from_exposure(self):
        """Read the sites to compute from the exposure file specified
        in the job definition."""

        sites = []
        path = os.path.join(self.base_path, self.params[config.EXPOSURE])

        reader = exposure.ExposurePortfolioFile(path)
        constraint = self.region

        LOG.debug(
            "Constraining exposure parsing to %s" % constraint)

        for asset_data in reader.filter(constraint):
            sites.append(asset_data[0])

        return sites

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
                self.id, gridpoint.row, gridpoint.column)

            kvs.get_client().rpush(asset_key, json.JSONEncoder().encode(asset))

    def store_vulnerability_model(self):
        """ load vulnerability and write to kvs """
        vulnerability.load_vulnerability_model(self.id,
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
        writer = risk_output.create_loss_curve_writer(kwargs['curve_mode'],
            serialize_path, self.params)
        if writer:
            writer.serialize(kwargs['curves'])

            return [serialize_path]
        else:
            return []

    def _write_output_for_block(self, job_id, block_id):
        """ Given a job and a block, write out a plotted curve """
        loss_ratio_curves = []
        loss_curves = []
        block = Block.from_kvs(block_id)
        for point in block.grid(self.region):
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.loads(x) for x in asset_list]:
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

    def write_loss_map(self, loss_poe):
        """ Iterates through all the assets and maps losses at loss_poe """
        # Make a special grid at a higher resolution
        risk_grid = shapes.Grid(self.region, float(self['RISK_CELL_SIZE']))
        path = os.path.join(self.base_path,
                            self['OUTPUT_DIR'],
                            "losses_at-%s.tiff" % loss_poe)
        output_generator = geotiff.LossMapGeoTiffFile(path, risk_grid,
                init_value=0.0, normalize=True)
        for point in self.region.grid:
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.loads(x) for x in asset_list]:
                key = kvs.tokens.loss_key(self.id, point.row, point.column,
                        asset["assetID"], loss_poe)
                loss = kvs.get(key)
                LOG.debug("Loss for asset %s at %s %s is %s" %
                    (asset["assetID"], asset['lon'], asset['lat'], loss))
                if loss:
                    loss_ratio = float(loss) / float(asset["assetValue"])
                    risk_site = shapes.Site(asset['lon'], asset['lat'])
                    risk_point = risk_grid.point_at(risk_site)
                    output_generator.write(
                            (risk_point.row, risk_point.column), loss_ratio)
        output_generator.close()
        return [path]


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


def split_into_blocks(sites, constraint, block_size=BLOCK_SIZE):
    """Split the set of sites into blocks. Provide an iterator
    to the blocks.

    :param sites: the sites to be splitted.
    :type sites: :py:class:`list`
    :param constraint: the constraint used. Just the sites that match
        the constraint are included. If None all sites are included.
    :type constraint: :py:class:`openquake.shapes.RegionConstraint` object
    :param sites_per_block: the number of sites per block.
    :type sites_per_block: integer
    :returns: for each call on this iterator, the next block is returned.
    :rtype: :py:class:`openquake.risk.general.Block`
    """

    filtered_sites = []

    for site in sites:
        if constraint:
            if constraint.match(site):
                filtered_sites.append(site)
        else:
            filtered_sites.append(site)

        if len(filtered_sites) == block_size:
            yield(Block(filtered_sites))
            filtered_sites = []

    if not filtered_sites:
        return

    yield(Block(filtered_sites))
