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
LOSS_MAP_FILENAME_FMT = 'loss-maps-%(loss_map_id)s.%(file_ext)s'
LOSS_FRACTION_FILENAME_FMT = 'loss-fractions-%(loss_fraction_id)s.xml'
AGGREGATE_LOSS_FILENAME_FMT = 'aggregate-loss-%s.csv'
BCR_FILENAME_FMT = 'bcr-distribution-%(bcr_distribution_id)s.xml'
EVENT_LOSS_FILENAME_FMT = 'event-loss-%s.csv'


# for each output_type there must be a function
# export_<output_type>_<export_type>(output, target_dir)
def export(output_id, target_dir, export_type='xml'):
    """
    Export the given risk calculation output from the database to the
    specified directory. See :func:`openquake.engine.export.hazard.export` for
    more details.
    """
    output = models.Output.objects.get(id=output_id)

    try:
        export_fn = EXPORTERS[export_type][output.output_type]
    except KeyError:
        raise NotImplementedError(
            'No "%(fmt)s" exporter is available for "%(output_type)s"'
            ' outputs' % dict(fmt=export_type, output_type=output.output_type)
        )

    return export_fn(output, os.path.expanduser(target_dir))


def _export_common(output, loss_type):
    """
    Returns a dict containing the output metadata which are serialized
    by nrml writers before actually writing the `output` data.
    """
    metadata = output.hazard_metadata
    if metadata.sm_path is not None:
        source_model_tree_path = core.LT_PATH_JOIN_TOKEN.join(
            metadata.sm_path)
    else:
        source_model_tree_path = None
    if metadata.gsim_path is not None:
        gsim_tree_path = core.LT_PATH_JOIN_TOKEN.join(metadata.gsim_path)
    else:
        gsim_tree_path = None

    return dict(investigation_time=metadata.investigation_time,
                statistics=metadata.statistics,
                quantile_value=metadata.quantile,
                source_model_tree_path=source_model_tree_path,
                gsim_tree_path=gsim_tree_path,
                unit=output.oq_job.risk_calculation.exposure_model.unit(
                    loss_type))


@core.makedirsdeco
def export_agg_loss_curve_xml(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss curves
    serializer
    """
    args = _export_common(output, output.loss_curve.loss_type)
    dest = os.path.join(
        target_dir,
        LOSS_CURVE_FILENAME_FMT % {'loss_curve_id': output.loss_curve.id}
    )
    writers.AggregateLossCurveXMLWriter(dest, **args).serialize(
        output.loss_curve.aggregatelosscurvedata)
    return dest


@core.makedirsdeco
def export_loss_curve_xml(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss curves
    serializer
    """
    args = _export_common(output, output.loss_curve.loss_type)
    dest = os.path.join(target_dir, LOSS_CURVE_FILENAME_FMT % {
        'loss_curve_id': output.loss_curve.id})
    args['insured'] = output.loss_curve.insured

    data = output.loss_curve.losscurvedata_set.all().order_by('asset_ref')

    writers.LossCurveXMLWriter(dest, **args).serialize(data)
    return dest


def _export_loss_map(output, target_dir, writer_class, file_ext):
    """
    General loss map export code.
    """
    core.makedirs(target_dir)

    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.loss_map.loss_type)

    dest = os.path.join(
        target_dir,
        LOSS_MAP_FILENAME_FMT % {'loss_map_id': output.loss_map.id,
                                 'file_ext': file_ext}
    )

    args.update(dict(
        poe=output.loss_map.poe,
        loss_category=risk_calculation.exposure_model.category))
    writer = writer_class(dest, **args)
    writer.serialize(
        output.loss_map.lossmapdata_set.all().order_by('asset_ref')
    )
    return dest


def export_loss_map_xml(output, target_dir):
    """
    Serialize a loss map to NRML/XML.
    """
    return _export_loss_map(output, target_dir, writers.LossMapXMLWriter,
                            'xml')


def export_loss_map_geojson(output, target_dir):
    """
    Serialize a loss map to geojson.
    """
    return _export_loss_map(output, target_dir, writers.LossMapGeoJSONWriter,
                            'geojson')


