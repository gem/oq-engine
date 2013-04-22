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

"""Base RiskCalculator class."""

import random
import StringIO

from openquake.risklib import scientific

from openquake.engine import logs
from openquake.engine.utils import config
from openquake.engine.db import models
from openquake.engine.calculators import base
from openquake.engine import export
from openquake.engine.utils import stats
from openquake.nrmllib.risk import parsers

# FIXME: why is a writer in a package called "input" ?
from openquake.engine.input import exposure as db_writer


class BaseRiskCalculator(base.Calculator):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies:
        A dictionary mapping each taxonomy with the number of assets the
        calculator will work on. Assets are extracted from the exposure input
        and filtered according to the `RiskCalculation.region_constraint`.

    :attribute asset_offsets:
        A generator of asset offsets used by each celery task. Assets are
        ordered by their id. An asset offset is an int that identify the set of
        assets going from offset to offset + block_size.

    :attribute dict vulnerability_functions:
        A dict mapping taxonomy to vulnerability functions used for this
        calculation.

    :attribute rnd:
        The random number generator (initialized with a master seed) used for
        sampling.

    :attribute dict taxonomy_imt:
        A dictionary mapping taxonomies to intensity measure type, to
        support structure dependent intensity measure types
    """

    hazard_getter = None  # the name of the hazard getter class; to override

    def __init__(self, job):
        super(BaseRiskCalculator, self).__init__(job)

        self.taxonomies = None
        self.rnd = None
        self.vulnerability_functions = None
        self.taxonomy_imt = dict()

    def pre_execute(self):
        """
        In this phase, the general workflow is:

            1. Parse the exposure input and store the exposure data (if not
               already present)
            2. Check if the exposure filtered with region_constraint is not
               empty
            3. Parse the risk models
            4. Initialize progress counters
            5. Initialize random number generator

        """

        # reload the risk calculation to avoid getting raw string
        # values instead of arrays
        self.job.risk_calculation = models.RiskCalculation.objects.get(
            pk=self.rc.pk)

        with logs.tracing('store exposure'):
            if self.rc.exposure_input is None:
                queryset = self.rc.inputs.filter(input_type='exposure')

                if queryset.exists():
                    self._store_exposure(queryset.all()[0])
                else:
                    raise RuntimeError("No exposure model given in input")

            self.taxonomies = self.rc.exposure_model.taxonomies_in(
                self.rc.region_constraint)

            if not sum(self.taxonomies.values()):
                raise RuntimeError(
                    ['Region of interest is not covered by the exposure input.'
                     ' This configuration is invalid. '
                     ' Change the region constraint input or use a proper '
                     ' exposure file'])

        with logs.tracing('store risk model'):
            self.set_risk_models()

        self._initialize_progress(sum(self.taxonomies.values()))

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

        :returns:
            An iterator over a list of arguments. Each contains:

            1. the job id
            2. the exposure subset on which the celery task is applied on
            3. the hazard getter and the hazard_id to be used
            4. a seed (eventually generated from a master seed)
            5. the output containers to be populated
            6. the specific calculator parameter set
        """
        output_containers = dict(
            (hazard_output.id,
             self.create_outputs(hazard_output))
            for hazard_output in self.considered_hazard_outputs())

        if self.rc.hazard_calculation:
            statistical_output_containers = self.create_statistical_outputs()
        else:
            statistical_output_containers = []

        calculator_parameters = self.calculator_parameters

        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = self.rc.exposure_model.get_asset_chunk(
                        taxonomy,
                        self.rc.region_constraint, offset, block_size)

                hazard = dict((ho.id, self.create_getter(ho, assets))
                              for ho in self.considered_hazard_outputs())

                taxonomy_args = self.taxonomy_args(taxonomy)

                logs.LOG.debug("Task with %s assets (%s, %s) got args %s",
                               len(assets), offset, block_size, taxonomy_args)

                yield ([self.job.id, hazard] +
                       taxonomy_args +
                       [output_containers] +
                       [statistical_output_containers] +
                       calculator_parameters)

    def taxonomy_args(self, taxonomy):
        """
        :returns:
            A fixed list of arguments that depends on the taxonomy that a
            calculator pass to a worker. Default to:

            1) a seed generated from the master seed
            2) the vulnerability function associated with the assets taxonomy
            3) the imt associated to such taxonomy

            Must be overriden in order to provide more/less arguments
            that depends on the taxonomy.
        """
        return [self.rnd.randint(0, models.MAX_SINT_32),
                self.vulnerability_functions[taxonomy],
                self.taxonomy_imt[taxonomy]]

    def export(self, *args, **kwargs):
        """
        If requested by the user, automatically export all result artifacts.

        :returns:
            A list of the export filenames, including the absolute path to each
            file.
        """

        exported_files = []
        with logs.tracing('exports'):
            if 'exports' in kwargs and kwargs['exports']:
                exported_files = sum([
                    export.risk.export(output.id, self.rc.export_dir)
                    for output in export.core.get_outputs(self.job.id)], [])

                for exp_file in exported_files:
                    logs.LOG.debug('exported %s' % exp_file)
        return exported_files

    # FIXME(lp). This logic (with the ones in `hazard_outputs`) should
    # go into the models module
    def considered_hazard_outputs(self):
        """
        Returns the list of hazard outputs to be considered
        """
        if self.rc.hazard_output:
            return [self.rc.hazard_output]
        else:
            return self.hazard_outputs(self.rc.hazard_calculation)

    def hazard_outputs(self, hazard_calculation):
        """
        Calculators must override this to select from the hazard calculation
        given in input which are the Output objects to be considered by the
        risk calculation to get the actual hazard input.

        Result objects should be ordered (e.g. by id) and be associated to a
        hazard logic tree realization.

        :returns:
            A list of :class:`openquake.engine.db.models.Output`
            objects to be used for a risk calculation.
        """
        raise NotImplementedError

    def create_statistical_outputs(self):
        """
        Create mean/quantile `Output` and `LossCurve`/`LossMap` containers.
        """

        mean_loss_curve_id = models.LossCurve.objects.create(
            output=models.Output.objects.create_output(
                job=self.job,
                display_name='Mean Loss Curves',
                output_type='loss_curve'),
            statistics='mean').id

        quantile_loss_curve_ids = dict(
            (quantile,
             models.LossCurve.objects.create(
                 output=models.Output.objects.create_output(
                     job=self.job,
                     display_name='quantile(%s)-curves' % quantile,
                     output_type='loss_curve'),
                 statistics='quantile',
                 quantile=quantile).id)
            for quantile in self.rc.quantile_loss_curves or [])

        mean_loss_map_ids = dict(
            (poe,
             models.LossMap.objects.create(
                 output=models.Output.objects.create_output(
                     job=self.job,
                     display_name="Mean Loss Map poe=%.4f" % poe,
                     output_type="loss_map"),
                 statistics="mean").id)
            for poe in self.rc.conditional_loss_poes or [])

        quantile_loss_map_ids = dict(
            (quantile,
             dict(
                 (poe, models.LossMap.objects.create(
                     output=models.Output.objects.create_output(
                         job=self.job,
                         display_name="Quantile Loss Map poe=%.4f q=%.4f" % (
                             poe, quantile),
                         output_type="loss_map"),
                     statistics="quantile",
                     quantile=quantile).id)
                 for poe in self.rc.conditional_loss_poes))
            for quantile in self.rc.quantile_loss_curves or [])

        return [mean_loss_curve_id, quantile_loss_curve_ids,
                mean_loss_map_ids, quantile_loss_map_ids]

    def create_getter(self, output, assets):
        """
        Create an instance of :class:`.hazard_getters.HazardGetter` associated
        to an hazard output.

        Calculator must override this to create the proper hazard getter.

        :param output:
            The ID of an :class:`openquake.engine.db.models.Output` produced by
            a hazard calculation.

        :param assets:
            The assets for which the HazardGetter should be created.

        :returns:
            A tuple where the first element is the hazard getter and the second
            is the associated weight (if `output` is associated with a logic
            tree realization).

        :raises:
            `RuntimeError` if the hazard associated with the `output` is not
            suitable to be used with this calculator.
        """
        raise NotImplementedError

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
        celery task function. Calculators should override this to
        provide custom arguments to its celery task
        """
        return []

    def _store_exposure(self, exposure_model_input):
        """
        Load exposure assets and write them to database.

        :param exposure_model_input: a
        :class:`openquake.engine.db.models.Input` object with input
        type `exposure`
        """

        # If this was an existing model, it was already parsed and should be in
        # the DB.
        if models.ExposureModel.objects.filter(
                input=exposure_model_input).exists():
            logs.LOG.debug("skipping storing exposure as an input model "
                           "was already present")
            return exposure_model_input.exposuremodel

        content = StringIO.StringIO(
            exposure_model_input.model_content.raw_content_ascii)
        db_writer.ExposureDBWriter(exposure_model_input).serialize(
            parsers.ExposureModelParser(content))
        return exposure_model_input.exposuremodel

    def _initialize_progress(self, total):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        logs.LOG.debug("Computing risk over %d assets" % total)
        self.progress.update(total=total)
        stats.pk_set(self.job.id, "lvr", 0)
        stats.pk_set(self.job.id, "nrisk_total", total)
        stats.pk_set(self.job.id, "nrisk_done", 0)

    def set_risk_models(self):
        (self.vulnerability_functions, self.taxonomy_imt) = (
            self.get_vulnerability_model())
        self.check_taxonomies(self.vulnerability_functions)

    def check_taxonomies(self, taxonomies):
        """
        If the model has less taxonomies than the exposure raises an
        error unless the parameter ``taxonomies_from_model`` is set.

        :param taxonomies:
            Taxonomies coming from the fragility/vulnerability model
        """
        orphans = set(self.taxonomies) - set(taxonomies)
        if orphans:
            msg = ('The following taxonomies are in the exposure model '
                   'but not in the risk model: %s' % sorted(orphans))
            if self.rc.taxonomies_from_model:
                # only consider the taxonomies in the fragility model
                self.taxonomies = dict((t, self.taxonomies[t])
                                       for t in self.taxonomies
                                       if t in taxonomies)
                logs.LOG.warn(msg)
            else:
                # all taxonomies in the exposure must be covered
                raise RuntimeError(msg)

    def get_vulnerability_model(self, retrofitted=False):
        """
        Load and parse the vulnerability model input associated with this
        calculation.

        :param bool retrofitted:
            `True` if the retrofitted model is going to be parsed

        :returns:
            A tuple with
               1) a dictionary mapping each taxonomy to a
               :class:`openquake.risklib.scientific.VulnerabilityFunction`
               instance.
               2) a dictionary mapping each taxonomy to an intensity
               measure type expressed as a string, i.e. SA(0.1)
        """

        if retrofitted:
            input_type = "vulnerability_retrofitted"
        else:
            input_type = "vulnerability"

        content = StringIO.StringIO(
            self.rc.inputs.get(
                input_type=input_type).model_content.raw_content_ascii)

        return self.parse_vulnerability_model(content)

    def parse_vulnerability_model(self, vuln_content):
        """
        Parse the vulnerability model and return a `dict` of vulnerability
        functions keyed by taxonomy and a `dict` of imts keyed by taxonomy.

        If a taxonomy is associated with more than one Intensity Measure Type
        (IMT), a `ValueError` will be raised.

        :param vuln_content:
            File-like object containg the vulnerability model XML.
        :returns:
            A dictionary mapping each taxonomy (as a `str`) to a
            :class:`openquake.risklib.scientific.VulnerabilityFunction`
            instance.
        :raises:
            * `ValueError` if a taxonomy is associated with more than one IMT.
            * `ValueError` if a loss ratio is 0 and its corresponding CoV
              (Coefficient of Variation) is > 0.0. This is mathematically
              impossible.
        """
        vfs = dict()

        taxonomy_imt = {}

        for record in parsers.VulnerabilityModelParser(vuln_content):
            taxonomy = record['ID']
            imt = record['IMT']
            loss_ratios = record['lossRatio']
            covs = record['coefficientsVariation']

            registered_imt = taxonomy_imt.get(taxonomy, imt)

            if imt != registered_imt:
                raise ValueError("The same taxonomy is associated with "
                                 "different imts %s and %s" % (
                                 imt, registered_imt))
            else:
                taxonomy_imt[taxonomy] = imt

            try:
                vfs[taxonomy] = scientific.VulnerabilityFunction(
                    record['IML'],
                    loss_ratios,
                    covs,
                    record['probabilisticDistribution'])
            except ValueError, err:
                msg = (
                    "Invalid vulnerability function with ID '%s': %s"
                    % (taxonomy, err.message)
                )
                raise ValueError(msg)

        imts = self.hc.get_imts()

        # check that the hazard data have all the imts needed by the
        # risk calculation
        for imt in set(taxonomy_imt.values()):
            if not imt in imts:
                raise ValueError(
                    "There is no hazard output for the intensity measure "
                    "%s; the available IMTs are %s" % (imt, imts))

        return vfs, taxonomy_imt

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves, LossMaps

        The default behavior is to create a loss curve and loss maps
        output.

        :returns:
            A dictionary mapping an Output object ID to a list of int (id of
            containers) or dict (poe->int)
        """

        job = self.job

        # add loss curve containers
        loss_curve_id = models.LossCurve.objects.create(
            hazard_output_id=hazard_output.id,
            output=models.Output.objects.create_output(
                job, "Loss Curve set for hazard %s" % hazard_output.id,
                "loss_curve")).pk

        # loss maps (or conditional loss maps) ...
        loss_map_ids = dict()

        if self.rc.conditional_loss_poes is not None:
            for poe in self.rc.conditional_loss_poes:
                loss_map_ids[poe] = models.LossMap.objects.create(
                    hazard_output_id=hazard_output.id,
                    output=models.Output.objects.create_output(
                        self.job,
                        "Loss Map Set with poe %s for hazard %s" % (
                            poe, hazard_output.id),
                        "loss_map"),
                    poe=poe).pk

        return [loss_curve_id, loss_map_ids]


class count_progress_risk(stats.count_progress):   # pylint: disable=C0103
    """
    Extend :class:`openquake.engine.utils.stats.count_progress` to work with
    celery task where the number of items (i.e. assets) are embedded in hazard
    getters.
    """
    def get_task_data(self, job_id, hazard_data, *args):

        first_hazard_data = hazard_data.values()[0]

        getter, _weight = first_hazard_data
        return job_id, len(getter.assets)
