#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Core functionality for the scenario_damage risk calculator.
"""

import StringIO
import collections

import numpy

from django import db

from openquake.nrmllib.risk import parsers
from openquake.risklib import api, scientific

from openquake.engine.calculators.risk import general
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine import logs
from openquake.engine.calculators import base


@tasks.oqtask
@general.count_progress_risk('r')
def scenario_damage(job_id, hazard,
                    taxonomy, fragility_functions,
                    _output_containers, _statistical_output_contaienrs):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id:
        The id of the current :class:`openquake.engine.db.models.OqJob`
    :param dict hazard:
        A dictionary mapping IDs of :class:`openquake.engine.db.models.Output`
        (with output_type set to 'gmf_scenario') to a tuple where the first
        element is an instance of
        :class:`..hazard_getters.GroundMotionScenarioGetter`, and the second
        element is the corresponding weight.
    :param taxonomy:
        The taxonomy being considered
    :param list fragility_functions:
        A list of callables representing the fragility functions used by the
        risklib calculator
    :param _output_containers:
        A dictionary {hazard_id: output_id} of output_type "dmg_dist_per_asset"
    """
    calculator = api.ScenarioDamage(fragility_functions)

    # Scenario Damage works only on one hazard
    hazard_getter = hazard.values()[0][0]
    with EnginePerformanceMonitor('hazard_getter', job_id, scenario_damage):
        assets, ground_motion_values, missings = hazard_getter()
    if not len(assets):
        logs.LOG.warn("Exit from task as no asset could be processed")
        base.signal_task_complete(
            job_id=job_id, fractions=None,
            num_items=len(missings), taxonomy=taxonomy)
        return

    with EnginePerformanceMonitor('computing', job_id, scenario_damage):
        fraction_matrix = calculator(ground_motion_values)
        aggfractions = sum(fraction_matrix[i] * asset.number_of_units
                           for i, asset in enumerate(assets))

    with EnginePerformanceMonitor('saving', job_id, scenario_damage), \
            db.transaction.commit_on_success(using='reslt_writer'):
        rc_id = models.OqJob.objects.get(id=job_id).risk_calculation.id
        for i, asset in enumerate(assets):
            save_dist_per_asset(
                fraction_matrix[i] * asset.number_of_units, rc_id, asset)

    # send aggregate fractions to the controller, the hook will collect them
    base.signal_task_complete(job_id=job_id,
                              num_items=len(assets) + len(missings),
                              fractions=aggfractions, taxonomy=taxonomy)

scenario_damage.ignore_result = False


def save_dist_per_asset(fractions, rc_id, asset):
    """
    Save the damage distribution for a given asset.

    :param fractions: numpy array with the damage fractions
    :param rc_id: the risk_calculation_id
    :param asset: an ExposureData instance
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpa = models.DmgDistPerAsset(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            exposure_data=asset)
        ddpa.save()


def save_dist_per_taxonomy(fractions, rc_id, taxonomy):
    """
    Save the damage distribution for a given taxonomy, by summing over
    all assets.

    :param fractions: numpy array with the damage fractions
    :param int rc_id: the risk_calculation_id
    :param str: the taxonomy string
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpt = models.DmgDistPerTaxonomy(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            taxonomy=taxonomy)
        ddpt.save()


