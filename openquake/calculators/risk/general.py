# -*- coding: utf-8 -*-

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

"""Common functionality for Risk calculators."""

# Silence 'Too many lines in module'
# pylint: disable=C0302

import os

from collections import defaultdict

from celery.task import task

from django.contrib.gis import geos

from openquake.calculators.base import Calculator
from openquake.db import models
from openquake import logs, kvs, shapes
from openquake.input import exposure as exposure_input
from openquake.input.fragility import FragilityDBWriter
from openquake.job import config as job_config
from openquake.output import risk as risk_output
from openquake.parser import fragility
from openquake.parser import vulnerability
from openquake.utils import round_float
from openquake.utils.tasks import calculator_for_task
from risklib import curve, event_based


LOG = logs.LOG
BLOCK_SIZE = 100


def conditional_loss_poes(params):
    """Return the PoE(s) specified in the configuration file used to
    compute the conditional loss."""

    return [float(x) for x in params.get(
        "CONDITIONAL_LOSS_POE", "").split()]


@task
def compute_risk(job_id, block_id, **kwargs):
    """A task for computing risk, calls the compute_risk method defined in the
    chosen risk calculator.

    The calculator used is determined by the calculation configuration's
    calculation mode (i.e., classical, event_based, etc.).
    """

    calculator = calculator_for_task(job_id, 'risk')

    return calculator.compute_risk(block_id, **kwargs)


