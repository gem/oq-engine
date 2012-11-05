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
    # TODO (lp) implement writer in nrml lib
    # filename = 'loss-ratio-curve-%s.xml' % output.id
    # path = os.path.abspath(os.path.join(target_dir, filename))
    # writer = LossCurveXMLWriter(path)
    # loss_curves = models.LossCurveData.objects.filter(
    #     loss_curve__output=output.id)
    # writer.serialize(loss_curves)
    # return [path]

    raise NotImplementedError
