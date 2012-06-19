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
from openquake.export.core import makedirs
from openquake.output.risk import AggregateLossCurveXMLWriter
from openquake.output.scenario_damage import DmgDistPerAssetXMLWriter
from openquake.output.scenario_damage import DmgDistPerTaxonomyXMLWriter
from openquake.output.scenario_damage import DmgDistTotalXMLWriter
from openquake.output.scenario_damage import CollapseMapXMLWriter


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


@makedirs
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


@makedirs
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


@makedirs
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


@makedirs
def export_collapse_map(output, target_dir):
    """
    Export the collapse map identified
    by the given output to the `target_dir`.

    :param output: db output record which identifies the distribution.
    :type output: :py:class:`openquake.db.models.Output`
    :param target_dir: destination directory of the exported file.
    :type target_dir: string
    """

    file_name = "collapse-map-%s.xml" % output.oq_job.id
    file_path = os.path.join(target_dir, file_name)

    cm = models.CollapseMap.objects.get(output=output)
    writer = CollapseMapXMLWriter(file_path, None)

    data = models.CollapseMapData.objects.filter(
        collapse_map=cm)

    writer.serialize(data)

    return [file_path]
