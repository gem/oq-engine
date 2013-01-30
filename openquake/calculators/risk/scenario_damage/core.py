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
from risklib import api, scientific
from openquake.calculators.risk import general
from openquake.utils import tasks, stats
from openquake.db import models
from openquake import logs
from openquake.calculators import base


@tasks.oqtask
@stats.count_progress('r')
def scenario_damage(job_id, assets, hazard_getter, hazard_id,
                    taxonomy, fragility_model, fragility_functions,
                    ddpa_id, imt):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id: the id of the current :class:`openquake.db.models.OqJob`
    :param assets: the list of :class:`risklib.scientific.Asset`
    instances considered
    :param hazard_getter: the name of an hazard getter to be used
    :param hazard_id: the hazard output id
    :param taxonomy: the taxonomy being considered
    :param fragility_model: a
    :class:`risklib.models.input.FragilityModel object
    :param fragility_functions: a
    :class:`risklib.models.input.FragilityFunctionSeq object
    :param ddpa_id: the output.id of output_type "dmg_dist_per_asset"
    :param imt: the Intensity Measure Type of the ground motion field
    """

    hazard_getter = general.hazard_getter(hazard_getter, hazard_id, imt)

    calculator = api.ScenarioDamage(fragility_model, fragility_functions)

    outputs = calculator(assets, [hazard_getter(a.site) for a in assets])

    with logs.tracing('save statistics per site'), \
            db.transaction.commit_on_success(using='reslt_writer'):
        for output in outputs:
            save_dist_per_asset(output.fractions, ddpa_id, output.asset)

    # send aggregate fractions to the controller, the hook will collect them
    aggfractions = sum(o.fractions for o in outputs)
    base.signal_task_complete(job_id=job_id, num_items=len(assets),
                              fractions=aggfractions, taxonomy=taxonomy)

scenario_damage.ignore_result = False


### XXX: the three utilities below could go in models ###

def save_dist_per_asset(fractions, output_id, asset):
    """
    Save the damage distribution for a given asset.
    """
    dmg_states = models.DmgState.objects.filter(output_id=output_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpa = models.DmgDistPerAsset(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            exposure_data=asset,
            location=asset.site)
        ddpa.save()


def save_dist_per_taxonomy(fractions, output_id, taxonomy):
    """
    Save the damage distribution for a given taxonomy, by summing over
    all assets.
    """
    dmg_states = models.DmgState.objects.filter(output_id=output_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpt = models.DmgDistPerTaxonomy(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            taxonomy=taxonomy)
        ddpt.save()


def save_dist_total(fractions, output_id):
    """
    Save the total distribution, by summing over all assets and taxonomies.
    """
    dmg_states = models.DmgState.objects.filter(output_id=output_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddt = models.DmgDistTotal(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi])
        ddt.save()


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage Risk Calculator. Computes three kinds of damage
    distributions: per asset, per taxonomy and total.
    """

    #: The core calculation celery task function
    core_calc_task = scenario_damage

    hazard_getter = "GroundMotionScenarioGetter"

    @property
    def hazard_id(self):
        """
        The ID of the :class:`openquake.db.models.Output` from which the
        hazard getter can extract the ground motion fields used by the risk
        calculation
        """
        if not self.rc.hazard_output.is_ground_motion_field():
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")
        return self.rc.hazard_output.id

    def worker_args(self, taxonomy):
        """
        :returns: a fixed list of arguments that a calculator may want
        to pass to a worker. In this case the list of fragility_functions
        for the given taxonomy.
        """
        return [taxonomy, self.fragility_model,
                self.fragility_functions[taxonomy]]

    def task_completed_hook(self, message):
        """
        Update the dictionary self.ddpt, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy.
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
            save_dist_per_taxonomy(fractions, self.ddpt_output.id, taxonomy)
            if tot is None:  # only the first time
                tot = numpy.zeros(fractions.shape)
            tot += fractions
        if tot is not None:
            save_dist_total(tot, self.ddt_output.id)

    @property
    def calculator_parameters(self):
        """
        Calculator specific parameters
        """
        return [self.imt]

    def create_outputs(self):
        """
        Create the three kind of outputs of a ScenarioDamage calculator
        dmg_dist_per_asset, dmg_dist_per_taxonomy, dmg_dist_total and
        populate the corresponding entries in DmgState. Return the
        id of the dmg_dist_per_asset output, to be passed to the celery
        worker.
        """
        self.ddpa_output = models.Output.objects.create_output(
            self.job, "Damage Distribution per Asset",
            "dmg_dist_per_asset")

        self.ddpt_output = models.Output.objects.create_output(
            self.job, "Damage Distribution per Taxonomy",
            "dmg_dist_per_taxonomy")

        self.ddt_output = models.Output.objects.create_output(
            self.job, "Damage Distribution Total",
            "dmg_dist_total")

        for output in self.ddpa_output, self.ddpt_output, self.ddt_output:
            for lsi, dstate in enumerate(self.damage_states):
                ds = models.DmgState(output=output, dmg_state=dstate, lsi=lsi)
                ds.save()

        return [self.ddpa_output.id]

    def set_risk_models(self):
        self.fragility_model, self.fragility_functions, self.damage_states = \
            self.parse_fragility_model()
        self.ddpt = {}  # dictionary taxonomy -> fractions

    def parse_fragility_model(self):
        ## this is hard-coded for the moment
        ## TODO: read the model from the XML file
        from risklib.models import input as i
        self.rc.inputs.get(input_type='fragility').path  # will be used
        self.imt = "MMI"
        imls = [7.0, 8.0, 9.0, 10.0, 11.0]
        limit_states = ['minor', 'moderate', 'severe', 'collapse']
        damage_states = ['no_damage'] + limit_states
        fm = i.FragilityModel('discrete', imls, limit_states)
        ffs = {}

        ffs['RC/DMRF-D/LR'] = i.FragilityFunctionSeq(
            fm, i.FragilityFunctionDiscrete,
            [[0.0, 0.09, 0.56, 0.91, 0.98],
             [0.0, 0.0, 0.04, 0.78, 0.96],
             [0.0, 0.0, 0.0, 0.29, 0.88],
             [0.0, 0.0, 0.0, 0.03, 0.63]])
        ffs['RC/DMRF-D/HR'] = i.FragilityFunctionSeq(
            fm, i.FragilityFunctionDiscrete,
            [[0.0, 0.09, 0.56, 0.92, 0.99],
             [0.0, 0.0, 0.04, 0.79, 0.97],
             [0.0, 0.0, 0.0, 0.3, 0.89],
             [0.0, 0.0, 0.0, 0.04, 0.64]])

        return fm, ffs, damage_states
