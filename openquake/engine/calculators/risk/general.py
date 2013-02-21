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

import os
import random


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
from openquake.engine.input import exposure as exposure_writer


#: Maximum number of loss curves to cache in buffers, for selects and inserts
_CURVE_CACHE_SIZE = 100000


class BaseRiskCalculator(base.CalculatorNext):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies:
      A dictionary mapping each taxonomy with the number of assets the
      calculator will work on. Assets are extracted from the exposure
      input and filtered according with the RiskCalculation
      region_constraint

    :attribute exposure_model:
      The exposure model used by the calculation

    :attribute asset_offsets:
      A generator of asset offsets used by each celery task. Assets are
      ordered by their id. An asset offset is an int that identify the
      set of assets going from offset to offset + block_size.

    :attribute dict vulnerability_functions:
       A dict mapping taxonomy to vulnerability functions used for
       this calculation

    :attribute rnd:
      The random number generator (initialized with a master seed) used
      for sampling

    :attribute str imt:
      The intensity measure type considered
    """

    hazard_getter = None  # the name of the hazard getter class; to override

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)

        self.taxonomies = None
        self.exposure_model = None
        self.rnd = None
        self.vulnerability_functions = None
        self.imt = None

    def pre_execute(self):
        """
        In this phase, the general workflow is

        1. Parse the exposure input and store the exposure data (if
        not already present)

        2. Check if the exposure filtered with region_constraint is
        not empty

        3. Parse the risk models

        4. Initialize progress counters

        5. Initialize random number generator
        """

        # reload the risk calculation to avoid getting raw string
        # values instead of arrays
        self.job.risk_calculation = models.RiskCalculation.objects.get(
            pk=self.rc.pk)

        with logs.tracing('store exposure'):
            self.exposure_model = self._store_exposure()

            self.taxonomies = self.exposure_model.taxonomies_in(
                self.rc.region_constraint)

            if not sum(self.taxonomies.values()):
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])

        with logs.tracing('store risk model'):
            self.set_risk_models()

        imts = self.hc.get_imts()

        if not self.imt in imts:
            raise RuntimeError(
                "There is no hazard output for the intensity measure %s; "
                "the available IMTs are %s" % (self.imt, imts))

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

        :returns: an iterator over a list of arguments. Each contains
        1) the job id
        2) the exposure subset on which the celery task is applied on
        3) the hazard getter and the hazard_id to be used
        4) a seed (eventually generated from a master seed)
        5) the output containers to be populated
        6) the specific calculator parameter set
        """

        output_containers = self.rc.output_container_builder(self)

        calculator_parameters = self.calculator_parameters

        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = self.exposure_model.get_asset_chunk(
                        taxonomy,
                        self.rc.region_constraint, offset, block_size)

                hazard = dict((ho.id, self.create_getter(ho, assets))
                              for ho in self.considered_hazard_outputs())
                worker_args = self.worker_args(taxonomy)

                logs.LOG.debug("Task with %s assets (%s, %s) got args %s",
                               len(assets), offset, block_size, worker_args)

                yield ([self.job.id, hazard] +
                       worker_args +
                       [output_containers] +
                       calculator_parameters)

    def worker_args(self, taxonomy):
        """
        :returns: a fixed list of arguments that a calculator may want
        to pass to a worker. Default to a seed generated from the
        master seed and the vulnerability function associated with the
        assets taxonomy. May be overriden.
        """
        return [self.rnd.randint(0, (2 ** 31) - 1),
                self.vulnerability_functions[taxonomy]]

    def export(self, *args, **kwargs):
        """
        If requested by the user, automatically export all result artifacts.

        :returns: A list of the export filenames, including the
            absolute path to each file.
        """

        exported_files = []
        with logs.tracing('exports'):
            if 'exports' in kwargs:
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
        :returns: a list of :class:`openquake.engine.db.models.Output`
        objects to be used for a risk calculation.

        Calculator must override this to select from the hazard
        calculation given in input which are the Output objects to be
        considered by the risk calculation to get the actual hazard
        input.

        Result objects should be ordered (e.g. by id) and be
        associated to an hazard logic tree realization
        """
        # FIXME(lp). It should accept an imt as a second parameter
        # instead of getting it from self.imt
        raise NotImplementedError

    def create_getter(self, output, assets):
        """
        Create an instance of :class:`.hazard_getters.HazardGetter`
        associated to a weight of an hazard logic tree realization.

        :returns: a tuple where the first element is the hazard getter
        and the second is the associated weight.

        Calculator must override this to create the proper hazard getter.

        :param hazard_output: the ID of an
        :class:`openquake.engine.db.models.Output` produced by an
        hazard calculation

        :raises: `RuntimeError` if the hazard associated with the
        `hazard_output` is not suitable to be used with this
        calculator
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

    def _store_exposure(self):
        """Load exposure assets and write them to database."""
        [exposure_model_input] = models.inputs4rcalc(
            self.rc, input_type='exposure')

        # If this was an existing model, it was already parsed and should be in
        # the DB.
        if not self.rc.force_inputs and models.ExposureModel.objects.filter(
                input=exposure_model_input).exists():
            return exposure_model_input.exposuremodel

        with logs.tracing('storing exposure'):
            path = os.path.join(self.rc.base_path, exposure_model_input.path)
            exposure_stream = parsers.ExposureModelParser(path)
            w = exposure_writer.ExposureDBWriter(exposure_model_input)
            w.serialize(exposure_stream)
        return w.model

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
        self.vulnerability_functions = self.parse_vulnerability_model()
        self.check_taxonomies(self.vulnerability_functions)

    def check_taxonomies(self, taxonomies):
        """
        :param taxonomies:
           taxonomies coming from the fragility/vulnerability model

        If the model has less taxonomies than the exposure raises an
        error unless the parameter ``taxonomies_from_model`` is set.
        """
        orphans = set(self.taxonomies) - set(taxonomies)
        if orphans:
            msg = ('The following taxonomies are in the exposure model '
                   'but not in the fragility model: %s' % sorted(orphans))
            if self.rc.taxonomies_from_model:
                # only consider the taxonomies in the fragility model
                self.taxonomies = dict((t, self.taxonomies[t])
                                       for t in self.fragility_functions
                                       if t in self.taxonomies)
                logs.LOG.warn(msg)
            else:
                # all taxonomies in the exposure must be covered
                raise RuntimeError(msg)

    def parse_vulnerability_model(self, retrofitted=False):
        """
        Parse vulnerability model input associated with this
        calculation.

        As a side effect, it also stores the first IMT (that may be
        needed for further hazard filtering) in the attribute `imt`.

        :param bool retrofitted: true if the retrofitted model is
        going to be parsed

         :returns: a dictionary mapping each taxonomy to a
        `:class:openquake.risklib.scientific.VulnerabilityFunction` instance.
        """

        if retrofitted:
            input_type = "vulnerability_retrofitted"
        else:
            input_type = "vulnerability"

        path = self.rc.inputs.get(input_type=input_type).path

        vfs = dict()

        # CAVEATS
        # 1) We use the first imt returned by the parser 2) Use the
        # last vf for a taxonomy returned by the parser (if multiple
        # vf for the same taxonomy are given).

        # We basically assume that the user will provide a
        # vulnerability model where for each taxonomy there is only
        # one vf for a taxonomy and an imt matching the ones in the
        # hazard output
        for record in parsers.VulnerabilityModelParser(path):
            if self.imt is None:
                self.imt = record['IMT']
            vfs[record['ID']] = scientific.VulnerabilityFunction(
                record['IML'],
                record['lossRatio'],
                record['coefficientsVariation'],
                record['probabilisticDistribution'])
        return vfs

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves, LossMaps

        The default behavior is to create a loss curve and loss maps
        output.

        :returns: a dictionary mapping an Output object ID to a list
        of int (id of containers) or dict (poe->int)
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

        # mean loss curves ...
        multiple_hazard_outputs_p = len(self.considered_hazard_outputs()) > 1
        if self.rc.mean_loss_curves and multiple_hazard_outputs_p:
            mean_loss_curve_id = models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job=self.job,
                    display_name='loss-curves',
                    output_type='loss_curve'),
                statistics='mean').id
        else:
            mean_loss_curve_id = None

        # quantile loss curves
        quantile_loss_curve_ids = {}
        if multiple_hazard_outputs_p and self.rc.quantile_loss_curves:
            for quantile in self.rc.quantile_loss_curves:
                quantile_loss_curve_ids[quantile] = (
                    models.LossCurve.objects.create(
                        output=models.Output.objects.create_output(
                            job=self.job,
                            display_name='quantile(%s)-curves' % quantile,
                            output_type='loss_curve'),
                        statistics='quantile',
                        quantile=quantile).id)

        return [loss_curve_id, loss_map_ids,
                mean_loss_curve_id, quantile_loss_curve_ids]


