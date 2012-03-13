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

from collections import defaultdict
from collections import OrderedDict
import math
import os

from celery.task import task

from django.contrib.gis import geos

from numpy import array
from numpy import exp
from numpy import histogram
from numpy import linspace
from numpy import mean
from numpy import where
from numpy import zeros
from scipy import sqrt, log
from scipy import stats
from scipy.stats import norm

from openquake.calculators.base import Calculator
from openquake.db import models
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.input.exposure import ExposureDBWriter
from openquake.job import config as job_config
from openquake.output import risk as risk_output
from openquake.parser import exposure
from openquake.parser import vulnerability
from openquake.utils import round_float
from openquake.utils.tasks import calculator_for_task


LOG = logs.LOG
BLOCK_SIZE = 100


def conditional_loss_poes(params):
    """Return the PoE(s) specified in the configuration file used to
    compute the conditional loss."""

    return [float(x) for x in params.get(
        "CONDITIONAL_LOSS_POE", "").split()]


def compute_conditional_loss(job_id, col, row, loss_curve, asset, loss_poe):
    """Compute the conditional loss for a loss curve and Probability of
    Exceedance (PoE)."""

    loss_conditional = _compute_conditional_loss(
        loss_curve, loss_poe)

    key = kvs.tokens.loss_key(job_id, row, col, asset.asset_ref, loss_poe)

    LOG.debug("Conditional loss is %s, write to key %s" %
            (loss_conditional, key))

    kvs.get_client().set(key, loss_conditional)


