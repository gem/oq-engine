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
from openquake.calculators.risk import hazard_getters
from openquake.utils import tasks
from openquake.db import models
from risklib import api


@tasks.oqtask
def classical(job_id, asset_ids, hazard_getter):
    job = models.OqJob.objects.get(job_id)
    rc = job.risk_calculation

    model = models.VulnerabilityModel.objects.get_from_job(job).to_risklib()
    assets = models.ExposureData.objects.filter(id__in=asset_ids)

    hazard_getter_class = hazard_getters.HAZARD_GETTERS[hazard_getter]
    hazard_getter = hazard_getter_class(rc.hazard_curve_id)

    calculator = api.conditional_losses(
        rc.conditional_loss_poes,
        api.classical(model, rc.lrem_steps_per_interval))

    for asset_output in api.compute_on_assets(
            assets, hazard_getter, calculator):
        print asset_output


class ClassicalRiskCalculator(general.BaseRiskCalculator):
    celery_task = classical
