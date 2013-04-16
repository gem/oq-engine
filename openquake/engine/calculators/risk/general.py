# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
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

import random
import StringIO
import numpy

from openquake.risklib import scientific

from django import db

from openquake.engine import logs
from openquake.engine.utils import config
from openquake.engine.db import models
from openquake.engine.calculators import base, post_processing
from openquake.engine import export
from openquake.engine.utils import stats
from openquake.engine.calculators.risk import hazard_getters
from openquake.nrmllib.risk import parsers

# FIXME: why is a writer in a package called "input" ?
from openquake.engine.input import exposure as db_writer


#: Maximum number of loss curves to cache in buffers, for selects and inserts
_CURVE_CACHE_SIZE = 100000


class BaseRiskCalculator(base.CalculatorNext):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies:
        A dictionary mapping each taxonomy with the number of assets the
        calculator will work on. Assets are extracted from the exposure input
        and filtered according to the `RiskCalculation.region_constraint`.

    :attribute asset_offsets:
        A generator of asset offsets used by each celery task. Assets are
        ordered by their id. An asset offset is an int that identify the set of
        assets going from offset to offset + block_size.

    :attribute dict vulnerability_functions:
        A dict mapping taxonomy to vulnerability functions used for this
        calculation.

    :attribute rnd:
        The random number generator (initialized with a master seed) used for
        sampling.

    :attribute dict taxonomies_imts:
        A dictionary mapping taxonomies to intensity measure type, to
        support structure dependent intensity measure types
    """

    hazard_getter = None  # the name of the hazard getter class; to override

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)

        self.taxonomies = None
        self.rnd = None
        self.vulnerability_functions = None
        self.taxonomies_imts = dict()

    def pre_execute(self):
        """
        In this phase, the general workflow is:

            1. Parse the exposure input and store the exposure data (if not
               already present)
            2. Check if the exposure filtered with region_constraint is not
               empty
            3. Parse the risk models
            4. Initialize progress counters
            5. Initialize random number generator

        """

        # reload the risk calculation to avoid getting raw string
        # values instead of arrays
        self.job.risk_calculation = models.RiskCalculation.objects.get(
            pk=self.rc.pk)

        with logs.tracing('store exposure'):
            if self.rc.exposure_input is None:
                queryset = self.rc.inputs.filter(input_type='exposure')

                if queryset.exists():
                    self._store_exposure(queryset.all()[0])
                else:
                    raise RuntimeError("No exposure model given in input")

            self.taxonomies = self.rc.exposure_model.taxonomies_in(
                self.rc.region_constraint)

            if not sum(self.taxonomies.values()):
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])

        with logs.tracing('store risk model'):
            self.set_risk_models()

        if self.hc is not None:
            imts = self.hc.get_imts()

            # check that the hazard calculation has all the imts needed by
            # the risk calculation
            for imt in set(self.taxonomies_imts.values()):
                if not imt in imts:
                    raise RuntimeError(
                        "There is no hazard output for the intensity measure "
                        "%s; the available IMTs are %s" % (imt, imts))

        self._initialize_progress(sum(self.taxonomies.values()))

        self.rnd = random.Random()
        self.rnd.seed(self.rc.master_seed)

    def block_size(self):
        """
        Number of assets handled per task.
        """
        return int(config.get('risk', 'block_size'))

    def concurrent_tasks(self):
        """
        Number of tasks to be in queue at any given time.
        """
        return int(config.get('risk', 'concurrent_tasks'))

    def task_arg_gen(self, block_size):
        """
        Generator function for creating the arguments for each task.

        It is responsible for the distribution strategy. It divides
        the considered exposure into chunks of homogeneous assets
        (i.e. having the same taxonomy). The chunk size is given by
        the `block_size` openquake config parameter

        :param int block_size:
            The number of work items per task (sources, sites, etc.).

        :returns:
            An iterator over a list of arguments. Each contains:

            1. the job id
            2. the exposure subset on which the celery task is applied on
            3. the hazard getter and the hazard_id to be used
            4. a seed (eventually generated from a master seed)
            5. the output containers to be populated
            6. the specific calculator parameter set
        """
        output_containers = dict(
            (hazard_output.id,
             self.create_outputs(hazard_output))
            for hazard_output in self.considered_hazard_outputs())

        if self.rc.hazard_calculation:
            statistical_output_containers = self.create_statistical_outputs()
        else:
            statistical_output_containers = []

        calculator_parameters = self.calculator_parameters

        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = self.rc.exposure_model.get_asset_chunk(
                        taxonomy,
                        self.rc.region_constraint, offset, block_size)

                # Get the imt depending on the taxonomy of the assets
                # (SD-IMT) and create the needed hazard getters for
                # all the hazard output
                imt = self.taxonomies_imts[taxonomy]
                hazard = dict((ho.id, self.create_getter(ho, imt, assets))
                              for ho in self.considered_hazard_outputs())

                worker_args = self.worker_args(taxonomy)

                logs.LOG.debug("Task with %s assets (%s, %s) got args %s",
                               len(assets), offset, block_size, worker_args)

                yield ([self.job.id, hazard] +
                       worker_args +
                       [output_containers] +
                       [statistical_output_containers] +
                       calculator_parameters)

    def worker_args(self, taxonomy):
        """
        :returns:
            A fixed list of arguments that a calculator may want to pass to a
            worker. Default to a seed generated from the master seed and the
            vulnerability function associated with the assets taxonomy. May be
            overriden.
        """
        return [self.rnd.randint(0, models.MAX_SINT_32),
                self.vulnerability_functions[taxonomy]]

    def export(self, *args, **kwargs):
        """
        If requested by the user, automatically export all result artifacts.

        :returns:
            A list of the export filenames, including the absolute path to each
            file.
        """

        exported_files = []
        with logs.tracing('exports'):
            if 'exports' in kwargs and kwargs['exports']:
                exported_files = sum([
                    export.risk.export(output.id, self.rc.export_dir)
                    for output in export.core.get_outputs(self.job.id)], [])

                for exp_file in exported_files:
                    logs.LOG.debug('exported %s' % exp_file)
        return exported_files

    def considered_hazard_outputs(self):
        """
        Returns the list of hazard outputs to be considered
        """
        if self.rc.hazard_output:
            return [self.rc.hazard_output]
        else:
            return self.hazard_outputs(self.rc.hazard_calculation)

    def hazard_outputs(self, hazard_calculation):
        """
        Calculators must override this to select from the hazard calculation
        given in input which are the Output objects to be considered by the
        risk calculation to get the actual hazard input.

        Result objects should be ordered (e.g. by id) and be associated to a
        hazard logic tree realization.

        :returns:
            A list of :class:`openquake.engine.db.models.Output`
            objects to be used for a risk calculation.
        """
        raise NotImplementedError

    def create_statistical_outputs(self):
        """
        Create mean/quantile `Output` and `LossCurve`/`LossMap` containers.
        """

        mean_loss_curve_id = models.LossCurve.objects.create(
            output=models.Output.objects.create_output(
                job=self.job,
                display_name='Mean Loss Curves',
                output_type='loss_curve'),
            statistics='mean').id

        quantile_loss_curve_ids = dict(
            (quantile,
             models.LossCurve.objects.create(
                 output=models.Output.objects.create_output(
                     job=self.job,
                     display_name='quantile(%s)-curves' % quantile,
                     output_type='loss_curve'),
                 statistics='quantile',
                 quantile=quantile).id)
            for quantile in self.rc.quantile_loss_curves or [])

        mean_loss_map_ids = dict(
            (poe,
             models.LossMap.objects.create(
                 output=models.Output.objects.create_output(
                     job=self.job,
                     display_name="Mean Loss Map poe=%.4f" % poe,
                     output_type="loss_map"),
                 statistics="mean").id)
            for poe in self.rc.conditional_loss_poes or [])

        quantile_loss_map_ids = dict(
            (quantile,
             dict(
                 (poe, models.LossMap.objects.create(
                     output=models.Output.objects.create_output(
                         job=self.job,
                         display_name="Quantile Loss Map poe=%.4f q=%.4f" % (
                             poe, quantile),
                         output_type="loss_map"),
                     statistics="quantile",
                     quantile=quantile).id)
                 for poe in self.rc.conditional_loss_poes))
            for quantile in self.rc.quantile_loss_curves or [])

        return [mean_loss_curve_id, quantile_loss_curve_ids,
                mean_loss_map_ids, quantile_loss_map_ids]

    def create_getter(self, output, imt, assets):
        """
        Create an instance of :class:`.hazard_getters.HazardGetter` associated
        to an hazard output.

        Calculator must override this to create the proper hazard getter.

        :param output:
            The ID of an :class:`openquake.engine.db.models.Output` produced by
            a hazard calculation.

        :param str imt:
            The imt used by the hazard getter to filter the hazard (a hazard
            output may contain values computed in multiple imt).

        :returns:
            A tuple where the first element is the hazard getter and the second
            is the associated weight (if `output` is associated with a logic
            tree realization).

        :raises:
            `RuntimeError` if the hazard associated with the `output` is not
            suitable to be used with this calculator.
        """
        raise NotImplementedError

    @property
    def rc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.engine.db.models.RiskCalculation`.
        """
        return self.job.risk_calculation

    @property
    def hc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.engine.db.models.HazardCalculation`.
        """
        return self.rc.get_hazard_calculation()

    @property
    def calculator_parameters(self):
        """
        The specific calculation parameters passed as args to the
        celery task function. Calculators should override this to
        provide custom arguments to its celery task
        """
        return []

    def _store_exposure(self, exposure_model_input):
        """
        Load exposure assets and write them to database.

        :param exposure_model_input: a
        :class:`openquake.engine.db.models.Input` object with input
        type `exposure`
        """

        # If this was an existing model, it was already parsed and should be in
        # the DB.
        if models.ExposureModel.objects.filter(
                input=exposure_model_input).exists():
            logs.LOG.debug("skipping storing exposure as an input model "
                           "was already present")
            return exposure_model_input.exposuremodel

        content = StringIO.StringIO(
            exposure_model_input.model_content.raw_content_ascii)
        db_writer.ExposureDBWriter(exposure_model_input).serialize(
            parsers.ExposureModelParser(content))
        return exposure_model_input.exposuremodel

    def _initialize_progress(self, total):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        logs.LOG.debug("Computing risk over %d assets" % total)
        self.progress.update(total=total)
        stats.pk_set(self.job.id, "lvr", 0)
        stats.pk_set(self.job.id, "nrisk_total", total)
        stats.pk_set(self.job.id, "nrisk_done", 0)

    def set_risk_models(self):
        self.vulnerability_functions = self.get_vulnerability_model()
        self.check_taxonomies(self.vulnerability_functions)

    def check_taxonomies(self, taxonomies):
        """
        If the model has less taxonomies than the exposure raises an
        error unless the parameter ``taxonomies_from_model`` is set.

        :param taxonomies:
            Taxonomies coming from the fragility/vulnerability model
        """
        orphans = set(self.taxonomies) - set(taxonomies)
        if orphans:
            msg = ('The following taxonomies are in the exposure model '
                   'but not in the risk model: %s' % sorted(orphans))
            if self.rc.taxonomies_from_model:
                # only consider the taxonomies in the fragility model
                self.taxonomies = dict((t, self.taxonomies[t])
                                       for t in self.taxonomies
                                       if t in taxonomies)
                logs.LOG.warn(msg)
            else:
                # all taxonomies in the exposure must be covered
                raise RuntimeError(msg)

    def get_vulnerability_model(self, retrofitted=False):
        """
        Load and parse the vulnerability model input associated with this
        calculation.

        As a side effect, it also stores the mapping between
        taxonomies and IMT (that is needed for further hazard
        filtering) in the attribute `taxonomies_imts`.

        :param bool retrofitted:
            `True` if the retrofitted model is going to be parsed

        :returns:
            A dictionary mapping each taxonomy to a
            :class:`openquake.risklib.scientific.VulnerabilityFunction`
            instance.
        """

        if retrofitted:
            input_type = "vulnerability_retrofitted"
        else:
            input_type = "vulnerability"

        content = StringIO.StringIO(
            self.rc.inputs.get(
                input_type=input_type).model_content.raw_content_ascii)

        return self.parse_vulnerability_model(content)

    def parse_vulnerability_model(self, vuln_content):
        """
        Parse the vulnerability model and return a `dict` of vulnerability
        functions keyed by taxonomy.

        If a taxonomy is associated with more than one Intensity Measure Type
        (IMT), a `ValueError` will be raised.

        :param vuln_content:
            File-like object containg the vulnerability model XML.
        :returns:
            A dictionary mapping each taxonomy (as a `str`) to a
            :class:`openquake.risklib.scientific.VulnerabilityFunction`
            instance.
        :raises:
            * `ValueError` if a taxonomy is associated with more than one IMT.
            * `ValueError` if a loss ratio is 0 and its corresponding CoV
              (Coefficient of Variation) is > 0.0. This is mathematically
              impossible.
        """
        vfs = dict()

        for record in parsers.VulnerabilityModelParser(vuln_content):
            taxonomy = record['ID']
            imt = record['IMT']
            loss_ratios = record['lossRatio']
            covs = record['coefficientsVariation']


            registered_imt = self.taxonomies_imts.get(taxonomy, imt)

            if imt != registered_imt:
                raise ValueError("The same taxonomy is associated with "
                                 "different imts %s and %s" % (
                                 imt, registered_imt))
            else:
                self.taxonomies_imts[taxonomy] = imt

            try:
                vfs[taxonomy] = scientific.VulnerabilityFunction(
                    record['IML'],
                    loss_ratios,
                    covs,
                    record['probabilisticDistribution'])
            except ValueError, err:
                msg = (
                    "Invalid vulnerability function with ID '%s': %s"
                    % (taxonomy, err.message)
                )
                raise ValueError(msg)
        return vfs

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves, LossMaps

        The default behavior is to create a loss curve and loss maps
        output.

        :returns:
            A dictionary mapping an Output object ID to a list of int (id of
            containers) or dict (poe->int)
        """

        job = self.job

        # add loss curve containers
        loss_curve_id = models.LossCurve.objects.create(
            hazard_output_id=hazard_output.id,
            output=models.Output.objects.create_output(
                job, "Loss Curve set for hazard %s" % hazard_output.id,
                "loss_curve")).pk

        # loss maps (or conditional loss maps) ...
        loss_map_ids = dict()

        if self.rc.conditional_loss_poes is not None:
            for poe in self.rc.conditional_loss_poes:
                loss_map_ids[poe] = models.LossMap.objects.create(
                    hazard_output_id=hazard_output.id,
                    output=models.Output.objects.create_output(
                        self.job,
                        "Loss Map Set with poe %s for hazard %s" % (
                            poe, hazard_output.id),
                        "loss_map"),
                    poe=poe).pk

        return [loss_curve_id, loss_map_ids]


def hazard_getter(hazard_getter_name, hazard_id, *args):
    """
    Initializes and returns an hazard getter
    """
    return getattr(hazard_getters, hazard_getter_name)(hazard_id, *args)


@db.transaction.commit_on_success
def update_aggregate_losses(curve_id, losses):
    """
    Update an aggregate loss curve with new `losses` (that will be
    added).

    :type losses:
        Numpy array.
    """

    # to avoid race conditions we lock the table
    query = """
      SELECT * FROM riskr.aggregate_loss_curve_data WHERE
      loss_curve_id = %s FOR UPDATE
    """

    [curve_data] = models.AggregateLossCurveData.objects.raw(query, [curve_id])

    if curve_data.losses:
        curve_data.losses = losses + curve_data.losses
    else:
        curve_data.losses = losses

    curve_data.save()


# FIXME
# Temporary solution, loss map for Scenario Risk
# is a different concept with respect to a loss map
# for a different calculator.

def write_loss_map_data(loss_map_id, asset, loss_ratio, std_dev=None):
    """
    Create :class:`openquake.engine.db.models.LossMapData`

    :param int loss_map_id:
        The ID of the output container.
    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.
    :param float value:
        Loss ratio value.
    :param float std_dev:
        Standard devation on loss ratios.
    """

    if std_dev is not None:
        std_dev = std_dev * asset.value

    return models.LossMapData.objects.create(
        loss_map_id=loss_map_id,
        asset_ref=asset.asset_ref,
        value=loss_ratio * asset.value,
        std_dev=std_dev,
        location=asset.site)


def write_bcr_distribution(
        bcr_distribution_id, asset, eal_original, eal_retrofitted, bcr):
    """
    Create a new :class:`openquake.engine.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id:
        The ID of :class:`openquake.engine.db.models.BCRDistribution` instance
        that holds the BCR map.

    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.

    :param float eal_original:
        Expected annual loss in the original model for the asset.
    :param float eal_retrofitted:
        Expected annual loss in the retrofitted model for the asset.
    :param float bcr:
        Benefit Cost Ratio parameter.
    """
    models.BCRDistributionData.objects.create(
        bcr_distribution_id=bcr_distribution_id,
        asset_ref=asset.asset_ref,
        average_annual_loss_original=eal_original * asset.value,
        average_annual_loss_retrofitted=eal_retrofitted * asset.value,
        bcr=bcr,
        location=asset.site)


def write_loss_curve(
        loss_curve_id, asset, poes, loss_ratios, average_loss_ratio):
    """
    Stores and returns a :class:`openquake.engine.db.models.LossCurveData`
    where the data are got by `asset_output` and the
    :class:`openquake.engine.db.models.LossCurve` output container is
    identified by `loss_curve_id`.

    :param int loss_curve_id:
        The ID of the output container.
    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.
    :param loss_ratios:
        A list of loss ratios.
    :param poes:
        A list of poes associated to `loss_ratios`.
    :param float average_loss_ratio:
        The average loss ratio of the curve.
    """
    return models.LossCurveData.objects.create(
        loss_curve_id=loss_curve_id,
        asset_ref=asset.asset_ref,
        location=asset.site,
        poes=poes,
        loss_ratios=loss_ratios,
        asset_value=asset.value,
        average_loss_ratio=average_loss_ratio)


def compute_and_write_statistics(
        mean_loss_curve_id, quantile_loss_curve_ids,
        mean_loss_map_ids, quantile_loss_map_ids,
        mean_loss_fraction_ids, quantile_loss_fraction_ids,
        weights, assets, loss_ratio_curve_matrix, hazard_montecarlo_p,
        conditional_loss_poes, poes_disagg, assume_equal):
    """
    :param int mean_loss_curve_id:
      the ID of the mean loss curve output container
    :param dict quantile_loss_curve_id:
      it maps quantile values to IDs of quantile loss curve output containers
    :param dict mean_loss_map_id:
      it maps poes to IDs of mean loss map output containers
    :param dict quantile_loss_map_ids:
      it maps quantile values to dicts poe -> ID of loss map output container
    :param dict mean_loss_fraction_ids:
      it maps poes to IDs of mean loss fraction output containers
    :param dict quantile_loss_fraction_ids:
      it maps quantile values to dicts poe -> ID of loss fraction output
      containers
    :param weights:
      the weights of each realization considered
    :param assets:
      the assets on which we are computing the statistics
    :param loss_ratio_curve_matrix:
      a numpy 2d array that stores the individual loss curves for each asset
      in `assets`
    :param bool hazard_montecarlo_p:
      True when explicit mean/quantiles calculation is used
    :param list conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param list poes_disagg:
      The poes taken into account to compute the loss maps needed for
      disaggregation
    :param str assume_equal:
      equal to "support" if loss curves has the same abscissae, or "image" if
      they have the same ordinates
    """

    for i, asset in enumerate(assets):
        loss_ratio_curves = loss_ratio_curve_matrix[:, i]

        if assume_equal == 'support':
            loss_ratios = loss_ratio_curves[0].abscissae
            curves_poes = [curve.ordinates for curve in loss_ratio_curves]
        elif assume_equal == 'image':
            max_losses = [lc.abscissae[-1] for lc in loss_ratio_curves
                          if lc.abscissae[-1]]
            if not max_losses:  # no damage. all trivial curves
                logs.LOG.info("No damages in asset %s" % asset)
                loss_ratios = loss_ratio_curves[0].abscissae
                curves_poes = [curve.ordinates for curve in loss_ratio_curves]
            else:  # standard case
                reference_curve = loss_ratio_curves[numpy.argmin(max_losses)]
                loss_ratios = reference_curve.abscissae

                curves_poes = [
                    reference_curve.ordinate_for(
                        [poe for loss, poe
                         in zip(curve.abscissae, curve.ordinates)
                         if loss <= min(max_losses)])
                    for curve in loss_ratio_curves]

        else:
            raise NotImplementedError

        quantiles_poes = dict()

        for quantile, quantile_loss_curve_id in (
                quantile_loss_curve_ids.items()):
            if hazard_montecarlo_p:
                q_curve = post_processing.weighted_quantile_curve(
                    curves_poes, weights, quantile)
            else:
                q_curve = post_processing.quantile_curve(curves_poes, quantile)

            quantiles_poes[quantile] = q_curve.tolist()

            write_loss_curve(
                quantile_loss_curve_id,
                asset,
                quantiles_poes[quantile],
                loss_ratios,
                scientific.average_loss(loss_ratios, quantiles_poes[quantile]))

        # then mean loss curve
        mean_poes = None
        if mean_loss_curve_id:
            mean_curve = post_processing.mean_curve(curves_poes, weights)
            mean_poes = mean_curve.tolist()

            write_loss_curve(
                mean_loss_curve_id,
                asset,
                mean_poes,
                loss_ratios,
                scientific.average_loss(loss_ratios, mean_poes))

        # mean and quantile loss maps
        loss_ratios = loss_ratio_curve_matrix[0, 0].abscissae

        for poe in conditional_loss_poes:
            write_loss_map_data(
                mean_loss_map_ids[poe],
                asset,
                scientific.conditional_loss_ratio(loss_ratios, mean_poes, poe))
            for quantile, poes in quantiles_poes.items():
                write_loss_map_data(
                    quantile_loss_map_ids[quantile][poe],
                    asset,
                    scientific.conditional_loss_ratio(loss_ratios, poes, poe))

        # mean and quantile loss fractions (only disaggregation by
        # taxonomy is supported here)
        for poe in poes_disagg:
            write_loss_fraction_data(
                mean_loss_fraction_ids[poe],
                value=asset.taxonomy,
                location=asset.site,
                absolute_loss=scientific.conditional_loss_ratio(
                    loss_ratios, mean_poes, poe) * asset.value)
            for quantile, poes in quantiles_poes.items():
                write_loss_fraction_data(
                    quantile_loss_fraction_ids[quantile][poe],
                    value=asset.taxonomy,
                    location=asset.site,
                    absolute_loss=scientific.conditional_loss_ratio(
                        loss_ratios, poes, poe) * asset.value)


def write_loss_fraction_data(loss_fraction_id, value, location, absolute_loss):
    """
    Create, save and return an instance of
    :class:`openquake.engine.db.models.LossFractionData` associated
    with `loss_fraction_id`, `value`, `location` and `absolute_loss`
    :param int loss_fraction_id:
       an ID to an output container instance
       of type :class:`openquake.engine.db.models.LossFraction
    :param str value:
       A value representing the fraction. In case of disaggregation by taxonomy
       it is a taxonomy string.
    :param point location: the location, the fraction refers to
    :param float absolute_loss:
       the absolute loss contribution of `value` in `location`
    """

    return models.LossFractionData.objects.create(
        loss_fraction_id=loss_fraction_id,
        value=value,
        location=location,
        absolute_loss=absolute_loss)


class count_progress_risk(stats.count_progress):   # pylint: disable=C0103
    """
    Extend :class:`openquake.engine.utils.stats.count_progress` to work with
    celery task where the number of items (i.e. assets) are embedded in hazard
    getters.
    """
    def get_task_data(self, job_id, hazard_data, *args):

        first_hazard_data = hazard_data.values()[0]

        getter, _weight = first_hazard_data
        return job_id, len(getter.assets)
