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

from openquake.engine import logs, export
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import \
    writers, validation, loaders, hazard_getters
from openquake.engine.utils import config, tasks
from openquake.risklib.workflows import RiskModel
from openquake.engine.performance import EnginePerformanceMonitor

BLOCK_SIZE = 100  # number of assets per block

MEMORY_ERROR = '''Running the calculation will require approximately
%dM, i.e. more than the memory which is available right now (%dM).
Please increase the free memory or apply a stringent region
constraint to reduce the number of assets. Alternatively you can set
epsilons_management=fast in openquake.cfg. It the correlation is
nonzero, consider setting asset_correlation=0 to avoid building the
correlation matrix.'''


@tasks.oqtask
def run_subtasks(job_id, calc, taxonomy, counts, outputdict):
    """
    Spawn risk tasks and return an OqTaskManager instance
    """
    logs.LOG.info('taxonomy=%s, assets=%d', taxonomy, counts)
    with calc.monitor("associating asset->site"):
        builder = hazard_getters.GetterBuilder(
            taxonomy, calc.rc, calc.eps_man)
    haz_outs = calc.rc.hazard_outputs()
    nbytes = builder.calc_nbytes(haz_outs)
    if nbytes:
        estimate_mb = nbytes / 1024 / 1024 * 3
        if calc.eps_man == 'fast' and calc.rc.asset_correlation == 0:
            pass  # using much less memory than the estimate, don't log
        else:
            logs.LOG.info('epsilons_management=%s: '
                          'you should need less than %dM (rough estimate)',
                          calc.eps_man, estimate_mb)
        phymem = psutil.phymem_usage()
        available_memory = (1 - phymem.percent / 100) * phymem.total
        available_mb = available_memory / 1024 / 1024
        if calc.eps_man == 'full' and nbytes * 3 > available_memory:
            raise MemoryError(MEMORY_ERROR % (estimate_mb, available_mb))

    task_no = 0
    name = calc.core_calc_task.__name__ + '[%s]' % taxonomy
    otm = tasks.OqTaskManager(calc.core_calc_task, logs.LOG.progress, name)
    with calc.monitor("building epsilons"):
        builder.init_epsilons(haz_outs)
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
        rm = calc.risk_models[taxonomy].copy(getters=getters)
        otm.submit(calc.job.id, rm, outputdict, calc.calculator_parameters)

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
            self.taxonomies_asset_count = (
                self.rc.preloaded_exposure_model or loaders.exposure(
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

        for validator_class in self.validators:
            validator = validator_class(self)
            error = validator.get_error()
            if error:
                raise ValueError("""Problems in calculator configuration:
                                 %s""" % error)

        self.eps_man = config.get('risk', 'epsilons_management')

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Method responsible for the distribution strategy. It divides
        the considered exposure into chunks of homogeneous assets
        (i.e. having the same taxonomy).
        """
        outputdict = writers.combine_builders(
            [ob(self) for ob in self.output_builders])

        arglist = [
            (self.job.id, self, taxonomy, counts, outputdict)
            for taxonomy, counts in self.taxonomies_asset_count.iteritems()]

        def agg(acc, otm):
            return otm.aggregate_results(self.agg_result, acc)
        name = run_subtasks.__name__ + '[%s]' % self.core_calc_task.__name__
        self.acc = tasks.map_reduce(run_subtasks, arglist, agg, self.acc, name)

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
                for taxonomy, vfs in self._get_vfs())

        # BCR risk models
        risk_models = {}
        orig_data = self._get_vfs(retrofitted=False)
        retro_data = self._get_vfs(retrofitted=True)

        for orig, retro in zip(orig_data, retro_data):
            taxonomy, vfs = orig
            taxonomy_, vfs_ = retro
            assert taxonomy_ == taxonomy_  # same taxonomy
            risk_models[taxonomy] = RiskModel(
                taxonomy, self.get_workflow(vfs, vfs_))

        return risk_models

    def _get_vfs(self, retrofitted=False):
        """
        Parse vulnerability models for each loss type in
        `openquake.engine.db.models.LOSS_TYPES`,
        then set the `risk_models` attribute.

        :param bool retrofitted:
            True if retrofitted models should be retrieved
        :returns:
            A dictionary taxonomy -> instance of `RiskModel`.
        """
        data = collections.defaultdict(list)  # imt, loss_type, vf per taxonomy
        for v_input, loss_type in self.rc.vulnerability_inputs(retrofitted):
            self.loss_types.add(loss_type)
            for taxonomy, vf in loaders.vulnerability(v_input).items():
                data[taxonomy].append((loss_type, vf))
        for taxonomy in data:
            yield taxonomy, dict(data[taxonomy])

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