def hazard_getter(hazard_getter_name, hazard_id, *args):
    """
    Initializes and returns an hazard getter
    """
    return getattr(hazard_getters, hazard_getter_name)(hazard_id, *args)


def write_loss_curve(loss_curve_id, asset, loss_ratio_curve):
    """
    Stores and returns a :class:`openquake.engine.db.models.LossCurveData`
    where the data are got by `asset_output` and the
    :class:`openquake.engine.db.models.LossCurve` output container is
    identified by `loss_curve_id`.

    :param int loss_curve_id: the ID of the output container
    :param asset: an instance of
           :class:`openquake.engine.db.models.ExposureData`
    :param loss_ratio_curve: an instance of
           :class:`openquake.risklib.curve.Curve`
    """

    return models.LossCurveData.objects.create(
        loss_curve_id=loss_curve_id,
        asset_ref=asset.asset_ref,
        location=asset.site,
        poes=loss_ratio_curve.ordinates,
        loss_ratios=loss_ratio_curve.abscissae,
        asset_value=asset.value)


@db.transaction.commit_on_success
def update_aggregate_losses(curve_id, losses):
    """
    Update an aggregate loss curve with new `losses` (that will be
    added)

    :type losses: numpy array
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

    :param int loss_map_id: the ID of the output container
    :param asset: an instance of
           :class:`openquake.engine.db.models.ExposureData`
    :param float value: loss ratio value
    :param float std_dev: std dev on loss ratios.
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

    :param int bcr_distribution_id: the ID of
    :class:`openquake.engine.db.models.BCRDistribution` instance that holds
    the BCR map

    :param asset: an instance of
        :class:`openquake.engine.db.models.ExposureData`

    :param float eal_original: expected annual loss in the original model
    for the asset
    :param float eal_retrofitted: expected annual loss in the retrofitted model
    for the asset
    :param float bcr: Benefit Cost Ratio parameter
    """
    models.BCRDistributionData.objects.create(
        bcr_distribution_id=bcr_distribution_id,
        asset_ref=asset.asset_ref,
        average_annual_loss_original=eal_original * asset.value,
        average_annual_loss_retrofitted=eal_retrofitted * asset.value,
        bcr=bcr,
        location=asset.site)


