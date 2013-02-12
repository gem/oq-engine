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

import numpy
from django import db

from openquake.nrmllib.risk import parsers
from openquake.risklib import api, scientific
from openquake.risklib.models.input import FragilityModel, FragilityFunctionSeq

from openquake.engine.calculators.risk import general
from openquake.engine.utils import tasks, stats
from openquake.engine.db import models
from openquake.engine import logs
from openquake.engine.calculators import base


@tasks.oqtask
@stats.count_progress('r')
def scenario_damage(job_id, assets, hazard_getter, hazard,
                    taxonomy, fragility_model, fragility_functions,
                    output_containers, imt):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id: the id of the current
    :class:`openquake.engine.db.models.OqJob`
    :param assets: the list of :class:`openquake.risklib.scientific.Asset`
    instances considered
    :param hazard_getter: the name of an hazard getter to be used
    :param hazard: the hazard output dictionary
    :param taxonomy: the taxonomy being considered
    :param fragility_model: a
    :class:`openquake.risklib.models.input.FragilityModel object
    :param fragility_functions: a
    :class:`openquake.risklib.models.input.FragilityFunctionSeq object
    :param output_containers: a dictionary {hazard_id: output_id}
    of output_type "dmg_dist_per_asset"
    :param imt: the Intensity Measure Type of the ground motion field
    """
    calculator = api.ScenarioDamage(fragility_model, fragility_functions)
    for hazard_id in hazard:
        hazard_getter = general.hazard_getter(hazard_getter, hazard_id, imt)

        outputs = calculator(assets, [hazard_getter(a.site) for a in assets])
        with logs.tracing('save statistics per site'), \
                db.transaction.commit_on_success(using='reslt_writer'):
            rc_id = models.OqJob.objects.get(id=job_id).risk_calculation.id
            for output in outputs:
                save_dist_per_asset(output.fractions, rc_id, output.asset)

    # send aggregate fractions to the controller, the hook will collect them
    aggfractions = sum(o.fractions for o in outputs)
    base.signal_task_complete(job_id=job_id, num_items=len(assets),
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
    """

    #: The core calculation celery task function
    core_calc_task = scenario_damage

    hazard_getter = "GroundMotionScenarioGetter"

    def __init__(self, job):
        super(ScenarioDamageRiskCalculator, self).__init__(job)
        # let's define a dictionary taxonomy -> fractions
        # updated in task_completed_hook when the fractions per taxonomy
        # becomes available, as computed by the workers
        self.ddpt = {}
        self.ddpt_output = None  # will be set in #create_outputs
        self.ddt_output = None  # will be set in #create_outputs
        self.fragility_model = None  # will be set in #set_risk_models
        self.fragility_functions = None  # will be set in #set_risk_models
        self.damage_states = None  # will be set in #set_risk_models

    def hazard_outputs(self, hazard_calculation):
        raise RuntimeError(
            "This calculator can not be run against "
            "a whole hazard calculation")

    def hazard_output(self, output):
        if output.output_type != 'gmf_scenario':
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")

    def worker_args(self, taxonomy):
        """
        :returns: a fixed list of arguments that a calculator may want
        to pass to a worker. In this case taxonomy, fragility_model and
        fragility_functions for the given taxonomy.
        """
        return [taxonomy, self.fragility_model,
                self.fragility_functions[taxonomy]]

    def task_completed_hook(self, message):
        """
        :param dict message: the message sent by the worker

        Update the dictionary self.ddpt, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from the message.
        """
        taxonomy = message['taxonomy']
        fractions = message['fractions']
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

    @property
    def calculator_parameters(self):
        """
        Return the calculator specific Intensity Measure Type.
        """
        return [self.imt]

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
        models.Output.objects.create_output(
            self.job, "Damage Distribution per Asset",
            "dmg_dist_per_asset")

        models.Output.objects.create_output(
            self.job, "Damage Distribution per Taxonomy",
            "dmg_dist_per_taxonomy")

        models.Output.objects.create_output(
            self.job, "Damage Distribution Total",
            "dmg_dist_total")

        models.Output.objects.create_output(
            self.job, "Collapse Map per Asset",
            "collapse_map")

    def set_risk_models(self):
        """
        Set the attributes fragility_model, fragility_functions, damage_states
        and populate the table DmgState for the current risk calculation.
        """
        self.fragility_model, self.fragility_functions, self.damage_states = \
            self.parse_fragility_model()
        for lsi, dstate in enumerate(self.damage_states):
            models.DmgState(risk_calculation=self.job.risk_calculation,
                            dmg_state=dstate, lsi=lsi).save()

    def parse_fragility_model(self):
        """
        Parse the fragility XML file and return fragility_model,
        fragility_functions, and damage_states for usage in set_risk_models.
        """
        path = self.rc.inputs.get(input_type='fragility').path  # will be used
        iterparse = iter(parsers.FragilityModelParser(path))
        fmt, iml, limit_states = iterparse.next()
        self.imt = iml['IMT']
        damage_states = ['no_damage'] + limit_states
        fm = FragilityModel(fmt, iml['imls'], limit_states)
        ffs = {}
        for taxonomy, values, no_damage_limit in iterparse:
            ffs[taxonomy] = FragilityFunctionSeq(fm, values, no_damage_limit)
        return fm, ffs, damage_states
