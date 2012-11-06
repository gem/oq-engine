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
from openquake.parser import (
    exposure as exposure_parser, vulnerability as vulnerability_parser)
from openquake.export import (
    core as export_core, risk as risk_export)
from openquake.utils import general, tasks


# FIXME: why is a writer in package called "input" ?
from openquake.input import exposure as exposure_writer


# default number of assets processed by a celery task
ASSET_BLOCK_SIZE = 1000


class BaseRiskCalculator(base.CalculatorNext):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute asset_ids
      The array of asset_ids the calculator will work on. They are
      extracted from the exposure input and filtered according with the
      RiskCalculation region_constraint

    :attribute output_container_ids
      A dictionary holding the output containers object ids (e.g. LossCurve,
      LossMap)
    """

    #: in subclasses, this would be a reference to the the celery task
    #  function used in the execute phase
    celery_task = None

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)
        self.asset_ids = []
        self.output_container_ids = None

    def pre_execute(self):
        """
        In this phase, the general workflow is

        1. Parse the exposure input and store the exposure data (if
        not already present)

        2. Filter the exposure in order to consider only the assets of
        interest

        3. Prepare and save the output containers.
        """
        with logs.tracing('store exposure'):
            exposure_model = self._store_exposure()

        with logs.tracing('filter exposure'):
            self.asset_ids = models.ExposureData.objects.contained_in(
                exposure_model, self.job.risk_calculation.region_constraint)

            if not self.asset_ids:
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])

        with logs.tracing('store risk model'):
            self.store_risk_model()

        with logs.tracing('create output containers'):
            self.output_container_ids = self.create_outputs()

    def execute(self):
        """
        Calculation work is parallelized over block of assets, which
        means that each task will compute risk for only a subset of
        the exposure considered.

        The asset block size value is got by the variable `block_size`
        in `[risk]` section of the OpenQuake config file.
        """

        asset_block_size = int(
            config.get('risk', 'block_size') or ASSET_BLOCK_SIZE)

        asset_chunks = list(general.block_splitter(
            self.asset_ids, asset_block_size))

        tf_args = dict(job_id=self.job.id,
                     hazard_getter="one_query_per_asset")
        tf_args.update(self.output_container_ids)

        tasks.distribute(
            self.celery_task,
            ("asset_ids", asset_chunks),
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
                outputs = export_core.get_outputs(self.job.id)

                for output in outputs:
                    exported_files.extend(risk_export.export(
                        output.id, self.job.risk_calculation.export_dir))

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
        queryset = exposure_model_input.exposuremodel_set
        if queryset.exists():
            assert queryset.count() == 1
            return queryset.all()[0]

        path = os.path.join(rc.base_path, exposure_model_input.path)
        exposure_stream = exposure_parser.ExposureModelFile(path)
        writer = exposure_writer.ExposureDBWriter(exposure_model_input)
        writer.serialize(exposure_stream)
        return writer.model

    def store_risk_model(self):
        """Load and store vulnerability model. It could be overriden
        to load fragility models or multiple vulnerability models"""

        rc = self.job.risk_calculation

        [vulnerability_input] = models.inputs4rcalc(rc.id,
                                                    input_type='vulnerability')

        for record in vulnerability_parser.VulnerabilityModelFile(
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

        :return a dictionary string -> ContainerObject ids
        """

        return dict(
            loss_curve=models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "Loss Curve set", "loss_curve")).pk)
