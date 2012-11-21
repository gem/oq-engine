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

import os
import math
import functools

from openquake import logs
from openquake.utils import config
from openquake.db import models
from openquake.calculators import base
from openquake.parser import risk
from openquake.export import (
    core as export_core, risk as risk_export)
from openquake.utils import tasks
from openquake.utils import stats
from openquake.calculators.risk import hazard_getters

# FIXME: why is a writer in a package called "input" ?
from openquake.input import exposure as exposure_writer


class BaseRiskCalculator(base.CalculatorNext):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute asset_nr:
      The number of assets the calculator will work on. Assets are
      extracted from the exposure input and filtered according with the
      RiskCalculation region_constraint

    :attribute output_container_ids:
      A dictionary holding the output containers object ids (e.g. LossCurve,
      LossMap)

    :attribute exposure_model_id:
      The exposure model used by the calculation

    :attribute assets_per_task:
      The number of assets processed by each celery task

    :attribute asset_offsets:
      A generator of asset offsets used by each celery task. Assets are
      ordered by their id. An asset offset is an int that identify the
      set of assets going from offset to offset + assets_per_task.
    """

    #: in subclasses, this would be a reference to the the celery task
    #  function used in the execute phase
    celery_task = lambda *args, **kwargs: None

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)
        self.output_container_ids = None
        self.assets_nr = None
        self.exposure_model_id = None
        self.assets_per_task = None
        self.asset_offsets = None

    def pre_execute(self):
        """
        In this phase, the general workflow is

        1. Parse the exposure input and store the exposure data (if
        not already present)

        2. Filter the exposure in order to consider only the assets of
        interest

        3. Prepare and save the output containers.

        4. Initialize progress counters
        """
        with logs.tracing('store exposure'):
            self.exposure_model_id = self._store_exposure().id

            self.assets_nr = models.ExposureData.objects.contained_in(
                self.exposure_model_id,
                self.job.risk_calculation.region_constraint).count()

            if not self.assets_nr:
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])
            self.assets_per_task = int(
                math.ceil(float(self.assets_nr) / int(
                    config.get('risk', 'task_number'))))

            self.asset_offsets = range(0, self.assets_nr, self.assets_per_task)

        with logs.tracing('store risk model'):
            self.store_risk_model()

        with logs.tracing('create output containers'):
            self.output_container_ids = self.create_outputs()

        self._initialize_progress()

    def execute(self):
        """
        Calculation work is parallelized over block of assets, which
        means that each task will compute risk for only a subset of
        the exposure considered.

        The asset block size value is got by the variable `block_size`
        in `[risk]` section of the OpenQuake config file.
        """

        tf_args = dict(
            job_id=self.job.id,
            hazard_getter="one_query_per_asset",
            assets_per_task=self.assets_per_task,
            region_constraint=self.job.risk_calculation.region_constraint,
            exposure_model_id=self.exposure_model_id,
            hazard_id=self.hazard_id)
        tf_args.update(self.output_container_ids)
        tf_args.update(self.calculation_parameters)

        tasks.distribute(
            self.celery_task,
            ("offset", self.asset_offsets),
            tf_args=tf_args)

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
                    risk_export.export(output.id,
                                       self.job.risk_calculation.export_dir)
                    for output in export_core.get_outputs(self.job.id)], [])

                for exp_file in exported_files:
                    logs.LOG.debug('exported %s' % exp_file)
        return exported_files

    def _store_exposure(self):
        """Load exposure assets and write them to database."""
        rc = self.job.risk_calculation
        [exposure_model_input] = models.inputs4rcalc(
            self.job.risk_calculation, input_type='exposure')

        # If this was an existing model, it was already parsed and should be in
        # the DB.
        if models.ExposureModel.objects.filter(
                input=exposure_model_input).exists():
            return exposure_model_input.exposuremodel

        path = os.path.join(rc.base_path, exposure_model_input.path)
        exposure_stream = risk.ExposureModelFile(path)
        writer = exposure_writer.ExposureDBWriter(exposure_model_input)
        writer.serialize(exposure_stream)
        return writer.model

    def _initialize_progress(self):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        stats.pk_set(self.job.id, "lvr", 0)
        stats.pk_set(self.job.id, "nrisk_total", self.assets_nr)
        stats.pk_set(self.job.id, "nrisk_done", 0)

    def store_risk_model(self):
        """Load and store vulnerability model. It could be overriden
        to load fragility models or multiple vulnerability models"""

        rc = self.job.risk_calculation

        [vulnerability_input] = models.inputs4rcalc(rc.id,
                                                    input_type='vulnerability')

        for record in risk.VulnerabilityModelFile(
                vulnerability_input.path):
            vulnerability_model, _ = (
                models.VulnerabilityModel.objects.get_or_create(
                    owner=vulnerability_input.owner,
                    input=vulnerability_input,
                    imt=record['IMT'].lower(), imls=record['IML'],
                    name=record['vulnerabilitySetID'],
                    asset_category=record['assetCategory'],
                    loss_category=record['lossCategory']))

            models.VulnerabilityFunction.objects.create(
                vulnerability_model=vulnerability_model,
                taxonomy=record['ID'],
                prob_distribution=record['probabilisticDistribution'],
                covs=record['coefficientsVariation'],
                loss_ratios=record['lossRatio'])

    def create_outputs(self):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves.

        The default behavior is to create a loss curve output.

        :return a dictionary string -> ContainerObject ids
        """

        job = self.job

        return dict(
            loss_curve_id=models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job, "Loss Curve set", "loss_curve")).pk)