def _compute_conditional_loss(curve, probability):
    """Return the loss (or loss ratio) corresponding to the given
    PoE (Probability of Exceendance).

    Return the max loss (or loss ratio) if the given PoE is smaller
    than the lowest PoE defined.

    Return zero if the given PoE is greater than the
    highest PoE defined.
    """
    # dups in the curve have to be skipped
    loss_curve = shapes.Curve(unique_curve(curve))

    if loss_curve.ordinate_out_of_bounds(probability):
        if probability < loss_curve.y_values[-1]:
            return loss_curve.x_values[-1]
        else:
            return 0.0

    return loss_curve.abscissa_for(probability)


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
            job_config.BCR_EVENT_BASED_MODE
        )

    def pre_execute(self):
        """Make sure the exposure and vulnerability data is in the database."""
        self.store_exposure_assets()
        self.store_vulnerability_model()
        self.partition()

    @staticmethod
    def _cell_to_polygon(lowerleft, cell_size):
        """Return the cell with the given mid point and size.

        :param lowerleft: the lower left corner of the risk cell
        :type lowerleft: a :py:class:`openquake.shapes.Site` instance
        :param float cell_size: the configured risk cell size

        :return: the risk cell as a :py:class:`django.contrib.gis.geos.Polygon`
        """
        lon, lat = lowerleft.coords
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
    def assets_for_cell(cls, job_id, lowerleft):
        """Return exposure assets for the given job and risk cell mid-point.

        :param int job_id: the database key of the job in question
        :param lowerleft: a :py:class:`openquake.shapes.Site` instance
            with the location of the lower left corner of the risk cell
        :returns: a potentially empty list of
            :py:class:`openquake.db.models.ExposureData` instances
        """
        jp = models.profile4job(job_id)
        assert jp.region_grid_spacing is not None, "Grid spacing not known."

        cls._load_exposure_model(job_id)
        if not cls._em_inputs:
            return []

        risk_cell = cls._cell_to_polygon(lowerleft, jp.region_grid_spacing)
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
        # pylint: disable=W0404
        from openquake import engine

        self.job_ctxt.blocks_keys = []  # pylint: disable=W0201
        sites = engine.read_sites_from_exposure(self.job_ctxt)

        block_count = 0

        for block in split_into_blocks(self.job_ctxt.job_id, sites):
            self.job_ctxt.blocks_keys.append(block.block_id)
            block.to_kvs()

            block_count += 1

        LOG.info("Job has partitioned %s sites into %s blocks",
                 len(sites), block_count)

    def store_exposure_assets(self):
        """Load exposure assets and write them to database."""
        [emdl] = models.inputs4job(self.job_ctxt.job_id, "exposure")
        path = os.path.join(self.job_ctxt.base_path, emdl.path)

        exposure_parser = exposure.ExposureModelFile(path)
        writer = ExposureDBWriter(emdl)
        writer.serialize(exposure_parser)

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
        """ Given a job and a block, write out a plotted curve """
        loss_ratio_curves = []
        loss_curves = []
        block = Block.from_kvs(job_id, block_id)
        for point, asset in self.grid_assets_iterator(
                block.grid(self.job_ctxt.region)):
            site = shapes.Site(asset.site.x, asset.site.y)

            loss_curve = kvs.get_client().get(
                kvs.tokens.loss_curve_key(
                    job_id, point.row, point.column, asset.asset_ref))
            loss_ratio_curve = kvs.get_client().get(
                kvs.tokens.loss_ratio_key(
                    job_id, point.row, point.column, asset.asset_ref))

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
            key = kvs.tokens.loss_key(self.job_ctxt.job_id, point.row,
                                      point.column, asset.asset_ref, loss_poe)

            loss_value = kvs.get_client().get(key)

            LOG.debug("Loss for asset %s at %s %s is %s" %
                (asset.asset_ref, asset.site.x, asset.site.y, loss_value))

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
                job_ctxt.job_id, job_ctxt.serialize_results_to, path,
                False)

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
        taxonomy is the same. The asset's `taxonomy` is only needed for
        correlated jobs and unlikely to be available for uncorrelated ones.
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

            if asset.taxonomy not in samples:
                samples[asset.taxonomy] = norm.rvs(loc=0, scale=1)
            return samples[asset.taxonomy]


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
                ({'bcr': 1, 'eal_retrofitted': 2, 'eal_original': 3}, assetID),
                ({'bcr': 3, 'eal_retrofitted': 4, 'eal_original': 5}, assetID),
                ...]),
             ...]
    """
    # too many local vars (16/15) -- pylint: disable=R0914
    result = defaultdict(list)

    vuln_curves = vulnerability.load_vuln_model_from_kvs(job_id)
    vuln_curves_retrofitted = vulnerability.load_vuln_model_from_kvs(
        job_id, retrofitted=True)

    for point in points:
        assets = BaseRiskCalculator.assets_for_cell(job_id, point.site)
        for asset in assets:
            vuln_function = vuln_curves[asset.taxonomy]
            loss_curve = get_loss_curve(point, vuln_function, asset)
            LOG.info('for asset %s loss_curve = %s',
                     asset.asset_ref, loss_curve)
            eal_original = compute_mean_loss(loss_curve)

            vuln_function = vuln_curves_retrofitted[asset.taxonomy]
            loss_curve = get_loss_curve(point, vuln_function, asset)
            LOG.info('for asset %s loss_curve retrofitted = %s',
                     asset.asset_ref, loss_curve)
            eal_retrofitted = compute_mean_loss(loss_curve)

            bcr = compute_bcr(eal_original, eal_retrofitted,
                              interest_rate, asset_life_expectancy,
                              asset.retrofitting_cost)

            LOG.info('for asset %s EAL original = %f, '
                     'EAL retrofitted = %f, BCR = %f',
                     asset.asset_ref, eal_original, eal_retrofitted, bcr)

            key = (asset.site.x, asset.site.y)

            result[key].append(({'bcr': bcr,
                                 'eal_original': eal_original,
                                 'eal_retrofitted': eal_retrofitted},
                                asset.asset_ref))

    return result.items()


def compute_loss_curve(loss_ratio_curve, asset):
    """Compute the loss curve for the given asset value.

    A loss curve is obtained from a loss ratio curve by
    multiplying each X value (loss ratio) for the given asset.
    """

    if not asset:
        return shapes.EMPTY_CURVE

    return loss_ratio_curve.rescale_abscissae(asset)


def _compute_mid_mean_pe(loss_ratio_curve):
    """Compute a new loss ratio curve taking the mean values."""

    loss_ratios = loss_ratio_curve.abscissae
    pes = loss_ratio_curve.ordinates

    ratios = collect(loop(loss_ratios, lambda x, y: mean([x, y])))
    mid_pes = collect(loop(pes, lambda x, y: mean([x, y])))

    return shapes.Curve(zip(ratios, mid_pes))


def _compute_mid_po(loss_ratio_pe_mid_curve):
    """Compute a loss ratio curve that has PoOs
    (Probabilities of Occurrence) as Y values."""

    loss_ratios = loss_ratio_pe_mid_curve.abscissae
    pes = loss_ratio_pe_mid_curve.ordinates

    ratios = collect(loop(loss_ratios, lambda x, y: mean([x, y])))
    pos = collect(loop(pes, lambda x, y: x - y))

    return shapes.Curve(zip(ratios, pos))


def compute_mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    mid_curve = _compute_mid_po(_compute_mid_mean_pe(curve))
    return sum(i * j for i, j in zip(
            mid_curve.abscissae, mid_curve.ordinates))


def loop(elements, func, *args):
    """Loop over the given elements, yielding func(current, next, *args)."""
    for idx in xrange(elements.size - 1):
        yield func(elements[idx], elements[idx + 1], *args)


def collect(iterator):
    """Simply collect the data taken from the given iterator."""
    data = []

    for element in iterator:
        data.append(element)

    return data


def unique_curve(curve):
    """ extracts unique values from a curve """
    seen = OrderedDict()

    for ordinate, abscissa in zip(curve.ordinates, curve.abscissae):
        seen[ordinate] = abscissa

    return zip(seen.values(), seen.keys())


def compute_bcr(eal_original, eal_retrofitted, interest_rate,
                asset_life_expectancy, retrofitting_cost):
    """
    Compute the Benefit-Cost Ratio.

    BCR = (EALo - EALr)(1-exp(-r*t))/(r*C)

    Where:

    * BCR -- Benefit cost ratio
    * EALo -- Expected annual loss for original asset
    * EALr -- Expected annual loss for retrofitted asset
    * r -- Interest rate
    * t -- Life expectancy of the asset
    * C -- Retrofitting cost
    """
    return ((eal_original - eal_retrofitted)
            * (1 - exp(- interest_rate * asset_life_expectancy))
            / (interest_rate * retrofitting_cost))


def compute_loss_ratios(vuln_function, gmf_set, epsilon_provider, asset):
    """Compute the set of loss ratios using the set of
    ground motion fields passed.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: ground motion fields used to compute the loss ratios
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    if vuln_function.is_empty:
        return array([])

    all_covs_are_zero = (vuln_function.covs <= 0.0).all()

    if all_covs_are_zero:
        return _mean_based(vuln_function, gmf_set)
    else:
        return _sampled_based(vuln_function, gmf_set, epsilon_provider, asset)


