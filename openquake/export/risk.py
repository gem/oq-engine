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

"""
Functions for exporting risk artifacts from the database.
"""


import os

from openquake.db import models
from openquake.export import core
from nrml.risk import writers


LOSS_CURVE_FILENAME_FMT = 'loss-curves-%(loss_curve_id)s.xml'


def export(output_id, target_dir):
    output = models.Output.objects.get(id=output_id)
    export_fn = _export_fn_map().get(
        output.output_type, core._export_fn_not_implemented)

    return export_fn(output, os.path.expanduser(target_dir))


def _export_fn_map():
    fn_map = {
        'loss_curve': export_loss_curve,
        }
    return fn_map


@core.makedirs
def export_loss_curve(output, target_dir):
    risk_calculation = output.oq_job.risk_calculation
    investigation_time = risk_calculation.hazard_calculation.investigation_time
    statistics, quantile_value = risk_calculation.hazard_statistics()

    source_model_tree_path, gsim_tree_path = None, None
    if not statistics:
        source_model_tree_path, gsim_tree_path = (
            risk_calculation.hazard_logic_tree_paths())

    [exposure_input] = models.inputs4rcalc(risk_calculation, "exposure")

    path = os.path.join(target_dir, LOSS_CURVE_FILENAME_FMT % {
        'loss_curve_id': output.losscurve.id})

    writer = writers.LossCurveXMLWriter(
        path,
        investigation_time,
        core.LT_PATH_JOIN_TOKEN.join(source_model_tree_path),
        core.LT_PATH_JOIN_TOKEN.join(gsim_tree_path),
        statistics, quantile_value,
        exposure_input.exposuremodel.stco_unit)

    writer.serialize(output.losscurve.losscurvedata_set.all())
    return [path]
