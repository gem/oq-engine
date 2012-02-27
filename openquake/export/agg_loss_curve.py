# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import os

from openquake.db import models
from openquake.export.core import makedirs


#@makedirs
def export_agg_loss_curve(output, target_dir):
    file_name = 'aggregate_loss_curve.xml'
    file_path = os.path.join(target_dir, file_name)

    agg_loss_curve = models.AggregateLossCurveData.objects.get(
        loss_curve__output=output.id)
    print agg_loss_curve

    return [file_path]