def _sampled_based(vuln_function, gmf_set, epsilon_provider, asset):
    """Compute the set of loss ratios when at least one CV
    (Coefficent of Variation) defined in the vulnerability function
    is greater than zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: ground motion fields used to compute the loss ratios
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    loss_ratios = []

    means = vuln_function.loss_ratio_for(gmf_set["IMLs"])
    covs = vuln_function.cov_for(gmf_set["IMLs"])

    for mean_ratio, cov in zip(means, covs):
        if mean_ratio <= 0.0:
            loss_ratios.append(0.0)
        else:
            variance = (mean_ratio * cov) ** 2.0

            epsilon = epsilon_provider.epsilon(asset)
            sigma = math.sqrt(
                        math.log((variance / mean_ratio ** 2.0) + 1.0))

            mu = math.log(mean_ratio ** 2.0 / math.sqrt(
                    variance + mean_ratio ** 2.0))

            loss_ratios.append(math.exp(mu + (epsilon * sigma)))

    return array(loss_ratios)


def _mean_based(vuln_function, gmf_set):
    """Compute the set of loss ratios when the vulnerability function
    has all the CVs (Coefficent of Variation) set to zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: the set of ground motion
        fields used to compute the loss ratios.
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    """

    loss_ratios = []
    retrieved = {}
    imls = vuln_function.imls

    # seems like with numpy you can only specify a single fill value
    # if the x_new is outside the range. Here we need two different values,
    # depending if the x_new is below or upon the defined values
    for ground_motion_field in gmf_set["IMLs"]:
        if ground_motion_field < imls[0]:
            loss_ratios.append(0.0)
        elif ground_motion_field > imls[-1]:
            loss_ratios.append(vuln_function.loss_ratios[-1])
        else:
            # The actual value is computed later
            mark = len(loss_ratios)
            retrieved[mark] = gmf_set['IMLs'][mark]
            loss_ratios.append(0.0)

    means = vuln_function.loss_ratio_for(retrieved.values())

    for mark, mean_ratio in zip(retrieved.keys(), means):
        loss_ratios[mark] = mean_ratio

    return array(loss_ratios)


def _compute_loss_ratios_range(loss_ratios, loss_histogram_bins):
    """Compute the range of loss ratios used to build the loss ratio curve.

    The range is obtained by computing the set of evenly spaced numbers
    over the interval [min_loss_ratio, max_loss_ratio].

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param int loss_histogram_bins:
        The number of bins to use in the computed loss histogram.
    """
    return linspace(loss_ratios.min(), loss_ratios.max(), loss_histogram_bins)


def _compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."

    # ruptures (earthquake) occured but probably due to distance,
    # magnitude and soil conditions, no ground motion was felt at that location
    if (loss_ratios <= 0.0).all():
        return zeros(loss_ratios_range.size - 1)

    invalid_ratios = lambda ratios: where(array(ratios) <= 0.0)[0].size

    hist = histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted on the first bin
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
    return hist


def _compute_rates_of_exceedance(cum_histogram, tses):
    """Compute the rates of exceedance for the given cumulative histogram
    using the given tses (tses is time span * number of realizations)."""

    if tses <= 0:
        raise ValueError("TSES is not supposed to be less than zero!")

    return (array(cum_histogram).astype(float) / tses)


def _compute_probs_of_exceedance(rates_of_exceedance, time_span):
    """Compute the probabilities of exceedance using the given rates of
    exceedance and the given time span."""

    poe = lambda rate: 1 - math.exp((rate * -1) * time_span)
    return array([poe(rate) for rate in rates_of_exceedance])


def compute_alpha(mean_loss_ratio, stddev):
    """
    Compute alpha value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed alpha value
    """

    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
                mean_loss_ratio ** 2)


def compute_beta(mean_loss_ratio, stddev):
    """
    Compute beta value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed beta value
    """

    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
        (mean_loss_ratio - mean_loss_ratio ** 2))


class Lognorm(object):
    """ Simple Wrapper to use in a generic way survival functions """

    @staticmethod
    def survival_function(loss_ratio, **kwargs):
        """
            Static method that prepares the calculation parameters
            to be passed to stats.lognorm.sf

            :param loss_ratio: current loss ratio
            :type loss_ratio: float

            :param kwargs: convenience dictionary
            :type kwargs: :py:class:`dict` with the following
                keys:
                    **vf** - vulnerability function as provided by
                            :py:class:`openquake.shapes.VulnerabilityFunction`
                    **col** - matrix column number
        """
        vuln_function = kwargs.get('vf')
        position = kwargs.get('col')

        vf_loss_ratio = vuln_function.loss_ratios[position]

        stddev = vuln_function.covs[position] * vf_loss_ratio

        variance = stddev ** 2.0

        sigma = sqrt(log((variance / vf_loss_ratio ** 2.0) + 1.0))
        mu = exp(log(vf_loss_ratio ** 2.0 /
            sqrt(variance + vf_loss_ratio ** 2.0)))

        return stats.lognorm.sf(loss_ratio, sigma, scale=mu)


class BetaDistribution(object):
    """ Simple Wrapper to use in a generic way Beta Distributions """

    @staticmethod
    def survival_function(loss_ratio, **kwargs):
        """
            Static method that prepares the calculation parameters
            to be passed to stats.beta.sf


            :param loss_ratio: current loss ratio
            :type loss_ratio: float

            :param kwargs: convenience dictionary
            :type kwargs: :py:class:`dict` with the following
                keys:
                    **vf** - vulnerability function as provided by
                            :py:class:`openquake.shapes.VulnerabilityFunction`
                    **col** - matrix column number
        """
        vuln_function = kwargs.get('vf')
        col = kwargs.get('col')
        vf_loss_ratio = vuln_function.loss_ratios[col]
        stddev = vuln_function.stddevs[col]

        return stats.beta.sf(loss_ratio,
                compute_alpha(vf_loss_ratio, stddev),
                compute_beta(vf_loss_ratio, stddev))


def compute_loss_ratio_curve(vuln_function, gmf_set,
        epsilon_provider, asset, loss_histogram_bins, loss_ratios=None):
    """Compute a loss ratio curve using the probabilistic event based approach.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: the set of ground motion
        fields used to compute the loss ratios.
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposureModelFile`
    :param int loss_histogram_bins:
        The number of bins to use in the computed loss histogram.
    """

    # with no gmfs (no earthquakes), an empty curve is enough
    if not gmf_set["IMLs"]:
        return shapes.EMPTY_CURVE

    if loss_ratios is None:
        loss_ratios = compute_loss_ratios(
            vuln_function, gmf_set, epsilon_provider, asset)

    loss_ratios_range = _compute_loss_ratios_range(
            loss_ratios, loss_histogram_bins)

    probs_of_exceedance = _compute_probs_of_exceedance(
            _compute_rates_of_exceedance(_compute_cumulative_histogram(
            loss_ratios, loss_ratios_range), gmf_set["TSES"]),
            gmf_set["TimeSpan"])

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


def _generate_curve(losses, probs_of_exceedance):
    """Generate a loss ratio (or loss) curve, given a set of losses
    and corresponding PoEs (Probabilities of Exceedance).

    This function is intended to be used internally.
    """

    mean_losses = collect(loop(losses, lambda x, y: mean([x, y])))
    return shapes.Curve(zip(mean_losses, probs_of_exceedance))


class AggregateLossCurve(object):
    """Aggregate a set of losses and produce the resulting loss curve."""

    def __init__(self):
        self.losses = None

    def append(self, losses):
        """Accumulate losses into a single sum..

        :param losses: an array of loss values.
        :type losses: 1-dimensional :py:class:`numpy.ndarray`
        """

        if self.losses is None:
            self.losses = losses
        else:
            self.losses = self.losses + losses

    @property
    def empty(self):
        """Return true is this aggregate curve has no losses
        associated, false otherwise."""
        return self.losses is None

    def compute(self, tses, time_span, loss_histogram_bins):
        """Compute the aggregate loss curve.

        :param tses: time representative of the Stochastic Event Set.
        :type tses: float
        :param time_span: time span parameter.
        :type time_span: float
        :param int loss_histogram_bins:
            The number of bins to use in the computed loss histogram.
        """

        if self.empty:
            return shapes.EMPTY_CURVE

        losses = self.losses
        loss_range = _compute_loss_ratios_range(losses, loss_histogram_bins)

        probs_of_exceedance = _compute_probs_of_exceedance(
                _compute_rates_of_exceedance(_compute_cumulative_histogram(
                losses, loss_range), tses), time_span)

        return _generate_curve(loss_range, probs_of_exceedance)
