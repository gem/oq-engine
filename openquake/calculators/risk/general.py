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
import StringIO

from openquake.db import models
from openquake.calculators import base
from openquake.parser import exposure as exposure_parser
from openquake.parser import vulnerability as vulnerability_parser
from openquake.utils import general, tasks


# FIXME: why is a writer in package called "input" ?
from openquake.input import exposure as exposure_writer


# number of assets processed by a celery task
ASSET_BLOCK_SIZE = 1000


class BaseRiskCalculator(base.CalculatorNext):
    """
    A temporary "dummy" calculator that doesn't do anything. This is currently
    only used to be able to exercise the risk engine end-to-end.

    This will eventually updated or replaced when we start to implement the new
    set of risk calculators based oq-risklib.

    :attr asset_ids
      An array of asset_ids
    """

    # the celery task used in the execute phase
    celery_task = None

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)
        self.asset_ids = []

    def pre_execute(self):
        self._store_exposure()
        self._store_risk_model()
        self.asset_ids = self._filter_exposure()

    def execute(self):
        asset_chunks = list(general.block_splitter(
            self.asset_ids, ASSET_BLOCK_SIZE))

        tasks.distribute(
            self.celery_task,
            ("asset_ids", asset_chunks),
            tf_args=dict(job_id=self.job.id,
                         hazard_getter="one_query_per_asset"))

    def _store_exposure(self):
        """Load exposure assets and write them to database."""
        rc = self.job.risk_calculation
        [exposure_model_input] = models.inputs4rcalc(
            self.job.risk_calculation, input_type='exposure')

        # If this was an existing model, it was already parsed and should be in
        # the DB.
        if exposure_model_input.exposuremodel_set.count():
            return

        path = os.path.join(rc.base_path, exposure_model_input.path)
        exposure_stream = exposure_parser.ExposureModelFile(path)
        writer = exposure_writer.ExposureDBWriter(exposure_model_input)
        writer.serialize(exposure_stream)

    def _filter_exposure(self):
        region_constraint = self.job.risk_calculation.region_constraint
        return models.ExposureData.objects.filter(
            site__contained=region_constraint).values_list('id', flat=True)

    def _store_risk_model(self):
        """ load vulnerability and write to db"""

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