@core.makedirsdeco
def export_loss_fraction_xml(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml loss fractions
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.loss_fraction.loss_type)
    hazard_metadata = models.Output.HazardMetadata(
        investigation_time=args['investigation_time'],
        statistics=args['statistics'],
        quantile=args.get('quantile_value'),
        sm_path=args['source_model_tree_path'],
        gsim_path=args['gsim_tree_path'])
    path = os.path.join(
        target_dir,
        LOSS_FRACTION_FILENAME_FMT % {
            'loss_fraction_id': output.loss_fraction.id})
    poe = output.loss_fraction.poe
    variable = output.loss_fraction.variable
    loss_category = risk_calculation.exposure_model.category

    writers.LossFractionsWriter(
        path, variable, args['unit'],
        loss_category, hazard_metadata, poe).serialize(
            output.loss_fraction.total_fractions(), output.loss_fraction)
    return path


@core.makedirsdeco
def export_bcr_distribution_xml(output, target_dir):
    """
    Export `output` to `target_dir` by using a nrml bcr distribution
    serializer
    """
    risk_calculation = output.oq_job.risk_calculation
    args = _export_common(output, output.bcr_distribution.loss_type)

    dest = os.path.join(
        target_dir,
        BCR_FILENAME_FMT % {'bcr_distribution_id': output.bcr_distribution.id},
    )
    args.update(
        dict(interest_rate=risk_calculation.interest_rate,
             asset_life_expectancy=risk_calculation.asset_life_expectancy))
    del args['investigation_time']

    writers.BCRMapXMLWriter(dest, **args).serialize(
        output.bcr_distribution.bcrdistributiondata_set.all().order_by(
            'asset_ref'))
    return dest


def make_dmg_dist_export(damagecls, writercls, filename):
    # XXX: clearly this is not a good approach for large exposures
    @core.makedirsdeco
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


export_dmg_dist_per_asset_xml = make_dmg_dist_export(
    models.DmgDistPerAsset, writers.DmgDistPerAssetXMLWriter,
    "dmg-dist-asset-%s.xml")


export_dmg_dist_per_taxonomy_xml = make_dmg_dist_export(
    models.DmgDistPerTaxonomy, writers.DmgDistPerTaxonomyXMLWriter,
    "dmg-dist-taxonomy-%s.xml")


export_dmg_dist_total_xml = make_dmg_dist_export(
    models.DmgDistTotal, writers.DmgDistTotalXMLWriter,
    "dmg-dist-total-%s.xml")


export_collapse_map_xml = make_dmg_dist_export(
    models.DmgDistPerAsset, writers.CollapseMapXMLWriter,
    "collapse-map-%s.xml")


def export_aggregate_loss_csv(output, target_dir):
    """
    Export aggregate losses in CSV
    """
    filepath = os.path.join(target_dir,
                            AGGREGATE_LOSS_FILENAME_FMT % (
                                output.aggregate_loss.id))

    with open(filepath, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['Mean', 'Standard Deviation'])
        writer.writerow([output.aggregate_loss.mean,
                        output.aggregate_loss.std_dev])
    return filepath

export_aggregate_loss = export_aggregate_loss_csv


def export_event_loss_csv(output, target_dir):
    """
    Export Event Loss Table in CSV format
    """

    filepath = os.path.join(target_dir,
                            EVENT_LOSS_FILENAME_FMT % (
                                output.id))

    with open(filepath, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Rupture', 'Magnitude', 'Aggregate Loss'])

        for event_loss in models.EventLossData.objects.filter(
                event_loss__output=output).select_related().order_by(
                    '-aggregate_loss'):
            writer.writerow(["%7d" % event_loss.rupture.id,
                             "%.07f" % event_loss.rupture.magnitude,
                             "%.07f" % event_loss.aggregate_loss])
    return filepath


XML_EXPORTERS = {
    'agg_loss_curve': export_agg_loss_curve_xml,
    'bcr_distribution': export_bcr_distribution_xml,
    'collapse_map': export_collapse_map_xml,
    'dmg_dist_per_asset': export_dmg_dist_per_asset_xml,
    'dmg_dist_per_taxonomy': export_dmg_dist_per_taxonomy_xml,
    'dmg_dist_total': export_dmg_dist_total_xml,
    'loss_curve': export_loss_curve_xml,
    'loss_fraction': export_loss_fraction_xml,
    'loss_map': export_loss_map_xml,
    # TODO(LB):
    # There are two exceptions; aggregate_loss and event_loss can only be
    # exported in CSV format.
    # We should re-think the way we're handling the export cases.
    'aggregate_loss': export_aggregate_loss_csv,
    'event_loss': export_event_loss_csv,
}
GEOJSON_EXPORTERS = {
    'loss_map': export_loss_map_geojson,
}
EXPORTERS = {
    'xml': XML_EXPORTERS,
    'geojson': GEOJSON_EXPORTERS,
}
