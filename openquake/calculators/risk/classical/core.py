# Copyright (c) 2010-2012, GEM Foundation.
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


from openquake.calculators.risk import general
from openquake.utils import tasks
from openquake.utils import stats
from openquake import logs
from risklib import api
from django.db import transaction


@tasks.oqtask
@general.with_assets
@stats.count_progress('r')
def classical(job_id, assets, hazard_getter, hazard_id,
              loss_curve_id, loss_map_ids,
              lrem_steps_per_interval, conditional_loss_poes):
    """
    Celery task for the classical risk calculator.

    Gets vulnerability model, instantiates risklib calculators and
    stores results to db in a single transaction.

    :param int job_id:
      ID of the currently running job
    :param assets:
      list of Assets to take into account
    :param hazard_getter:
      Strategy used to get the hazard curves
    :param int hazard_id
      ID of the Hazard Output the risk calculation is based on
    :param loss_curve_id
      ID of the `openquake.db.models.LossCurve` output container used
      to store the computed loss curves
    :param loss_map_ids
      Dictionary poe->ID of the `openquake.db.models.LossMap` output
      container used to store the computed loss maps
    :param int lrem_steps_per_interval
      Steps per interval used to compute the Loss Ratio Exceedance matrix
    :param conditional_loss_poes
      The poes taken into accout to compute the loss maps
    """

    vulnerability_model = general.fetch_vulnerability_model(job_id)
    hazard_getter = general.hazard_getter(hazard_getter, hazard_id)

    calculator = api.conditional_losses(
        conditional_loss_poes,
        api.classical(vulnerability_model, lrem_steps_per_interval))

    with transaction.commit_on_success(using='reslt_writer'):
        logs.LOG.debug(
            'launching compute_on_assets over %d assets' % len(assets))
        for asset_output in api.compute_on_assets(
            assets, hazard_getter, calculator):
            general.write_loss_curve(loss_curve_id, asset_output)
            if loss_map_ids:
                general.write_loss_map(loss_map_ids, asset_output)
classical.ignore_result = False


class ClassicalRiskCalculator(general.BaseRiskCalculator):
    """
    Classical PSHA risk calculator. Computes loss curves and loss
    params for a given set of assets.
    """

    #: The core calculation celery task function
    celery_task = classical

    @property
    def calculation_parameters(self):
        """
        The specific calculation parameters passed as kwargs to the
        celery task function
        """
        rc = self.job.risk_calculation

        return {
            'lrem_steps_per_interval': rc.lrem_steps_per_interval,
            'conditional_loss_poes': rc.conditional_loss_poes
            }

    @property
    def hazard_id(self):
        """
        The ID of the `openquake.db.models.HazardCurve` object that
        stores the hazard curves used by the risk calculation
        """
        return self.job.risk_calculation.hazard_output.hazardcurve.id
