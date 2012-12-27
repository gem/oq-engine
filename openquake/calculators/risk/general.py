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

from openquake import logs
from openquake.utils import config
from openquake.db import models
from openquake.calculators import base
from openquake.parser import risk
from openquake.export import (
    core as export_core, risk as risk_export)
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

    :attribute asset_offsets:
      A generator of asset offsets used by each celery task. Assets are
      ordered by their id. An asset offset is an int that identify the
      set of assets going from offset to offset + block_size.
    """

    #: in subclasses, this would be a reference to the the celery task
    #  function used in the execute phase
    core_calc_task = lambda *args, **kwargs: None

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)
        self.assets_nr = None
        self.exposure_model_id = None

        self.progress = dict(total=0, computed=0)

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

            self.assets_nr = models.ExposureData.objects.contained_in_count(
                self.exposure_model_id,
                self.job.risk_calculation.region_constraint)

            if not self.assets_nr:
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])

        with logs.tracing('store risk model'):
            self.store_risk_model()

        self.progress.update(total=self.assets_nr)
        self._initialize_progress()

    def block_size(self):
        return int(config.get('risk', 'block_size'))

    def concurrent_tasks(self):
        return int(config.get('risk', 'concurrent_tasks'))

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

        with logs.tracing('storing exposure'):
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

        store_risk_model(self.job.risk_calculation, "vulnerability")


def hazard_getter(hazard_getter_name, hazard_id):
    """
    Initializes and returns an hazard getter
    """
    return hazard_getters.HAZARD_GETTERS[hazard_getter_name](hazard_id)


def fetch_vulnerability_model(job_id, retrofitted=False):
    """
    Utility method to use in a celery task to get a vulnerability
    model suitable to be used with Risklib.

    :param int job_id: The ID of the current job

    :param bool retrofitted: True if a retrofitted vulnerability model
    should be returned
    """

    if retrofitted:
        input_type = "vulnerability_retrofitted"
    else:
        input_type = "vulnerability"

    return models.OqJob.objects.get(pk=job_id).risk_calculation.model(
        input_type).to_risklib()


def write_loss_curve(loss_curve_id, asset_output):
    """
    Stores a :class:`openquake.db.models.LossCurveData` where the data are
    got by `asset_output` and the :class:`openquake.db.models.LossCurve`
    output container is identified by `loss_curve_id`.

    :param int loss_curve_id: the ID of the output container

    :param asset_output: an instance of
    :class:`risklib.models.output.ClassicalOutput` or of
    :class:`risklib.models.output.ProbabilisticEventBasedOutput`
    returned by risklib
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
    Create :class:`openquake.db.models.LossMapData` objects where the
    data are got by `asset_output` and the
    :class:`openquake.db.models.LossMap` output containers are got by
    `loss_map_ids`.

    :param dict loss_map_ids: A dictionary storing that links poe to
    :class:`openquake.db.models.LossMap` output container

    :param asset_output: an instance of
    :class:`risklib.models.output.ClassicalOutput` or of
    :class:`risklib.models.output.ProbabilisticEventBasedOutput`
    """

    for poe, loss in asset_output.conditional_losses.items():
        models.LossMapData.objects.create(
            loss_map_id=loss_map_ids[poe],
            asset_ref=asset_output.asset.asset_ref,
            value=loss,
            std_dev=None,
            location=asset_output.asset.site)


def write_bcr_distribution(bcr_distribution_id, asset_output):
    """
    Create a new :class:`openquake.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id: the ID of
    :class:`openquake.db.models.BCRDistribution` instance that holds
    the BCR map
    :param asset_output: an instance of
    :class:`risklib.models.output.BCROutput` that holds BCR data for a
    specific asset
    """
    models.BCRDistributionData.objects.create(
        bcr_distribution_id=bcr_distribution_id,
        asset_ref=asset_output.asset.asset_ref,
        average_annual_loss_original=asset_output.eal_original,
        average_annual_loss_retrofitted=asset_output.eal_retrofitted,
        bcr=asset_output.bcr,
        location=asset_output.asset.site)


def store_risk_model(rc, input_type):
    """
    Parse and store :class:`openquake.db.models.VulnerabilityModel` and
    :class:`openquake.db.models.VulnerabilityFunction`.

    :param str input_type: the input type of the
    :class:`openquake.db.models.Input` object which provides the risk models

    :param rc: the current :class:`openquake.db.models.RiskCalculation`
    instance
    """
    [vulnerability_input] = models.inputs4rcalc(
        rc.id, input_type=input_type)

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
