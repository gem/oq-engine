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
import collections
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


class RiskCalculator(base.CalculatorNext):
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

    def __init__(self, job):
        super(RiskCalculator, self).__init__(job)

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

        try:
            self.rc.hazard_calculation
        except models.ObjectDoesNotExist:
            raise RuntimeError(
                "The provided hazard calculation ID does not exist")

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
            2. a getter object needed to get the hazard data
            3. the needed risklib calculators
            4. the output containers to be populated
            5. the specific calculator parameter set
        """
        output_containers = self.create_statistical_outputs()

        for hazard in self.rc.hazard_outputs():
            output_containers.update(self.create_outputs(hazard))

        calculator_parameters = self.calculator_parameters

        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = self.rc.exposure_model.get_asset_chunk(
                        taxonomy,
                        self.rc.region_constraint, offset, block_size)

                risklib_calculators = self.calculation_units(assets)

                yield [self.job.id, risklib_calculators,
                       output_containers] + calculator_parameters

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

    def create_statistical_outputs(self):
        """
        Create mean/quantile `models.LossCurve`/`LossMap` containers.

        :returns:
           a dict mapping `OutputKey` objects to generated container ids
        """

        ret = OutputDict()

        if len(self.rc.hazard_outputs()) < 2:
            return ret

        ret.set(models.LossCurve.objects.create(
            output=models.Output.objects.create_output(
                job=self.job,
                display_name='Mean Loss Curves',
                output_type='loss_curve'),
            statistics='mean'))

        for quantile in self.rc.quantile_loss_curves or []:
            ret.set(models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job=self.job,
                    display_name='quantile(%s)-curves' % quantile,
                    output_type='loss_curve'),
                statistics='quantile',
                quantile=quantile))

        for poe in self.rc.conditional_loss_poes or []:
            ret.set(models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    job=self.job,
                    display_name="Mean Loss Map poe=%.4f" % poe,
                    output_type="loss_map"),
                statistics="mean",
                poe=poe))

        for quantile in self.rc.quantile_loss_curves or []:
            for poe in self.rc.conditional_loss_poes or []:
                name = "Quantile Loss Map poe=%.4f q=%.4f" % (poe, quantile)
                ret.set(models.LossMap.objects.create(
                    output=models.Output.objects.create_output(
                        job=self.job,
                        display_name=name,
                        output_type="loss_map"),
                    statistics="quantile",
                    quantile=quantile,
                    poe=poe))

        return ret

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
            A dictionary mapping an OutputKey object to ids of generated
            containers
        """

        ret = OutputDict()

        job = self.job

        # add loss curve containers
        ret.set(models.LossCurve.objects.create(
            hazard_output_id=hazard_output.id,
            output=models.Output.objects.create_output(
                job,
                "Loss Curve set for hazard %s" % hazard_output.id,
                "loss_curve")))

        for poe in self.rc.conditional_loss_poes or []:
            ret.set(models.LossMap.objects.create(
                    hazard_output_id=hazard_output.id,
                    output=models.Output.objects.create_output(
                        self.job,
                        "Loss Map Set with poe %s for hazard %s" % (
                            poe, hazard_output.id),
                        "loss_map"),
                    poe=poe))

        return ret


class count_progress_risk(stats.count_progress):   # pylint: disable=C0103
    """
    Extend :class:`openquake.engine.utils.stats.count_progress` to work with
    celery task where the number of items (i.e. assets) are embedded in hazard
    getters.
    """
    def get_task_data(self, job_id, calculators, *_args):
        first_getter = calculators[0].getter
        return job_id, len(first_getter.assets)


OutputKey = collections.namedtuple('OutputKey', [
    'output_type', 'hazard_output_id', 'poe', 'quantile', 'statistics'])


class OutputDict(dict):
    """
    A dict keying OutputKey instances to database ID, with convenience
    setter and getter methods to manage Output containers
    """

    def get(self,
            output_type=None,
            hazard_output_id=None,
            poe=None,
            quantile=None,
            statistics=None):
        return self[OutputKey(output_type, hazard_output_id,
                              poe, quantile, statistics)]

    def set(self, container):

        hazard_output_id = getattr(container, "hazard_output_id")
        poe = getattr(container, "poe", None)
        quantile = getattr(container, "quantile", None)
        statistics = getattr(container, "statistics", None)

        self[OutputKey(
            output_type=container.output.output_type,
            hazard_output_id=hazard_output_id,
            poe=poe,
            quantile=quantile,
            statistics=statistics)] = container.id


#: A calculation unit holds a risklib calculator and a getter that
#: retrieves the data to work on
CalculationUnit = collections.namedtuple('CalculationUnit', 'calc getter')