class BaseRiskCalculator(Calculator):
    """Base abstract class for Risk calculators."""

    # Exposure model inputs (cached result). We need to refresh these for each
    # job, otherwise the tests break when the entire suite is run.
    _em_inputs = None
    _em_job_id = -1

    def execute(self):
        """Calculation logic goes here; subclasses must implement this."""
        raise NotImplementedError()

    def is_benefit_cost_ratio_mode(self):
        """
        Return True if current calculation mode is Benefit-Cost Ratio.
        """
        return self.job_ctxt.params[job_config.CALCULATION_MODE] in (
            job_config.BCR_CLASSICAL_MODE,
            job_config.BCR_EVENT_BASED_MODE)

    def pre_execute(self):
        """Make sure the exposure and vulnerability data is in the database."""
        self.store_exposure_assets()
        self.store_vulnerability_model()
        self.partition()

    def _get_correlation_type(self):
        seed = self.job_ctxt["EPSILON_RANDOM_SEED"]
        correlation_types = dict(
            uncorrelated=event_based.UNCORRELATED,
            perfect=event_based.PERFECTLY_CORRELATED)
        correlation_type = correlation_types.get(
            self.job_ctxt["ASSET_CORRELATION"], event_based.UNCORRELATED)

        return seed, correlation_type

    @staticmethod
    def _cell_to_polygon(center, cell_size):
        """Return the cell with the given mid point and size.

        :param center: the center of the risk cell
        :type center: a :py:class:`openquake.shapes.Site` instance
        :param float cell_size: the configured risk cell size

        :return: the risk cell as a :py:class:`django.contrib.gis.geos.Polygon`
        """
        clon, clat = center.coords
        half_csize = cell_size / 2.0
        lon, lat = (clon - half_csize, clat - half_csize)

        coos = [(lon, lat),                             # lower left
                (lon, lat + cell_size),                 # upper left
                (lon + cell_size, lat + cell_size),     # upper right
                (lon + cell_size, lat),                 # lower right
                (lon, lat)]
        coos = [(round_float(x), round_float(y)) for x, y in coos]
        return geos.Polygon(coos)

    @classmethod
    def _load_exposure_model(cls, job_id):
        """Load and cache the exposure model."""

        if cls._em_inputs is None or cls._em_job_id != job_id:
            # This query obtains the exposure model input rows and needs to be
            # made only once in the course of a risk calculation.
            cls._em_inputs = models.inputs4job(job_id, "exposure")
            cls._em_job_id = job_id

    @classmethod
    def assets_for_cell(cls, job_id, center):
        """Return exposure assets for the given job and risk cell mid-point.

        :param int job_id: the database key of the job in question
        :param center: a :py:class:`openquake.shapes.Site` instance
            with the location of the risk cell center
        :returns: a potentially empty list of
            :py:class:`openquake.db.models.ExposureData` instances
        """
        jp = models.profile4job(job_id)
        assert jp.region_grid_spacing is not None, "Grid spacing not known."

        cls._load_exposure_model(job_id)
        if not cls._em_inputs:
            return []

        risk_cell = cls._cell_to_polygon(center, jp.region_grid_spacing)
        result = models.ExposureData.objects.filter(
            exposure_model__input__in=cls._em_inputs,
            site__contained=risk_cell)

        return list(result)

    @classmethod
    def assets_at(cls, job_id, site):
        """
        Load the assets from the exposure defined at the given site.

        :param job_id: the id of the job
        :type job_id: integer
        :param site: site where the assets are defined
        :type site: instance of :py:class:`openquake.shapes.Site`
        :returns: a list of
            :py:class:`openquake.db.models.ExposureData` objects
        """

        cls._load_exposure_model(job_id)

        if not cls._em_inputs:
            return []

        em = models.ExposureData.objects
        result = em.filter(exposure_model__input__in=cls._em_inputs,
                site=geos.Point(site.longitude, site.latitude))

        return list(result)

    def partition(self):
        """Split the sites to compute in blocks and store
        them in the underlying KVS system."""

        self.job_ctxt.blocks_keys = []  # pylint: disable=W0201
        sites = exposure_input.read_sites_from_exposure(self.job_ctxt)

        block_count = 0

        for block in split_into_blocks(self.job_ctxt.job_id, sites):
            self.job_ctxt.blocks_keys.append(block.block_id)
            block.to_kvs()

            block_count += 1

        LOG.info("Job has partitioned %s sites into %s blocks",
                 len(sites), block_count)

    def store_exposure_assets(self):
        """
        Load exposure assets from input file and store them
        into database, if necessary.
        """

        exposure_input.store_exposure_assets(
            self.job_ctxt.job_id, self.job_ctxt.base_path)

    def store_fragility_model(self):
        """Load fragility model and write it to database."""
        new_models = []
        fmis = models.inputs4job(self.job_ctxt.job_id, "fragility")
        for fmi in fmis:
            if fmi.fragilitymodel_set.all().count() > 0:
                continue
            path = os.path.join(self.job_ctxt.base_path, fmi.path)
            parser = fragility.FragilityModelParser(path)
            writer = FragilityDBWriter(fmi, parser)
            writer.serialize()
            new_models.append(writer.model)
        return new_models if new_models else None

    def store_vulnerability_model(self):
        """ load vulnerability and write to kvs """
        path = os.path.join(
            self.job_ctxt.base_path,
            self.job_ctxt.params["VULNERABILITY"])
        vulnerability.load_vulnerability_model(self.job_ctxt.job_id, path)

        if self.is_benefit_cost_ratio_mode():
            path = os.path.join(
                self.job_ctxt.base_path,
                self.job_ctxt.params["VULNERABILITY_RETROFITTED"])
            vulnerability.load_vulnerability_model(
                self.job_ctxt.job_id, path, retrofitted=True)

    def _serialize(self, block_id, **kwargs):
        """
        Build filename/paths for serializing and call _serialize

        Return the list of filenames. The list will be empty if nothing was
        actually serialized.
        """

        if kwargs['curve_mode'] == 'loss_ratio':
            serialize_filename = "%s-block-#%s-block#%s.xml" % (
                self.job_ctxt.params["LOSS_CURVES_OUTPUT_PREFIX"],
                self.job_ctxt.job_id,
                block_id)
        elif kwargs['curve_mode'] == 'loss':
            serialize_filename = "%s-loss-block-#%s-block#%s.xml" % (
                self.job_ctxt.params["LOSS_CURVES_OUTPUT_PREFIX"],
                self.job_ctxt.job_id,
                block_id)
        elif kwargs['curve_mode'] == 'insured_loss_curve':
            serialize_filename = "%s-insured-loss-block=#%s-block#%s.xml" % (
                'insured_loss_curves',
                self.job_ctxt.job_id,
                block_id)

        serialize_path = os.path.join(self.job_ctxt.base_path,
            self.job_ctxt.params['OUTPUT_DIR'],
            serialize_filename)

        LOG.debug("Serializing %s" % kwargs['curve_mode'])
        writer = risk_output.create_loss_curve_writer(
            self.job_ctxt.job_id, self.job_ctxt.serialize_results_to,
            serialize_path, kwargs['curve_mode'])
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
            * asset is an :py:class:`openquake.db.models.ExposureData` instance
        """
        for point in grid:
            assets = self.assets_for_cell(self.job_ctxt.job_id, point.site)
            for asset in assets:
                yield point, asset

    def _write_output_for_block(self, job_id, block_id):
        """
        Write loss / loss ratio curves to xml for a single block.
        """

        loss_curves = []
        loss_ratio_curves = []
        insured_loss_curves = []

        block = Block.from_kvs(job_id, block_id)

        for site in block.sites:
            point = self.job_ctxt.region.grid.point_at(site)
            assets = BaseRiskCalculator.assets_at(self.job_ctxt.job_id, site)

            for asset in assets:
                loss_curve = kvs.get_client().get(
                    kvs.tokens.loss_curve_key(
                    job_id, point.row, point.column, asset.asset_ref))

                loss_ratio_curve = kvs.get_client().get(
                    kvs.tokens.loss_ratio_key(
                    job_id, point.row, point.column, asset.asset_ref))

                insured_loss_curve = kvs.get_client().get(
                    kvs.tokens.insured_loss_curve_key(
                        job_id, point.row, point.column, asset.asset_ref))

                if loss_curve:
                    loss_curve = curve.Curve.from_json(loss_curve)
                    loss_curves.append((site, (loss_curve, asset)))

                if loss_ratio_curve:
                    loss_ratio_curve = curve.Curve.from_json(loss_ratio_curve)
                    loss_ratio_curves.append((site, (loss_ratio_curve, asset)))

                if insured_loss_curve:
                    insured_loss_curve = curve.Curve.from_json(
                        insured_loss_curve)

                    insured_loss_curves.append((site,
                        (insured_loss_curve, asset)))

        results = self._serialize(block_id, curves=loss_ratio_curves,
                curve_mode="loss_ratio")

        if loss_curves:
            results.extend(self._serialize(
                block_id, curves=loss_curves, curve_mode="loss",
                curve_mode_prefix="loss_curve", render_multi=True))

        if insured_loss_curves:
            results.extend(self._serialize(
                block_id, curves=insured_loss_curves,
                curve_mode="insured_loss_curve",
                curve_mode_prefix="insured_loss_curve",
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
            key = kvs.tokens.loss_key(self.job_ctxt.job_id, point.row,
                                      point.column, asset.asset_ref, loss_poe)

            loss_value = kvs.get_client().get(key)

            if loss_value:
                risk_site = shapes.Site(asset.site.x, asset.site.y)
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
        for block_id in self.job_ctxt.blocks_keys:
            key = kvs.tokens.bcr_block_key(self.job_ctxt.job_id, block_id)
            block_data = kvs.get_value_json_decoded(key)
            data += [(shapes.Site(latitude=lat, longitude=lon), payload)
                     for ((lon, lat), payload) in block_data]
        return data


class ProbabilisticRiskCalculator(BaseRiskCalculator):
    """Common base class for the Classical and Event-Based risk calculators."""

    def compute_risk(self, block_id):
        """Perform calculation and store the result in the kvs.

        Calls either :meth:`_compute_bcr` or :meth:`_compute_loss` depending
        on the calculation mode.
        """
        if self.is_benefit_cost_ratio_mode():
            return self._compute_bcr(block_id)
        else:
            return self._compute_loss(block_id)

    def _compute_bcr(self, _block_id):
        """Compute Benefit-Cost Ratio for a block of sites. Implement this in
        subclasses to provide the calculation-mode-specific logic."""
        raise NotImplementedError()

    def _compute_loss(self, _block_id):
        """Compute loss for a block of sites. Implement this in
        subclasses to provide the calculation-mode-specific logic."""
        raise NotImplementedError()

    def write_output(self):
        """Write the output of a block to db/xml.
        """
        job_ctxt = self.job_ctxt

        for block_id in job_ctxt.blocks_keys:
            #pylint: disable=W0212
            self._write_output_for_block(job_ctxt.job_id, block_id)

        for loss_poe in conditional_loss_poes(job_ctxt.params):
            path = os.path.join(job_ctxt.base_path,
                job_ctxt.params['OUTPUT_DIR'],
                "losses_at-%s.xml" % loss_poe)
            writer = risk_output.create_loss_map_writer(
                job_ctxt.job_id, job_ctxt.serialize_results_to,
                path, False)

            if writer:
                metadata = {
                    "scenario": False,
                    "timeSpan": job_ctxt.params["INVESTIGATION_TIME"],
                    "poE": loss_poe,
                }

                writer.serialize(
                    [metadata]
                    + self.asset_losses_per_site(
                        loss_poe,
                        self.grid_assets_iterator(
                            job_ctxt.region.grid)))
                LOG.info('Loss Map is at: %s' % path)

    def write_output_bcr(self):
        """
        Write BCR map in NRML format.
        """
        path = os.path.join(self.job_ctxt.base_path,
                            self.job_ctxt.params['OUTPUT_DIR'],
                            "bcr-map.xml")
        writer = risk_output.create_bcr_map_writer(
            self.job_ctxt.job_id, self.job_ctxt.serialize_results_to, path)

        metadata = {
            'interestRate': self.job_ctxt.params['INTEREST_RATE'],
            'assetLifeExpectancy': self.job_ctxt.params[
                'ASSET_LIFE_EXPECTANCY'],
        }

        writer.serialize([metadata] + self.asset_bcr_per_site())
        LOG.info('BCR Map is at: %s' % path)


class Block(object):
    """A block is a collection of sites to compute."""

    def __init__(self, job_id, block_id, sites):
        """
        :param int job_id:
            The id of a current job.
        :param int block_id:
            Sequence number of the site block (from 0 to N-1, where N is the
            number of blocks).
        :param sites:
            `list` of :class:`openquake.shapes.Site` objects.
        """
        self.job_id = job_id
        self.block_id = block_id
        self._sites = sites

    def __eq__(self, other):
        """Compares job_id, and block_id.

        This is a shallow comparison; site lists are not compared."""
        return (self.job_id == other.job_id
                and self.block_id == other.block_id)

    @property
    def sites(self):
        """The `list` of :class:`openquake.shapes.Site` objects contained by
        this Block."""
        return self._sites

    def grid(self, region):
        """Provide an iterator across the unique grid points within a region,
         corresponding to the sites within this block."""

        used_points = []
        for site in self.sites:
            point = region.grid.point_at(site)
            if point not in used_points:
                used_points.append(point)
                yield point

    @staticmethod
    def from_kvs(job_id, block_id):
        """Return the block in the underlying KVS system with the given id."""

        block_key = kvs.tokens.risk_block_key(job_id, block_id)

        raw_sites = kvs.get_value_json_decoded(block_key)

        sites = []

        for raw_site in raw_sites:
            sites.append(shapes.Site(raw_site[0], raw_site[1]))

        return Block(job_id, block_id, sites)

    def to_kvs(self):
        """Store this block into the underlying KVS system."""

        raw_sites = []

        for site in self.sites:
            raw_sites.append(site.coords)

        block_key = kvs.tokens.risk_block_key(self.job_id,
                                              self.block_id)

        kvs.set_value_json_encoded(block_key, raw_sites)


def split_into_blocks(job_id, sites, block_size=BLOCK_SIZE):
    """Creates a generator for splitting a list of sites into
    :class:`openquake.calculators.risk.general.Block`s.

    :param job_id:
        The id for the current job.
    :param sites:
        `list` of :class:`openquake.shapes.Site` objects to be split
        into blocks.
    :param int block_size:
        The maximum size for each block.
    :returns:
        For each call to this generator, the next block is returned.
    :rtype:
        :class:`openquake.calculators.risk.general.Block`
    """
    if block_size < 1:
        raise RuntimeError("block_size should be at least 1.")

    for block_id, i in enumerate(xrange(0, len(sites), block_size)):
        yield Block(job_id, block_id=block_id,
                    sites=sites[i:i + block_size])


def load_gmvs_at(job_id, site):
    """
    From the KVS, load all the ground motion values for the given site. We
    expect one ground motion value per realization of the job.
    Since there can be tens of thousands of realizations, this could return a
    large list.

    Note(LB): In the future, we may want to refactor this (and the code which
    uses the values) to use a generator instead.

    :param site: :py:class:`openquake.shapes.Site` object

    :returns: List of ground motion values (as floats). Each value represents a
                realization of the calculation for a single site.
    """
    gmfs_key = kvs.tokens.ground_motion_values_key(job_id, site)
    return [float(x['mag']) for x in kvs.get_list_json_decoded(gmfs_key)]


def hazard_input_site(job_ctxt, site):
    """
    Given a specific risk site (a location where we have
    some assets defined), return the corresponding site
    where to load hazard input from.

    If the `COMPUTE_HAZARD_AT_ASSETS_LOCATIONS` parameter
    is specified in the configuration file, the site is
    exactly the site where the asset is defined. Otherwise it
    is the center of the cell where the risk site falls in.

    :param job_ctxt: the context of the running job.
    :type job_ctxt: :class:`JobContext` instance
    :param site: the risk site (a location where there
        are some assets defined).
    :type site: :class:`openquake.shapes.Site` instance
    :returns: the location where the hazard must be
        loaded from.
    :rtype: :class:`openquake.shapes.Site` instance
    """

    if job_ctxt.has(job_config.COMPUTE_HAZARD_AT_ASSETS):
        return site
    else:
        return job_ctxt.region.grid.point_at(site).site