def save_dist_total(fractions, rc_id):
    """
    Save the total distribution, by summing over all assets and taxonomies.

    :param fractions: numpy array with the damage fractions
    :param int rc_id: the risk_calculation_id
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddt = models.DmgDistTotal(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi])
        ddt.save()


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage Risk Calculator. Computes four kinds of damage
    distributions: per asset, per taxonomy, total and collapse map.

    :attr dict fragility_functions:
        A dictionary of dictionary mapping taxonomy ->
        (limit state -> fragility function) where a fragility function is an
        instance of
        :class:`openquake.risklib.scientific.FragilityFunctionContinuous` or
        :class:`openquake.risklib.scientific.FragilityFunctionDiscrete`.
    """

    #: The core calculation celery task function
    core_calc_task = scenario_damage

    hazard_getter = general.hazard_getters.GroundMotionScenarioGetter

    def __init__(self, job):
        super(ScenarioDamageRiskCalculator, self).__init__(job)
        # let's define a dictionary taxonomy -> fractions
        # updated in task_completed_hook when the fractions per taxonomy
        # becomes available, as computed by the workers
        self.ddpt = {}
        self.ddpt_output = None  # will be set in #create_outputs
        self.ddt_output = None  # will be set in #create_outputs
        self.fragility_functions = None  # will be set in #set_risk_models
        self.damage_states = None  # will be set in #set_risk_models

    def hazard_outputs(self, hazard_calculation):
        """
        :returns:
            The single hazard output associated to `hazard_calculation`
        """

        # in scenario hazard calculation we do not have hazard logic
        # tree realizations, and we have only one output
        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.get(
                output_type='gmf_scenario')

    def create_getter(self, output, imt, assets):
        """
        See :meth:`..general.BaseRiskCalculator.create_getter`
        """
        if output.output_type != 'gmf_scenario':
            raise RuntimeError(
                "The provided hazard output is not a ground motion field: %s"
                % output.output_type)

        return (self.hazard_getter(
            output.id, imt, assets, self.rc.best_maximum_distance), 1)

    def worker_args(self, taxonomy):
        """
        :returns:
            A fixed list of arguments that a calculator may want to pass to a
            worker. In this case taxonomy, fragility_model and
            fragility_functions for the given taxonomy.
        """
        return [taxonomy,
                self.fragility_functions[taxonomy]]

    def task_completed_hook(self, message):
        """
        Update the dictionary self.ddpt, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from the message.

        :param dict message:
            The message sent by the worker
        """
        taxonomy = message['taxonomy']
        fractions = message.get('fractions')

        if fractions is not None:
            if taxonomy not in self.ddpt:
                self.ddpt[taxonomy] = numpy.zeros(fractions.shape)
            self.ddpt[taxonomy] += fractions

    def post_process(self):
        """
        Save the damage distributions by taxonomy and total on the db.
        """
        tot = None
        for taxonomy, fractions in self.ddpt.iteritems():
            save_dist_per_taxonomy(fractions, self.rc.id, taxonomy)
            if tot is None:  # only the first time
                tot = numpy.zeros(fractions.shape)
            tot += fractions
        if tot is not None:
            save_dist_total(tot, self.rc.id)

    # must be overridden, otherwise the parent will create loss curves
    def create_outputs(self, _hazard_ouput):
        """
        Create the outputs of a ScenarioDamage calculator
        dmg_dist_per_asset, dmg_dist_per_taxonomy, dmg_dist_total, collapse_map
        """
        # NB: the outputs do not need to be passed to the workers, since
        # the aggregation per taxonomy and total are performed in the
        # controller node, in the task_completion_hook, whereas the
        # computations per asset only need the risk_calculation_id,
        # extracted from the job_id
        ddpa = models.Output.objects.create_output(
            self.job, "Damage Distribution per Asset",
            "dmg_dist_per_asset")

        ddpt = models.Output.objects.create_output(
            self.job, "Damage Distribution per Taxonomy",
            "dmg_dist_per_taxonomy")

        ddt = models.Output.objects.create_output(
            self.job, "Damage Distribution Total",
            "dmg_dist_total")

        collapse_map = models.Output.objects.create_output(
            self.job, "Collapse Map per Asset",
            "collapse_map")

        # save the damage states for the given risk calculation
        for lsi, dstate in enumerate(self.damage_states):
            models.DmgState.objects.create(
                risk_calculation=self.job.risk_calculation,
                dmg_state=dstate, lsi=lsi)

        return [ddpa, ddpt, ddt, collapse_map]

    def set_risk_models(self):
        """
        Set the attributes fragility_model, fragility_functions, damage_states
        and manage the case of missing taxonomies.
        """
        self.fragility_functions = fm = self.parse_fragility_model()
        self.check_taxonomies(fm)

    def parse_fragility_model(self):
        """
        Parse the fragility XML file and return fragility_model,
        fragility_functions, and damage_states for usage in set_risk_models.
        """
        content = StringIO.StringIO(
            self.rc.inputs.get(
                input_type='fragility').model_content.raw_content_ascii)
        iterparse = iter(parsers.FragilityModelParser(content))
        fmt, limit_states = iterparse.next()

        self.damage_states = ['no_damage'] + limit_states
        self.fragility_functions = collections.defaultdict(dict)

        for taxonomy, iml, params, no_damage_limit in iterparse:
            self.taxonomies_imts[taxonomy] = iml['IMT']

            if fmt == "discrete":
                if no_damage_limit is None:
                    self.fragility_functions[taxonomy] = [
                        scientific.FragilityFunctionDiscrete(
                            iml['imls'], poes, iml['imls'][0])
                        for poes in params]
                else:
                    self.fragility_functions[taxonomy] = [
                        scientific.FragilityFunctionDiscrete(
                            [no_damage_limit] + iml['imls'], [0.0] + poes,
                            no_damage_limit)
                        for poes in params]

            else:
                self.fragility_functions[taxonomy] = [
                    scientific.FragilityFunctionContinuous(*mean_stddev)
                    for mean_stddev in params]
        return self.fragility_functions

    def create_statistical_outputs(self):
        """
        Override default behaviour as BCR and scenario calculators do
        not compute mean/quantiles outputs"
        """
        pass
