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
from openquake.output.risk import (
    AggregateLossCurveXMLWriter, LossCurveXMLWriter)
from openquake.output.scenario_damage import (
DmgDistPerAssetXMLWriter, DmgDistPerTaxonomyXMLWriter, DmgDistTotalXMLWriter)


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
    filename = 'loss-ratio-curve-%s.xml' % output.id
    path = os.path.abspath(os.path.join(target_dir, filename))
    writer = LossCurveXMLWriter(path)

    loss_curves = models.LossCurveData.objects.filter(
        loss_curve__output=output.id)
    writer.serialize(loss_curves)
    return [path]


@core.makedirs
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


@core.makedirs
def export_dmg_dist_per_asset(output, target_dir):
    """
    Export the damage distribution per asset identified
    by the given output to the `target_dir`.

    :param output: db output record which identifies the distribution.
    :type output: :py:class:`openquake.db.models.Output`
    :param target_dir: destination directory of the exported file.
    :type target_dir: string
    """

    file_name = "dmg-dist-asset-%s.xml" % output.oq_job.id
    file_path = os.path.join(target_dir, file_name)

    dda = models.DmgDistPerAsset.objects.get(output=output)
    writer = DmgDistPerAssetXMLWriter(
        file_path, dda.end_branch_label, dda.dmg_states)

    data = models.DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda)
    writer.serialize(data)

    return [file_path]


@core.makedirs
def export_dmg_dist_per_taxonomy(output, target_dir):
    """
    Export the damage distribution per taxonomy identified
    by the given output to the `target_dir`.

    :param output: db output record which identifies the distribution.
    :type output: :py:class:`openquake.db.models.Output`
    :param target_dir: destination directory of the exported file.
    :type target_dir: string
    """

    file_name = "dmg-dist-taxonomy-%s.xml" % output.oq_job.id
    file_path = os.path.join(target_dir, file_name)

    ddt = models.DmgDistPerTaxonomy.objects.get(output=output)
    writer = DmgDistPerTaxonomyXMLWriter(
        file_path, ddt.end_branch_label, ddt.dmg_states)

    data = models.DmgDistPerTaxonomyData.objects.filter(
        dmg_dist_per_taxonomy=ddt)

    writer.serialize(data)

    return [file_path]


@core.makedirs
def export_dmg_dist_total(output, target_dir):
    """
    Export the total damage distribution identified
    by the given output to the `target_dir`.

    :param output: db output record which identifies the distribution.
    :type output: :py:class:`openquake.db.models.Output`
    :param target_dir: destination directory of the exported file.
    :type target_dir: string
    """

    file_name = "dmg-dist-total-%s.xml" % output.oq_job.id
    file_path = os.path.join(target_dir, file_name)

    ddt = models.DmgDistTotal.objects.get(output=output)
    writer = DmgDistTotalXMLWriter(
        file_path, ddt.end_branch_label, ddt.dmg_states)

    data = models.DmgDistTotalData.objects.filter(
        dmg_dist_total=ddt)

    writer.serialize(data)

    return [file_path]
