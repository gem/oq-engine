# -*- coding: utf-8 -*-

# Copyright (c) 2010-2014, GEM Foundation.
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

"""Base RiskCalculator class."""

import collections

from openquake.engine import logs, export
from openquake.engine.utils import config
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import writers, validation, loaders


class RiskCalculator(base.Calculator):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies_asset_count:
        A dictionary mapping each taxonomy with the number of assets the
        calculator will work on. Assets are extracted from the exposure input
        and filtered according to the `RiskCalculation.region_constraint`.

    :attribute dict risk_models:
        A nested dict taxonomy -> loss type -> instances of `RiskModel`.
    """

    # a list of :class:`openquake.engine.calculators.risk.validation` classes
    validators = [validation.HazardIMT, validation.EmptyExposure,
                  validation.OrphanTaxonomies, validation.ExposureLossTypes,
                  validation.NoRiskModels]

    def __init__(self, job):
        super(RiskCalculator, self).__init__(job)

        self.taxonomies_asset_count = None
        self.risk_models = None

    def pre_execute(self):
        """
        In this phase, the general workflow is:
            1. Parse the exposure to get the taxonomies
            2. Parse the available risk models
            3. Initialize progress counters
            4. Validate exposure and risk models
        """
        with self.monitor('get exposure'):
            self.taxonomies_asset_count = \
                (self.rc.preloaded_exposure_model or loaders.exposure(
                    self.job, self.rc.inputs['exposure'])
                 ).taxonomies_in(self.rc.region_constraint)

        with self.monitor('parse risk models'):
            self.risk_models = self.get_risk_models()

            # consider only the taxonomies in the risk models if
            # taxonomies_from_model has been set to True in the
            # job.ini
            if self.rc.taxonomies_from_model:
                self.taxonomies_asset_count = dict(
                    (t, count)
                    for t, count in self.taxonomies_asset_count.items()
                    if t in self.risk_models)

        n_assets = sum(self.taxonomies_asset_count.itervalues())
        logs.LOG.info('Considering %d assets of %d distinct taxonomies',
                      n_assets, len(self.taxonomies_asset_count))
        for taxonomy, counts in self.taxonomies_asset_count.iteritems():
            logs.LOG.info('taxonomy=%s, assets=%d', taxonomy, counts)

        for validator_class in self.validators:
            validator = validator_class(self)
            error = validator.get_error()
            if error:
                raise ValueError("""Problems in calculator configuration:
                                 %s""" % error)

    def task_arg_gen(self):
        """
        Generator function for creating the arguments for each task.

        It is responsible for the distribution strategy. It divides
        the considered exposure into chunks of homogeneous assets
        (i.e. having the same taxonomy). The chunk size is given by
        the `block_size` openquake config parameter.

        :returns:
            An iterator over a list of arguments. Each contains:

            1. the job id
            2. a getter object needed to get the hazard data
            3. the needed risklib calculators
            4. the outputdict to be populated
            5. the specific calculator parameter set
        """
        outputdict = writers.combine_builders(
            [builder(self) for builder in self.output_builders])

        # TODO: (MS) we will remove the block size dependency in the near
        # future; for the moment let's used a fixed size
        block_size = 100

        for taxonomy, assets_nr in self.taxonomies_asset_count.items():
            asset_offsets = range(0, assets_nr, block_size)
            for offset in asset_offsets:

                with self.monitor("getting asset chunks"):
                    assets = models.ExposureData.objects.get_asset_chunk(
                        self.rc, taxonomy, offset, block_size)
                for risk_model in self.risk_models[taxonomy].values():
                    self.init_risk_model(risk_model, assets)
                yield [
                    self.job.id,
                    self.risk_models[taxonomy].values(),
                    outputdict,
                    self.calculator_parameters]

    def _get_outputs_for_export(self):
        """
        Util function for getting :class:`openquake.engine.db.models.Output`
        objects to be exported.
        """
        return export.core.get_outputs(self.job.id)

    def _do_export(self, output_id, export_dir, export_type):
        """
        Risk-specific implementation of
        :meth:`openquake.engine.calculators.base.Calculator._do_export`.

        Calls the risk exporter.
        """
        return export.risk.export(output_id, export_dir, export_type)

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
        celery task function. A calculator must override this to
        provide custom arguments to its celery task
        """
        return []

    def get_risk_models(self, retrofitted=False):
        """
        Parse vulnerability models for each loss type in
        `openquake.engine.db.models.LOSS_TYPES`,
        then set the `risk_models` attribute.

        :param bool retrofitted:
            True if retrofitted models should be retrieved
        :returns:
            A nested dict taxonomy -> loss type -> instances of `RiskModel`.
        """
        risk_models = collections.defaultdict(dict)

        for v_input, loss_type in self.rc.vulnerability_inputs(retrofitted):
            for taxonomy, model in loaders.vulnerability(v_input):
                risk_models[taxonomy][loss_type] = model.copy(
                    loss_type=loss_type)

        return risk_models

#: Calculator parameters are used to compute derived outputs like loss
#: maps, disaggregation plots, quantile/mean curves. See
#: :class:`openquake.engine.db.models.RiskCalculation` for a description

CalcParams = collections.namedtuple(
    'CalcParams', [
        'conditional_loss_poes',
        'poes_disagg',
        'sites_disagg',
        'insured_losses',
        'quantiles',
        'asset_life_expectancy',
        'interest_rate',
        'mag_bin_width',
        'distance_bin_width',
        'coordinate_bin_width',
        'damage_state_ids'
    ])


def make_calc_params(conditional_loss_poes=None,
                     poes_disagg=None,
                     sites_disagg=None,
                     insured_losses=None,
                     quantiles=None,
                     asset_life_expectancy=None,
                     interest_rate=None,
                     mag_bin_width=None,
                     distance_bin_width=None,
                     coordinate_bin_width=None,
                     damage_state_ids=None):
    """
    Constructor of CalculatorParameters
    """
    return CalcParams(conditional_loss_poes,
                      poes_disagg,
                      sites_disagg,
                      insured_losses,
                      quantiles,
                      asset_life_expectancy,
                      interest_rate,
                      mag_bin_width,
                      distance_bin_width,
                      coordinate_bin_width,
                      damage_state_ids)
