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


import os

from nrml import writers as nrml_writers

from openquake.db import models
from openquake.export.core import makedirs


HAZARD_CURVES_FILENAME_FMT = 'hazard-curves-%(hazard_curve_id)s.xml'
#: Used to separate node labels in a logic tree path
LT_PATH_JOIN_TOKEN = '|'


@makedirs
def export_hazard_curves(output, target_dir):
    """
    Export the specified hazard curve ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` of type `hazard_curve`.
    :param str target_dir:
        Destination directory location of exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    hc = models.HazardCurve.objects.get(output=output.id)
    hcd = models.HazardCurveData.objects.filter(hazard_curve=hc.id)

    filename = HAZARD_CURVES_FILENAME_FMT % dict(hazard_curve_id=hc.id)
    path = os.path.abspath(os.path.join(target_dir, filename))

    if hc.lt_realization is not None:
        # If the curves are for a specified logic tree realization,
        # get the tree paths
        lt_rlz = hc.lt_realization
        smlt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:
        # These curves must be statistical aggregates
        smlt_path = None
        gsimlt_path = None

    metadata = {
        'statistics': hc.statistics,
        'smlt_path': smlt_path,
        'gsimlt_path': gsimlt_path,
        'sa_period': hc.sa_period,
        'sa_damping': hc.sa_damping,
    }
    writer = nrml_writers.HazardCurveXMLWriter(
        path, hc.investigation_time, hc.imt, hc.imls, **metadata)
    writer.serialize(hcd)

    return [path]
