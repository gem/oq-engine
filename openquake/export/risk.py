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


"""Functions for exporting Risk artifacts from the database."""


import os

from openquake.db import models
from openquake.export.core import makedirs
from openquake.output.risk import AggregateLossCurveXMLWriter


@makedirs
def export_agg_loss_curve(output, target_dir):
    """Export the specified aggregate loss curve ``output`` to the
    ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` associated with the aggregate loss
        curve results.
    :param str target_dir:
        Destination directory location of the exported files.
    """

    file_name = 'aggregate_loss_curve.xml'
    file_path = os.path.join(target_dir, file_name)

    agg_loss_curve = models.AggregateLossCurveData.objects.get(
        loss_curve__output=output.id)

    agg_lc_writer = AggregateLossCurveXMLWriter(file_path)
    agg_lc_writer.serialize(agg_loss_curve.losses, agg_loss_curve.poes)

    return [file_path]
