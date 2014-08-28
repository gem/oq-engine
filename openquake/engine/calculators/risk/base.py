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

"""
Base RiskCalculator class.
"""

import collections
import psutil

from openquake.nrmllib.risk import parsers
from openquake.risklib.workflows import RiskModel
from openquake.commonlib.riskloaders import get_taxonomy_vfs

from openquake.engine import logs, export
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import \
    writers, validation, hazard_getters
from openquake.engine.utils import config, tasks
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.input.exposure import ExposureDBWriter


BLOCK_SIZE = 100  # number of assets per block

MEMORY_ERROR = '''Running the calculation will require approximately
%dM, i.e. more than the memory which is available right now (%dM).
Please increase the free memory or apply a stringent region
constraint to reduce the number of assets. Alternatively you can set
epsilon_sampling in openquake.cfg. It the correlation is
nonzero, consider setting asset_correlation=0 to avoid building the
correlation matrix.'''


@tasks.oqtask
def build_getters(job_id, counts_taxonomy, calc):
    """
    :param job_id:
        ID of the current risk job
    :param counts_taxonomy:
        a sorted list of pairs (counts, taxonomy) for each bunch of assets
    :param calc:
        :class:`openquake.engine.calculators.risk.base.RiskCalculator` instance
    """
    all_getters = []
    for counts, taxonomy in counts_taxonomy:
        logs.LOG.info('taxonomy=%s, assets=%d', taxonomy, counts)

        # building the GetterBuilder
        with calc.monitor("associating asset->site"):
            builder = hazard_getters.GetterBuilder(
                taxonomy, calc.rc, calc.eps_sampling)

        # estimating the needed memory
        haz_outs = calc.rc.hazard_outputs()
        nbytes = builder.calc_nbytes(haz_outs)
        if nbytes:
            # TODO: the estimate should be revised by taking into account
            # the number of realizations
            estimate_mb = nbytes / 1024 / 1024 * 3
            phymem = psutil.phymem_usage()
            available_memory = (1 - phymem.percent / 100) * phymem.total
            available_mb = available_memory / 1024 / 1024
            if nbytes * 3 > available_memory:
                raise MemoryError(MEMORY_ERROR % (estimate_mb, available_mb))

        # initializing the epsilons
        builder.init_epsilons(haz_outs)

        # building the tasks
        task_no = 0
        name = calc.core_calc_task.__name__ + '[%s]' % taxonomy
        otm = tasks.OqTaskManager(calc.core_calc_task, logs.LOG.progress, name)

        for offset in range(0, counts, BLOCK_SIZE):
            with calc.monitor("getting asset chunks"):
                assets = models.ExposureData.objects.get_asset_chunk(
                    calc.rc, taxonomy, offset, BLOCK_SIZE)
            with calc.monitor("building getters"):
                try:
                    getters = builder.make_getters(
                        calc.getter_class, haz_outs, assets)
                except hazard_getters.AssetSiteAssociationError as err:
                    # TODO: add a test for this corner case
                    # https://bugs.launchpad.net/oq-engine/+bug/1317796
                    logs.LOG.warn('Taxonomy %s: %s', taxonomy, err)
                    continue

            # submitting task
            task_no += 1
            logs.LOG.info('Built task #%d for taxonomy %s', task_no, taxonomy)
            risk_model = calc.risk_models[taxonomy]
            otm.submit(job_id, risk_model, getters,
                       calc.outputdict, calc.calculator_parameters)

    return otm


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

    bcr = False  # flag overridden in BCR calculators

    def __init__(self, job):
        super(RiskCalculator, self).__init__(job)
        self.taxonomies_asset_count = None
        self.risk_models = None
        self.loss_types = set()
        self.acc = {}

    def agg_result(self, acc, res):
        """
        Aggregation method, to be overridden in subclasses
        """
        return acc

    def pre_execute(self):
        """
        In this phase, the general workflow is:
            1. Parse the exposure to get the taxonomies
            2. Parse the available risk models
            3. Validate exposure and risk models
        """
        with self.monitor('get exposure'):
            exposure = self.rc.exposure_model
            if exposure is None:
                ExposureDBWriter(self.job).serialize(
                    parsers.ExposureModelParser(self.rc.inputs['exposure']))
            self.taxonomies_asset_count = \
                self.rc.exposure_model.taxonomies_in(self.rc.region_constraint)

        with self.monitor('parse risk models'):
            self.risk_models = self.get_risk_models()
            for rm in self.risk_models.itervalues():
                self.loss_types.update(rm.loss_types)

            # consider only the taxonomies in the risk models if
            # taxonomies_from_model has been set to True in the
            # job.ini
            if self.rc.taxonomies_from_model:
                self.taxonomies_asset_count = dict(
                    (t, count)
                    for t, count in self.taxonomies_asset_count.items()
                    if t in self.risk_models)

        for validator_class in self.validators:
            validator = validator_class(self)
            error = validator.get_error()
            if error:
                raise ValueError("""Problems in calculator configuration:
                                 %s""" % error)

        num_assets = sum(self.taxonomies_asset_count.itervalues())
        num_taxonomies = len(self.taxonomies_asset_count)
        logs.LOG.info('Considering %d assets of %d distinct taxonomies',
                      num_assets, num_taxonomies)
        self.eps_sampling = int(config.get('risk', 'epsilon_sampling'))

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Method responsible for the distribution strategy.
        """
        self.outputdict = writers.combine_builders(
            [ob(self) for ob in self.output_builders])
        ct = sorted((counts, taxonomy) for taxonomy, counts
                    in self.taxonomies_asset_count.iteritems())
        self.acc = tasks.apply_reduce(
            build_getters, (self.job.id, ct, self),
            lambda acc, otm: otm.aggregate_results(self.agg_result, acc),
            self.acc, self.concurrent_tasks)

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

    def get_risk_models(self):
        # regular risk models
        if self.bcr is False:
            return dict(
                (taxonomy, RiskModel(taxonomy, self.get_workflow(vfs)))
                for taxonomy, vfs in get_taxonomy_vfs(
                    self.rc.inputs, models.LOSS_TYPES))

        # BCR risk models
        orig_data = get_taxonomy_vfs(
            self.rc.inputs, models.LOSS_TYPES, retrofitted=False)
        retro_data = get_taxonomy_vfs(
            self.rc.inputs, models.LOSS_TYPES, retrofitted=True)

        risk_models = {}
        for (taxonomy, vfs), (taxonomy_, vfs_) in zip(orig_data, retro_data):
            assert taxonomy_ == taxonomy_  # same taxonomy
            risk_models[taxonomy] = RiskModel(
                taxonomy, self.get_workflow(vfs, vfs_))
        return risk_models

    def get_workflow(self, vulnerability_functions):
        """
        To be overridden in subclasses. Must return a workflow instance.
        """
        class Workflow():
            vulnerability_functions = {}
        return Workflow()

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
