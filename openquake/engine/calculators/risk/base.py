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

import itertools
import numpy

from openquake.commonlib import risk_parsers
from openquake.hazardlib.imt import from_string
from openquake.commonlib.readinput import get_risk_model
from openquake.commonlib.parallel import virtual_memory

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine.calculators.risk import \
    writers, validation, hazard_getters
from openquake.engine.utils import config, tasks
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.input.exposure import ExposureDBWriter

MEMORY_ERROR = '''Running the calculation will require approximately
%dM, i.e. more than the memory which is available right now (%dM).
Please increase the free memory or apply a stringent region
constraint to reduce the number of assets. Alternatively you can set
epsilon_sampling in openquake.cfg. It the correlation is
nonzero, consider setting asset_correlation=0 to avoid building the
correlation matrix.'''

eps_sampling = int(config.get('risk', 'epsilon_sampling'))


@tasks.oqtask
def prepare_risk(counts_taxonomy, calc, monitor):
    """
    Associates the assets to the closest hazard sites and populate
    the table asset_site. For some calculators also initializes the
    epsilon matrices and save them on the database.

    :param counts_taxonomy:
        a sorted list of pairs (counts, taxonomy) for each bunch of assets
    :param calc:
        the current risk calculator
    :param monitor:
        monitor of the current risk job
    """
    assoc_mon = monitor("associating asset->site", autoflush=True)
    init_mon = monitor("initializing epsilons", autoflush=True)

    for counts, taxonomy in counts_taxonomy:

        # building the RiskInitializers
        with assoc_mon:
            initializer = hazard_getters.RiskInitializer(taxonomy, calc)
            initializer.init_assocs()

        # estimating the needed memory
        nbytes = initializer.calc_nbytes(eps_sampling)
        if nbytes:
            # TODO: the estimate should be revised by taking into account
            # the number of realizations
            estimate_mb = nbytes / 1024 / 1024 * 3
            phymem = virtual_memory()
            available_memory = (1 - phymem.percent / 100) * phymem.total
            available_mb = available_memory / 1024 / 1024
            if nbytes * 3 > available_memory:
                raise MemoryError(
                    MEMORY_ERROR % (estimate_mb, available_mb))

        # initializing epsilons
        with init_mon:
            initializer.init_epsilons(eps_sampling)


@tasks.oqtask
def run_risk(sorted_assocs, calc, monitor):
    """
    Run the risk calculation on the given assets by using the given
    hazard initializers and risk calculator.

    :param sorted_assocs:
        asset_site associations, sorted by taxonomy
    :param calc:
        the risk calculator to use
    :param monitor:
        monitor of the current risk job
    """
    acc = calc.acc
    hazard_outputs = calc.get_hazard_outputs()
    exposure_model = calc.exposure_model
    time_event = calc.time_event

    get_assets_mon = monitor("getting assets", autoflush=True)
    get_haz_mon = monitor("getting hazard", autoflush=True)

    for taxonomy, assocs_by_taxonomy in itertools.groupby(
            sorted_assocs, lambda a: a.asset.taxonomy):
        with get_assets_mon:
            assets = models.ExposureData.objects.get_asset_chunk(
                exposure_model, time_event, assocs_by_taxonomy)
        for it in models.ImtTaxonomy.objects.filter(
                job=calc.job, taxonomy=taxonomy):
            imt = it.imt.imt_str
            with get_haz_mon:
                getter = calc.getter_class(
                    imt, taxonomy, hazard_outputs, assets)
            logs.LOG.info(
                'Read %d data for %d assets of taxonomy %s, imt=%s',
                len(set(getter.site_ids)), len(assets), taxonomy, imt)

            res = calc.core(
                calc.risk_model[imt, taxonomy],
                getter, calc.outputdict, calc.oqparam, monitor)
            acc = calc.agg_result(acc, res)
    return acc


