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

import risklib

from django import db

from openquake import logs
from openquake.utils import config
from openquake.db import models
from openquake.calculators import base
from openquake import export
from openquake.utils import stats
from openquake.calculators.risk import hazard_getters
from nrml.risk import parsers

# FIXME: why is a writer in a package called "input" ?
from openquake.input import exposure as exposure_writer


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

        self.progress.update(total=sum(self.taxonomies.values()))
        self._initialize_progress()

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

        output_containers = self.create_outputs()
        calculator_parameters = self.calculator_parameters

        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = self.exposure_model.get_asset_chunk(
                        taxonomy,
                        self.rc.region_constraint, offset, block_size)

                tf_args = ([
                    self.job.id,
                    assets, self.hazard_getter, self.hazard_id] +
                    self.worker_args(taxonomy) +
                    output_containers + calculator_parameters)

                yield tf_args

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
        If requested by the user, automatically export all result artifacts to
        the specified format. (NOTE: The only export format supported at the
        moment is NRML XML.

        :returns:
            A list of the export filenames, including the absolute path to each
            file.
        """

        exported_files = []
        with logs.tracing('exports'):

            if 'exports' in kwargs and 'xml' in kwargs['exports']:
                exported_files = sum([
                    export.risk.export(output.id, self.rc.export_dir)
                    for output in export.core.get_outputs(self.job.id)], [])

                for exp_file in exported_files:
                    logs.LOG.debug('exported %s' % exp_file)
        return exported_files

    def hazard_id(self):
        """
        :returns: The ID of the output container of the hazard used
        for this risk calculation. E.g. an `openquake.db.models.HazardCurve'

        :raises: `RuntimeError` if the hazard associated with the
        current risk calculation is not suitable to be used with this
        calculator
        """

        # Calculator must override this to select from the hazard
        # output the proper hazard output container
        raise NotImplementedError

    @property
    def rc(self):
        """
        A shorter and more convenient way of accessing the
        :class:`~openquake.db.models.RiskCalculation`.
        """
        return self.job.risk_calculation

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
            writer = exposure_writer.ExposureDBWriter(exposure_model_input)
            writer.serialize(exposure_stream)
        return writer.model

    def _initialize_progress(self):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        stats.pk_set(self.job.id, "lvr", 0)
        stats.pk_set(self.job.id, "nrisk_total", sum(self.taxonomies.values()))
        stats.pk_set(self.job.id, "nrisk_done", 0)

    def set_risk_models(self):
        self.vulnerability_functions = self.parse_vulnerability_model()

    def parse_vulnerability_model(self, retrofitted=False):
        """
        Parse vulnerability model input associated with this
        calculation.

        As a side effect, it also stores the first IMT (that may be
        needed for further hazard filtering) in the attribute `imt`.

        :param bool retrofitted: true if the retrofitted model is
        going to be parsed

         :returns: a dictionary mapping each taxonomy to a
        `:class:risklib.scientific.VulnerabilityFunction` instance.
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
            vfs[record['ID']] = risklib.scientific.VulnerabilityFunction(
                record['IML'],
                record['lossRatio'],
                record['coefficientsVariation'],
                record['probabilisticDistribution'])
        return vfs

    def create_outputs(self):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves, LossMaps

        The default behavior is to create a loss curve and loss maps
        output.

        :return a list of int (id of containers) or dict (poe->int)
        """

        job = self.job

        # add loss curve containers
        loss_curve_id = models.LossCurve.objects.create(
            output=models.Output.objects.create_output(
                job, "Loss Curve set", "loss_curve")).pk

        loss_map_ids = dict()

        for poe in self.job.risk_calculation.conditional_loss_poes:
            loss_map_ids[poe] = models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    self.job,
                    "Loss Map Set with poe %s" % poe,
                    "loss_map"),
                poe=poe).pk
        return [loss_curve_id, loss_map_ids]


def hazard_getter(hazard_getter_name, hazard_id, *args):
    """
    Initializes and returns an hazard getter
    """
    return getattr(hazard_getters, hazard_getter_name)(hazard_id, *args)


def write_loss_curve(loss_curve_id, asset, asset_output):
    """
    Stores and returns a :class:`openquake.db.models.LossCurveData`
    where the data are got by `asset_output` and the
    :class:`openquake.db.models.LossCurve` output container is
    identified by `loss_curve_id`.

    :param int loss_curve_id: the ID of the output container
    :param asset: an instance of :class:`openquake.db.models.ExposureData`
    :param asset_output: an instance of
    :class:`risklib.models.output.ClassicalOutput` or of
    :class:`risklib.models.output.ProbabilisticEventBasedOutput`
    returned by risklib
    """
    return models.LossCurveData.objects.create(
        loss_curve_id=loss_curve_id,
        asset_ref=asset.asset_ref,
        location=asset.site,
        poes=asset_output.loss_curve.ordinates,
        losses=asset_output.loss_curve.abscissae,
        loss_ratios=asset_output.loss_ratio_curve.abscissae)


def write_loss_map(loss_map_ids, asset, asset_output):
    """
    Create :class:`openquake.db.models.LossMapData` objects where the
    data are got by `asset_output` and the
    :class:`openquake.db.models.LossMap` output containers are got by
    `loss_map_ids`.

    :param dict loss_map_ids: A dictionary storing that links poe to
    :class:`openquake.db.models.LossMap` output container

    :param asset: an instance of :class:`openquake.db.models.ExposureData`

    :param asset_output: an instance of
    :class:`risklib.models.output.ClassicalOutput` or of
    :class:`risklib.models.output.ProbabilisticEventBasedOutput`
    """

    for poe, loss in asset_output.conditional_losses.items():
        models.LossMapData.objects.create(
            loss_map_id=loss_map_ids[poe],
            asset_ref=asset.asset_ref,
            value=loss,
            std_dev=None,
            location=asset.site)


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


def write_bcr_distribution(bcr_distribution_id, asset, asset_output):
    """
    Create a new :class:`openquake.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id: the ID of
    :class:`openquake.db.models.BCRDistribution` instance that holds
    the BCR map

    :param asset: an instance of :class:`openquake.db.models.ExposureData`

    :param asset_output: an instance of
    :class:`risklib.models.output.BCROutput` that holds BCR data for a
    specific asset
    """
    models.BCRDistributionData.objects.create(
        bcr_distribution_id=bcr_distribution_id,
        asset_ref=asset.asset_ref,
        average_annual_loss_original=asset_output.eal_original,
        average_annual_loss_retrofitted=asset_output.eal_retrofitted,
        bcr=asset_output.bcr,
        location=asset.site)