def curve_statistics(asset, loss_ratio_curves, curves_weights,
                     mean_loss_curve_id, quantile_loss_curve_ids,
                     explicit_quantiles, assume_equal):

    if assume_equal == 'support':
        loss_ratios = loss_ratio_curves[0].abscissae
        curves_poes = [curve.ordinates for curve in loss_ratio_curves]
    elif assume_equal == 'image':
        loss_ratios = loss_ratio_curves[0].abscissae
        curves_poes = [curve.ordinate_for(loss_ratios)
                       for curve in loss_ratio_curves]
    else:
        raise NotImplementedError

    for quantile, quantile_loss_curve_id in quantile_loss_curve_ids.items():
        if explicit_quantiles:
            q_curve = post_processing.weighted_quantile_curve(
                curves_poes, curves_weights, quantile)
        else:
            q_curve = post_processing.quantile_curve(
                curves_poes, quantile)

        models.LossCurveData.objects.create(
            loss_curve_id=quantile_loss_curve_id,
            asset_ref=asset.asset_ref,
            poes=q_curve.tolist(),
            loss_ratios=loss_ratios,
            asset_value=asset.value,
            location=asset.site.wkt)

    # then means
    if mean_loss_curve_id:
        mean_curve = post_processing.mean_curve(
            curves_poes, weights=curves_weights)

        models.LossCurveData.objects.create(
            loss_curve_id=mean_loss_curve_id,
            asset_ref=asset.asset_ref,
            poes=mean_curve.tolist(),
            loss_ratios=loss_ratios,
            asset_value=asset.value,
            location=asset.site.wkt)
