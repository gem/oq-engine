# Copyright (c) 2010-2013, GEM Foundation.
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
import csv

from openquake.engine.db import models
from openquake.engine.export import core
from openquake.nrmllib.risk import writers


LOSS_CURVE_FILENAME_FMT = 'loss-curves-%(loss_curve_id)s.xml'
LOSS_MAP_FILENAME_FMT = 'loss-maps-%(loss_map_id)s-poe-%(poe)s.xml'
AGGREGATE_LOSS_FILENAME_FMT = 'aggregate-loss-%s.csv'
BCR_FILENAME_FMT = 'bcr-distribution-%(bcr_distribution_id)s.xml'


# for each output_type there must be a function
# export_<output_type>(output, target_dir)
def export(output_id, target_dir):
    """
    Export the given risk calculation output from the database to the
    specified directory. See `openquake.engine.export.hazard.export` for more
    details.
    """
    output = models.Output.objects.get(id=output_id)
    return [globals().get(
        "export_%s" % output.output_type,
        core._export_fn_not_implemented)(
            output, os.path.expanduser(target_dir))]


def _export_common(output):
    """
    Returns a dict containing the common arguments used by nrml
    serializers to serialize the risk calculation `output`.
    """
    risk_calculation = output.oq_job.risk_calculation
    investigation_time = (
        risk_calculation.get_hazard_calculation().investigation_time)
    statistics, quantile_value = risk_calculation.hazard_statistics

    source_model_tree_path, gsim_tree_path = None, None

    if risk_calculation.calculation_mode != u'scenario':
        if not statistics:
            lt_paths = risk_calculation.hazard_logic_tree_paths

            if lt_paths:
                source_model_tree_path, gsim_tree_path = [
                    core.LT_PATH_JOIN_TOKEN.join(x) for x in lt_paths]

    unit = risk_calculation.exposure_model.stco_unit

    return dict(investigation_time=investigation_time,
                statistics=statistics,
                quantile_value=quantile_value,
                source_model_tree_path=source_model_tree_path,
                gsim_tree_path=gsim_tree_path,
                unit=unit)


@core.makedirs
def export_agg_loss_curve(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss curves
    serializer
    """
    args = _export_common(output)
    args['path'] = os.path.join(target_dir, LOSS_CURVE_FILENAME_FMT % {
        'loss_curve_id': output.loss_curve.id})
    writers.AggregateLossCurveXMLWriter(**args).serialize(
        output.loss_curve.aggregatelosscurvedata)
    return args['path']


@core.makedirs
def export_loss_curve(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss curves
    serializer
    """
    args = _export_common(output)
    args['path'] = os.path.join(target_dir, LOSS_CURVE_FILENAME_FMT % {
        'loss_curve_id': output.loss_curve.id})
    args['insured'] = output.loss_curve.insured

    data = output.loss_curve.losscurvedata_set.all().order_by('asset_ref')

    writers.LossCurveXMLWriter(**args).serialize(data)
    return args['path']

export_ins_loss_curve = export_loss_curve


@core.makedirs
def export_loss_map(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss map
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output)
    args.update(
        dict(path=os.path.join(target_dir, LOSS_MAP_FILENAME_FMT % {
            'loss_map_id': output.loss_map.id,
            'poe': output.loss_map.poe}),
            poe=output.loss_map.poe,
            loss_category=risk_calculation.exposure_model.category))
    writers.LossMapXMLWriter(**args).serialize(
        output.loss_map.lossmapdata_set.all().order_by('asset_ref'))
    return args['path']


@core.makedirs
def export_bcr_distribution(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml bcr distribution
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output)

    args.update(
        dict(path=os.path.join(target_dir, BCR_FILENAME_FMT % {
            'bcr_distribution_id': output.bcr_distribution.id}),
            interest_rate=risk_calculation.interest_rate,
            asset_life_expectancy=risk_calculation.asset_life_expectancy))
    del args['investigation_time']

    writers.BCRMapXMLWriter(**args).serialize(
        output.bcr_distribution.bcrdistributiondata_set.all().order_by(
            'asset_ref'))
    return args['path']


def make_dmg_dist_export(damagecls, writercls, filename):
    # XXX: clearly this is not a good approach for large exposures
    @core.makedirs
    def export_dmg_dist(output, target_dir):
        """
        Export the damage distribution identified
        by the given output to the `target_dir`.

        :param output: db output record which identifies the distribution.
        :type output: :py:class:`openquake.engine.db.models.Output`
        :param target_dir: destination directory of the exported file.
        :type target_dir: string
        """
        job = output.oq_job
        rc_id = job.risk_calculation.id
        file_path = os.path.join(target_dir, filename % job.id)
        dmg_states = list(models.DmgState.objects.filter(
            risk_calculation__id=rc_id).order_by('lsi'))
        if writercls is writers.CollapseMapXMLWriter:  # special case
            writer = writercls(file_path)
            data = damagecls.objects.filter(dmg_state=dmg_states[-1])
        else:
            writer = writercls(file_path, [ds.dmg_state for ds in dmg_states])
            data = damagecls.objects.filter(
                dmg_state__risk_calculation__id=rc_id)
        writer.serialize(data.order_by('dmg_state__lsi'))
        return file_path

    return export_dmg_dist

export_dmg_dist_per_asset = make_dmg_dist_export(
    models.DmgDistPerAsset, writers.DmgDistPerAssetXMLWriter,
    "dmg-dist-asset-%s.xml")

export_dmg_dist_per_taxonomy = make_dmg_dist_export(
    models.DmgDistPerTaxonomy, writers.DmgDistPerTaxonomyXMLWriter,
    "dmg-dist-taxonomy-%s.xml")

export_dmg_dist_total = make_dmg_dist_export(
    models.DmgDistTotal, writers.DmgDistTotalXMLWriter,
    "dmg-dist-total-%s.xml")

export_collapse_map = make_dmg_dist_export(
    models.DmgDistPerAsset, writers.CollapseMapXMLWriter,
    "collapse-map-%s.xml")


def export_aggregate_loss(output, target_dir):
    """
    Export aggregate losses in CSV
    """
    filepath = os.path.join(target_dir,
                            AGGREGATE_LOSS_FILENAME_FMT % output.id)

    with open(filepath, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['Output ID', 'Mean', 'Standard Deviation'])
        writer.writerow([output.aggregatelossdata.id,
                        output.aggregatelossdata.mean,
                        output.aggregatelossdata.std_dev])
    return filepath