class RiskCalculator(base.Calculator):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies_asset_count:
        A dictionary mapping each taxonomy with the number of assets the
        calculator will work on. Assets are extracted from the exposure input
        and filtered according to the `region_constraint`.

    :attribute dict risk_model:
        A nested dict taxonomy -> loss type -> instances of `Workflow`.
    """

    # a list of :class:`openquake.engine.calculators.risk.validation` classes
    validators = [validation.HazardIMT, validation.EmptyExposure,
                  validation.OrphanTaxonomies, validation.ExposureLossTypes,
                  validation.NoRiskModels]

    def __init__(self, job):
        super(RiskCalculator, self).__init__(job)
        self.taxonomies_asset_count = None
        self.risk_model = None
        self.loss_types = set()
        self.acc = {}
        self.oqparam.hazard_output = models.Output.objects.get(
            pk=self.oqparam.hazard_output_id) \
            if self.oqparam.hazard_output_id else None
        dist = self.oqparam.maximum_distance
        grid_spacing = self.oqparam.region_grid_spacing
        if grid_spacing:
            dist = min(dist, grid_spacing * numpy.sqrt(2) / 2)
        self.best_maximum_distance = dist
        self.time_event = self.oqparam.time_event
        self.taxonomies_from_model = self.oqparam.taxonomies_from_model

    def get_hazard_outputs(self):
        """
        :param rcparam: OqParams instance for a risk calculation

        Returns the list of hazard outputs to be considered. Apply
        `filters` to the default queryset.
        """
        oq = self.oqparam
        if oq.hazard_output:
            return [oq.hazard_output]
        elif oq.hazard_calculation_id:
            if oq.calculation_mode in ["classical_risk", "classical_bcr",
                                       "classical_damage"]:
                filters = dict(output_type='hazard_curve_multi',
                               hazard_curve__lt_realization__isnull=False)
            elif oq.calculation_mode in [
                    "event_based_risk", "event_based_bcr"]:
                filters = dict(
                    output_type='gmf', gmf__lt_realization__isnull=False)
            elif oq.calculation_mode == "event_based_fr":
                filters = dict(output_type='ses')
            elif oq.calculation_mode in ['scenario_risk', 'scenario_damage']:
                filters = dict(output_type='gmf_scenario')
            else:
                raise NotImplementedError

            return models.Output.objects.filter(
                oq_job=oq.hazard_calculation_id, **filters).order_by('id')
        else:
            raise RuntimeError("Neither hazard calculation "
                               "neither a hazard output has been provided")

    def agg_result(self, acc, res):
        """
        Aggregation method, to be overridden in subclasses
        """
        return acc

    def populate_imt_taxonomy(self):
        """
        Populate the table `imt_taxonomy` by inserting the associations
        coming from the risk model files. For fragility functions there
        is a single IMT for each taxonomy.
        """
        imt_taxonomy_set = set()
        for (imt, taxonomy), workflow in self.risk_model.iteritems():
            self.loss_types.update(workflow.loss_types)
            imt_taxonomy_set.add((imt, taxonomy))
            # insert the IMT in the db, if not already there
            models.Imt.save_new([from_string(imt)])
        for imt, taxonomy in imt_taxonomy_set:
            models.ImtTaxonomy.objects.create(
                job=self.job, imt=models.Imt.get(imt), taxonomy=taxonomy)

            # consider only the taxonomies in the risk models if
            # taxonomies_from_model has been set to True in the
            # job.ini
            if self.taxonomies_from_model:
                self.taxonomies_asset_count = dict(
                    (t, count)
                    for t, count in self.taxonomies_asset_count.items()
                    if (imt, t) in self.risk_model)

    def pre_execute(self):
        """
        In this phase, the general workflow is:
            1. Parse the exposure to get the taxonomies
            2. Parse the available risk models
            3. Validate exposure and risk models
        """
        try:
            self.exposure_model = self.job.exposure_model
        except models.ObjectDoesNotExist:
            with self.monitor('import exposure', autoflush=True):
                ExposureDBWriter(self.job).serialize(
                    risk_parsers.ExposureModelParser(
                        self.oqparam.inputs['exposure']))
            self.exposure_model = self.job.exposure_model
        self.taxonomies_asset_count = \
            self.exposure_model.taxonomies_in(
                self.oqparam.region_constraint)

        with self.monitor('parse risk models', autoflush=True):
            self.risk_model = self.get_risk_model()

        self.populate_imt_taxonomy()

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

    def prepare_risk(self):
        """
        Associate assets and sites and for some calculator generate the
        epsilons.
        """
        self.outputdict = writers.combine_builders(
            [ob(self) for ob in self.output_builders])

        # build the initializers hazard -> risk
        ct = sorted((counts, taxonomy) for taxonomy, counts
                    in self.taxonomies_asset_count.iteritems())
        tasks.apply_reduce(prepare_risk, (ct, self, self.monitor),
                           concurrent_tasks=self.concurrent_tasks)

    @EnginePerformanceMonitor.monitor
    def execute(self):
        """
        Method responsible for the distribution strategy. The risk
        calculators share a two phase distribution logic: in phase 1
        the initializer objects are built, by distributing per taxonomy;
        in phase 2 the real computation is run, by distributing in chunks
        of asset_site associations.
        """
        self.prepare_risk()
        # then run the real computation
        assocs = models.AssetSite.objects.filter(job=self.job).order_by(
            'asset__taxonomy')
        self.acc = tasks.apply_reduce(
            run_risk, (assocs, self, self.monitor),
            self.agg_result, self.acc, self.concurrent_tasks,
            name=self.core.__name__)

    def get_risk_model(self):
        """
        :returns: a :class:`openquake.risklib.riskinput.RiskModel` dictionary
        """
        return get_risk_model(self.oqparam)