def with_assets(fn):
    """
    Decorator helper for a risk calculation celery task.

    It transforms an oqtask function accepting an offset as first
    argument and a block size over a list of assets into a function
    that accepts a list of assets contained in a region_constraint.

    The exposure_model, the region constraint and the assets_per_task
    are got by kwargs of the original function. Such arguments are
    removed from the function signature.

    It is also responsible to log the progress
    """
    @functools.wraps(fn)
    def wrapped_function(job_id, offset, **kwargs):
        """
        The wrapped celery task function that expects in input an
        offset over the collection of all the Asset considered
        by the risk calculation.
        """
        exposure_model_id = kwargs['exposure_model_id']
        region_constraint = kwargs['region_constraint']
        assets_per_task = kwargs['assets_per_task']

        del kwargs['exposure_model_id']
        del kwargs['region_constraint']
        del kwargs['assets_per_task']

        assets = models.ExposureData.objects.contained_in(
            exposure_model_id,
            region_constraint)[offset:offset + assets_per_task]

        fn(job_id, assets, **kwargs)
        logs.log_percent_complete(job_id, "risk")

    return wrapped_function


def hazard_getter(hazard_getter_name, hazard_id):
    """
    Initializes and returns an hazard getter
    """
    return hazard_getters.HAZARD_GETTERS[hazard_getter_name](hazard_id)


def fetch_vulnerability_model(job_id):
    """
    Returns the vulnerability model associated with the current
    running job
    """
    job = models.OqJob.objects.get(pk=job_id)
    return job.risk_calculation.model("vulnerability").to_risklib()


def write_loss_curve(loss_curve_id, asset_output):
    """
    Stores a `openquake.db.models.LossCurveData` where the data are
    got by `asset_output` and the `openquake.db.models.LossCurve`
    output container is identified by `loss_curve_id`.
    """
    models.LossCurveData.objects.create(
        loss_curve_id=loss_curve_id,
        asset_ref=asset_output.asset.asset_ref,
        location=asset_output.asset.site,
        poes=asset_output.loss_curve.y_values,
        losses=asset_output.loss_curve.x_values,
        loss_ratios=asset_output.loss_ratio_curve.x_values)


def write_loss_map(loss_map_ids, asset_output):
    """
    Stores `openquake.db.models.LossMapData` objects where the data
    are got by `asset_output` and the `openquake.db.models.LossMap`
    output containers are got by `loss_map_ids`.
    """

    for poe, loss in asset_output.conditional_losses.items():
        models.LossMapData.objects.create(
            loss_map_id=loss_map_ids[poe],
            asset_ref=asset_output.asset.asset_ref,
            value=loss,
            std_dev=None,
            location=asset_output.asset.site)
