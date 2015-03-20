# Copyright (c) 2015, GEM Foundation.
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
Core functionality for the classical damage risk calculator.
"""

from openquake.engine.calculators.risk import (
    base, hazard_getters, writers)
from openquake.engine.calculators import calculators
from openquake.engine.db import models


def classical_damage(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the classical risk calculator.

    :param workflow:
      A :class:`openquake.risklib.riskinput.RiskModel` instance
    :param getter:
      A HazardGetter instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (e.g. a LossCurve)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
    """
    for loss_type in workflow.loss_types:
        with monitor('computing risk'):
            outputs = workflow.compute_all_outputs(getter, loss_type)
        with monitor('saving risk'):
            for out in outputs:
                damage = models.Damage.objects.get(
                    risk_calculation=params.job_id, hazard_output=out.hid)
                writers.classical_damage(
                    out.output.assets, out.output.damages,
                    params.damage_state_ids, damage.id)
        # TODO: statistical outputs


@calculators.add('classical_damage')
class ClassicalDamageCalculator(base.RiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss maps
    for a given set of assets.
    """

    core = staticmethod(classical_damage)

    validators = []
    # TODO: add proper validation

    output_builders = [writers.DamageCurveBuilder]

    getter_class = hazard_getters.HazardCurveGetter

    def pre_execute(self):
        """
        Create the DmgState objects associated to the current calculation
        """
        super(ClassicalDamageCalculator, self).pre_execute()
        self.oqparam.job_id = self.job.id
        self.oqparam.damage_state_ids = []
        for lsi, dstate in enumerate(self.risk_model.damage_states):
            ds = models.DmgState.objects.create(
                risk_calculation=self.job, dmg_state=dstate, lsi=lsi)
            self.oqparam.damage_state_ids.append(ds.id)
