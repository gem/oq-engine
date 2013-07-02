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

import collections
import StringIO

from django.core.exceptions import ObjectDoesNotExist

from openquake.risklib import scientific
from openquake.nrmllib.risk import parsers

from openquake.engine import logs, export
from openquake.engine.utils import config, stats
from openquake.engine.db import models
from openquake.engine.calculators import base, post_processing
from openquake.engine.calculators.risk import writers
from openquake.engine.input.exposure import ExposureDBWriter


class RiskCalculator(base.Calculator):
    """
    Abstract base class for risk calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.

    :attribute dict taxonomies:
        A dictionary mapping each taxonomy with the number of assets the
        calculator will work on. Assets are extracted from the exposure input
        and filtered according to the `RiskCalculation.region_constraint`.

    :attribute dict risk_models:
        A nested dict taxonomy -> loss type -> instances of `RiskModel`.
    """

    def __init__(self, job):
        super(RiskCalculator, self).__init__(job)

        # FIXME(lp). taxonomy_asset_count would be a better name
        self.taxonomies = None
        self.risk_models = None

    def pre_execute(self):
        """
        In this phase, the general workflow is:
            1. Parse and validate the exposure to get the taxonomies
            2. Parse and validate the available risk models
            3. Validate the given hazard
            4. Initialize progress counters
            5. Update the job stats
        """

        # reload the risk calculation to avoid getting raw string
        # values instead of arrays
        self.job.risk_calculation = models.RiskCalculation.objects.get(
            pk=self.rc.pk)

        self.taxonomies = self.get_taxonomies()

        self.validate_hazard()

        with logs.tracing('parse risk models'):
            self.risk_models = self.get_risk_models()
            self.check_taxonomies(self.risk_models)
            self.check_imts(required_imts(self.risk_models))

        assets_num = sum(self.taxonomies.values())
        self._initialize_progress(assets_num)

    def validate_hazard(self):
        """
        Calculators must override this to provide additional
        validation.

        :raises:
           `ValueError` if an Hazard Calculation has been passed
           but it does not exist
        """
        # If an Hazard Calculation ID has been given in input, check
        # that it exists
        try:
            self.rc.hazard_calculation
        except ObjectDoesNotExist:
            raise RuntimeError(
                "The provided hazard calculation ID does not exist")

    def get_taxonomies(self):
        """
          Parse the exposure input and store the exposure data (if not
          already present). Then, check if the exposure filtered with
          region_constraint is not empty.

          :returns:
              a dictionary mapping taxonomy string to the number of
              assets in that taxonomy
        """
        # if we are not going to use a preloaded exposure, we need to
        # parse and store the exposure from the given xml file
        if self.rc.exposure_input is None:
            queryset = self.rc.inputs.filter(input_type='exposure')
            if queryset.exists():
                with logs.tracing('store exposure'):
                    exposure = self._store_exposure(queryset.all()[0])
            else:
                raise ValueError("No exposure model given in input")
        else:  # exposure has been preloaded. Get it from the rc
            exposure = self.rc.exposure_model

        taxonomies = exposure.taxonomies_in(self.rc.region_constraint)

        if not sum(taxonomies.values()):
            raise ValueError(
                ['Region of interest is not covered by the exposure input.'
                 ' This configuration is invalid. '
                 ' Change the region constraint input or use a proper '
                 ' exposure file'])
        return taxonomies

    def block_size(self):
        """
        Number of assets handled per task.
        """
        return int(config.get('risk', 'block_size'))

    def expected_tasks(self, block_size):
        """
        Number of tasks generated by the task_arg_gen
        """
        num_tasks = 0
        for num_assets in self.taxonomies.values():
            n, r = divmod(num_assets, block_size)
            if r:
                n += 1
            num_tasks += n
        return num_tasks

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

        num_tasks = 0
        for taxonomy, assets_nr in self.taxonomies.items():
            asset_offsets = range(0, assets_nr, block_size)

            for offset in asset_offsets:
                with logs.tracing("getting assets"):
                    assets = models.ExposureData.objects.get_asset_chunk(
                        self.rc, taxonomy, offset, block_size)

                calculation_units = self.get_calculation_units(assets)

                num_tasks += 1
                yield [self.job.id,
                       calculation_units,
                       output_containers,
                       self.calculator_parameters]

        # sanity check to protect against future changes of the distribution
        # logic
        expected_tasks = self.expected_tasks(block_size)
        if num_tasks != expected_tasks:
            raise RuntimeError('Expected %d tasks, generated %d!' % (
                               expected_tasks, num_tasks))

    def get_calculation_units(self, assets):
        """
        :returns: the calculation units to be considered. Default
        behavior is to returns a dict keyed by loss types. Calculators
        that do not support multiple loss types must override this
        method.
        """
        return dict([(loss_type, self.calculation_units(loss_type, assets))
                     for loss_type in loss_types(self.risk_models)])

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
        ExposureDBWriter(exposure_model_input).serialize(
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

        job_stats = models.JobStats.objects.get(oq_job=self.job)
        job_stats.num_sites = total
        job_stats.num_tasks = self.expected_tasks(self.block_size())
        job_stats.save()

    def get_risk_models(self, retrofitted=False):
        """
        Parse vulnerability models for each loss type in
        `openquake.engine.db.models.LOSS_TYPES`,
        then set the `risk_models` attribute.

        :param bool retrofitted:
            True if retrofitted models should be set
        :returns:
            all the intensity measure types required by the risk models
        :raises:
            * `ValueError` if no models can be found
            * `ValueError` if the exposure does not provide the costs needed
            by the available loss types in the risk models
        """
        risk_models = collections.defaultdict(dict)

        for loss_type in models.LOSS_TYPES:
            if loss_type == "fatalities":
                cost_type = "occupants"
            else:
                cost_type = loss_type

            vfs = self.get_vulnerability_model(cost_type, retrofitted)
            for taxonomy, model in vfs.items():
                risk_models[taxonomy][loss_type] = model

            if vfs:
                if loss_type != "fatalities":
                    if not self.rc.exposure_model.exposuredata_set.filter(
                            cost__cost_type__name=cost_type).exists():
                        raise ValueError(
                            "Invalid exposure "
                            "for computing loss type %s. " % loss_type)
                else:
                    if self.rc.exposure_model.missing_occupants():
                        raise ValueError("Invalid exposure "
                                         "for computing occupancy losses.")

        if not risk_models:
            raise ValueError(
                'At least one risk model of type %s must be defined' % (
                    models.LOSS_TYPES))
        return risk_models

    def check_imts(self, model_imts):
        """
        Raise a ValueError if no hazard exists in any of the given
        intensity measure types

        :param model_imts:
           an iterable of intensity measure types in long form string.
        """
        imts = self.hc.get_imts()
        imts = sorted(imts)

        # check that the hazard data have all the imts needed by the
        # risk calculation
        missing = set(model_imts) - set(imts)
        missing = sorted(list(missing))

        if missing:
            raise ValueError(
                "There is no hazard output for: %s. "
                "The available IMTs are: %s." % (", ".join(missing),
                                                 ", ".join(imts)))

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

    def get_vulnerability_model(self, cost_type, retrofitted=False):
        """
        Load and parse the vulnerability model input associated with this
        calculation.

        :param str cost_type:
            any value that has a corresponding CostType instance in the
            current calculation
        :param bool retrofitted:
            `True` if the retrofitted model is going to be parsed

        :returns:
            a dictionary mapping each taxonomy to a :class:`RiskModel` instance
        """

        if retrofitted:
            input_type = "vulnerability_retrofitted"
        else:
            input_type = "vulnerability"

        input_type = "%s_%s" % (cost_type, input_type)

        queryset = self.rc.inputs.filter(input_type=input_type)
        if not queryset.exists():
            return {}
        else:
            model = queryset[0]

        content = StringIO.StringIO(model.model_content.raw_content_ascii)

        return self.parse_vulnerability_model(content)

    def parse_vulnerability_model(self, vuln_content):
        """
        :param vuln_content:
            File-like object containg the vulnerability model XML.
        :returns:
            a `dict` of `RiskModel` keyed by taxonomy
        :raises:
            * `ValueError` if validation of any vulnerability function fails
        """
        vfs = dict()

        for record in parsers.VulnerabilityModelParser(vuln_content):
            taxonomy = record['ID']
            imt = record['IMT']
            loss_ratios = record['lossRatio']
            covs = record['coefficientsVariation']
            distribution = record['probabilisticDistribution']

            if taxonomy in vfs:
                raise ValueError("Error creating vulnerability function for "
                                 "taxonomy %s. A taxonomy can not "
                                 "be associated with "
                                 "different vulnerability functions" % (
                                 taxonomy))

            try:
                vfs[taxonomy] = RiskModel(
                    imt,
                    scientific.VulnerabilityFunction(
                        record['IML'],
                        loss_ratios,
                        covs,
                        distribution),
                    None)
            except ValueError, err:
                msg = (
                    "Invalid vulnerability function with ID '%s': %s"
                    % (taxonomy, err.message)
                )
                raise ValueError(msg)

        return vfs

    def create_outputs(self, hazard_output):
        """
        Create outputs container objects (e.g. LossCurve, Output).

        Derived classes should override this to create containers for
        storing objects other than LossCurves, LossMaps

        The default behavior is to create a loss curve and loss maps
        output.

        :returns:
            An instance of
            :class:`openquake.engine.calculators.risk.writers.OutputDict`
        """

        ret = writers.OutputDict()

        job = self.job

        for loss_type in loss_types(self.risk_models):
            # add loss curve containers
            ret.set(models.LossCurve.objects.create(
                hazard_output_id=hazard_output.id,
                loss_type=loss_type,
                output=models.Output.objects.create_output(
                    job,
                    "loss curves. type=%s, hazard=%s" % (
                        loss_type, hazard_output.id),
                    "loss_curve")))

            # then loss maps containers
            for poe in self.rc.conditional_loss_poes or []:
                ret.set(models.LossMap.objects.create(
                        hazard_output_id=hazard_output.id,
                        loss_type=loss_type,
                        output=models.Output.objects.create_output(
                            self.job,
                            "loss maps. type=%s poe=%s, hazard=%s" % (
                                loss_type, poe, hazard_output.id),
                            "loss_map"),
                        poe=poe))
        return ret

    def create_statistical_outputs(self):
        """
        Create mean/quantile `models.LossCurve`/`LossMap` containers.

        :returns:
           an instance of
           :class:`openquake.engine.calculators.risk.writers.OutputDict`
        """

        ret = writers.OutputDict()

        if len(self.rc.hazard_outputs()) < 2:
            return ret

        for loss_type in loss_types(self.risk_models):
            ret.set(models.LossCurve.objects.create(
                output=models.Output.objects.create_output(
                    job=self.job,
                    display_name='mean loss curves. type=%s' % loss_type,
                    output_type='loss_curve'),
                statistics='mean',
                loss_type=loss_type))

            for quantile in self.rc.quantile_loss_curves or []:
                name = 'quantile(%s) loss curves. type=%s' % (
                    quantile, loss_type)
                ret.set(models.LossCurve.objects.create(
                    output=models.Output.objects.create_output(
                        job=self.job,
                        display_name=name,
                        output_type='loss_curve'),
                    statistics='quantile',
                    quantile=quantile,
                    loss_type=loss_type))

            for poe in self.rc.conditional_loss_poes or []:
                ret.set(models.LossMap.objects.create(
                    output=models.Output.objects.create_output(
                        job=self.job,
                        display_name="mean loss map type=%s poe=%.4f" % (
                            loss_type, poe),
                        output_type="loss_map"),
                    statistics="mean",
                    loss_type=loss_type,
                    poe=poe))

            for quantile in self.rc.quantile_loss_curves or []:
                for poe in self.rc.conditional_loss_poes or []:
                    name = "quantile(%.4f) loss map type=%s poe=%.4f" % (
                        quantile, loss_type, poe)
                    ret.set(models.LossMap.objects.create(
                        output=models.Output.objects.create_output(
                            job=self.job,
                            display_name=name,
                            output_type="loss_map"),
                        statistics="quantile",
                        quantile=quantile,
                        loss_type=loss_type,
                        poe=poe))

        return ret


class count_progress_risk(stats.count_progress):   # pylint: disable=C0103
    """
    Extend :class:`openquake.engine.utils.stats.count_progress` to work with
    celery task where the number of items (i.e. assets) are embedded in
    calculation units.
    """
    def get_task_data(self, job_id, units, *_args):
        num_items = get_num_items(units)

        return job_id, num_items


def get_num_items(units):
    """
    :param units:
        a not empty dictionary of not empty lists of
        :class:`openquake.engine.calculators.risk.base.CalculationUnit`
        instances
    """
    # FIXME(lp). Navigating in an opaque structure is a code smell.
    # We need to refactor the data structure used by celery tasks.

    # let's get the first one
    first_list_of_units = units.values()[0]

    # get the first item in the list. Then, get the getter from it
    # (an instance of `..hazard_getters.HazardGetter`.
    first_getter = first_list_of_units[0].getter

    # A getter keeps a reference to the list of assets we want to
    # consider
    num_items = len(first_getter.assets)

    return num_items


#: Hold both a Vulnerability function or a fragility function set and
#: the IMT associated to it
RiskModel = collections.namedtuple(
    'RiskModel',
    'imt vulnerability_function fragility_functions')


#: A calculation unit holds a risklib calculator (e.g. an instance of
#: :class:`openquake.risklib.api.Classical`), a getter that
#: retrieves the data to work on, and the type of losses we are considering
CalculationUnit = collections.namedtuple(
    'CalculationUnit',
    'calc getter')


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


def asset_statistics(losses, curves_poes, quantiles, weights, poes):
    """
    Compute output statistics (mean/quantile loss curves and maps)
    for a single asset

    :param losses:
       the losses on which the loss curves are defined
    :param curves_poes:
       a numpy matrix suitable to be used with
       :func:`openquake.engine.calculators.post_processing`
    :param list quantiles:
       an iterable over the quantile levels to be considered for
       quantile outputs
    :param list weights:
       the weights associated with each realization. If all the elements are
       `None`, implicit weights are taken into account
    :param list poes:
       the poe taken into account for computing loss maps

    :returns:
       a tuple with
       1) mean loss curve
       2) a list of quantile curves
    """
    montecarlo = weights[0] is not None

    quantile_curves = []
    for quantile in quantiles:
        if montecarlo:
            q_curve = post_processing.weighted_quantile_curve(
                curves_poes, weights, quantile)
        else:
            q_curve = post_processing.quantile_curve(curves_poes, quantile)

        quantile_curves.append((losses, q_curve))

    # then mean loss curve
    mean_curve_poes = post_processing.mean_curve(curves_poes, weights)
    mean_curve = (losses, mean_curve_poes)

    mean_map = [scientific.conditional_loss_ratio(losses, mean_curve_poes, poe)
                for poe in poes]

    quantile_maps = [[scientific.conditional_loss_ratio(losses, poes, poe)
                      for losses, poes in quantile_curves]
                     for poe in poes]

    return (mean_curve, quantile_curves, mean_map, quantile_maps)


def required_imts(risk_models):
    """
    Get all the intensity measure types required by `risk_models`

    A nested dict taxonomy -> loss_type -> `RiskModel` instance

    :returns: a set with all the required imts
    """
    risk_models = sum([d.values() for d in risk_models.values()], [])
    return set([m.imt for m in risk_models])


def loss_types(risk_models):
    return set(sum([d.keys() for d in risk_models.values()], []))
