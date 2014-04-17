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
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import \
    writers, validation, loaders, hazard_getters
from openquake.engine.utils import tasks

@tasks.oqtask
def make_getter_builder(job_id, taxonomy):
    rc = models.OqJob.objects.get(pk=job_id).risk_calculation
    return hazard_getters.GetterBuilder(taxonomy, rc)
    

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
        self.loss_types = set()

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

        def update_dict(acc, builder):
            acc[builder.taxonomy] = builder
            logs.LOG.progress('Built builder for %s', builder.taxonomy)
            return acc
        self.getter_builders = tasks.map_reduce(
            make_getter_builder,
            [(self.job.id, taxo) for taxo in self.taxonomies_asset_count],
            update_dict, {})  # a dictionary {taxonomy: builder}

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

        # TODO: check that the block size dependency has been removed
        block_size = 100

        epsilon_nbytes = 0  # number of epsilons * number of bytes per float
        for taxonomy, assets_nr in self.taxonomies_asset_count.items():
            risk_model = self.risk_models[taxonomy]
            with self.monitor("associating asset->site"):
                builder = self.getter_builders[taxonomy]
                epsilon_nbytes += sum(
                    eps.nbytes for eps in builder.epsilons.itervalues())
            for offset in range(0, assets_nr, block_size):
                with self.monitor("getting asset chunks"):
                    assets = models.ExposureData.objects.get_asset_chunk(
                        self.rc, taxonomy, offset, block_size)
                with self.monitor("building getters"):
                    rm = risk_model.copy(
                        getters=builder.make_getters(
                            self.getter_class, 
                            self.rc.hazard_outputs(),
                            assets, risk_model.imt),
                        workflow=self.get_workflow(taxonomy))
                yield [
                    self.job.id,
                    rm,
                    sorted(self.loss_types),
                    outputdict,
                    self.calculator_parameters]
        if epsilon_nbytes:
            logs.LOG.info('Allocating %dM for the epsilons',
                          epsilon_nbytes / 1024 / 1024)

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
            A nested taxonomy -> instance of `RiskModel`.
        """
        risk_models = collections.defaultdict(dict)
        for v_input, loss_type in self.rc.vulnerability_inputs(retrofitted):
            self.loss_types.add(loss_type)
            for taxonomy, model in loaders.vulnerability(v_input):
                risk_models[taxonomy] = model.copy(taxonomy=taxonomy)

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
