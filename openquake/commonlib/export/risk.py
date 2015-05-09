#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import operator
import collections

import numpy

from openquake.baselib.general import AccumDict
from openquake.commonlib.export import export, ds_export
from openquake.commonlib import writers, risk_writers, riskmodels
from openquake.commonlib.writers import scientificformat
from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)
from openquake.risklib import scientific


# ########################## utility functions ############################## #

def compose_arrays(a1, a2):
    """
    Compose composite arrays by generating an extended datatype containing
    all the fields. The two arrays must have the same shape.
    """
    fields1 = [(f, dt[0]) for f, dt in a1.dtype.fields.items()]
    fields2 = [(f, dt[0]) for f, dt in a2.dtype.fields.items()]
    composite = numpy.zeros(a1.shape, numpy.dtype(fields1 + fields2))
    for f1 in dict(fields1):
        composite[f1] = a1[f1]
    for f2 in dict(fields2):
        composite[f2] = a2[f2]
    return composite


def get_assets(dstore):
    """
    :param dstore: a datastore with a key `specific_assets`
    :returns: an ordered array of records (asset_ref, lon, lat)
    """
    assets = dstore['specific_assets']  # they are already ordered by ID
    asset_dt = numpy.dtype(
        [('asset_ref', str, 20), ('lon', float), ('lat', float)])
    asset_data = numpy.array(
        [(asset.id, asset.location[0], asset.location[1])
         for asset in assets], asset_dt)
    return asset_data


# ############################### exporters ############################## #

# this is used by classical_risk from csv
@ds_export.add(('avg_losses', 'h5', 'csv'))
def ds_export_avg_losses(ekey, dstore):
    avg_losses = dstore[ekey[:-1]]
    rlzs = dstore['rlzs_assoc'].realizations
    assets = get_assets(dstore)
    columns = 'asset_ref lon lat avg'.split()
    fnames = []
    for rlz, losses in zip(rlzs, avg_losses):
        dest = os.path.join(
            dstore.export_dir, 'rlz-%03d-avg_loss.csv' % rlz.ordinal)
        data = compose_arrays(assets, losses)
        writers.write_csv(dest, data, fmt='%11.7E', header=columns)
        fnames.append(dest)
    return fnames


@ds_export.add(
    ('loss_curves', 'individual', 'hdf5', 'csv'),
    ('loss_curves', 'stats', 'hdf5', 'csv'),
    ('loss_maps', 'individual', 'hdf5', 'csv'),
    ('loss_maps', 'stats', 'hdf5', 'csv'))
def ds_export_loss_curves(ekey, dstore):
    assets = get_assets(dstore)
    rlzs = dstore['rlzs_assoc'].realizations
    rlz_by_dset = {rlz.uid: rlz for rlz in rlzs}
    fnames = []
    if ekey[0] == 'loss_curves':
        columns = 'asset_ref lon lat losses poes avg'.split()
    elif ekey[0] == 'loss_maps':
        columns = None
    for dset, curves_by_lt in dstore[ekey[:-1]]:
        if dset in rlz_by_dset:
            prefix = 'rlz-%03d' % rlz_by_dset[dset].ordinal
        else:
            prefix = dset
        for loss_type in curves_by_lt.dtype.fields:
            curves = compose_arrays(
                assets, curves_by_lt[loss_type])
            dest = os.path.join(
                dstore.export_dir, '%s-%s-%s.csv' %
                (prefix, loss_type, ekey[0]))
            writers.write_csv(dest, curves, fmt='%10.6E', header=columns)
            fnames.append(dest)
    return fnames


@ds_export.add(('agg_loss_curve', 'individual', 'hdf5', 'csv'),
               ('agg_loss_curve', 'stats', 'hdf5', 'csv'))
def ds_export_agg_loss_curve(ekey, dstore):
    rlzs = dstore['rlzs_assoc'].realizations
    rlz_by_dset = {rlz.uid: rlz for rlz in rlzs}
    fnames = []
    columns = 'losses poes avg'.split()
    for dset, loss_curve_by_lt in dstore[ekey[:-1]]:
        if dset in rlz_by_dset:
            prefix = 'rlz-%03d' % rlz_by_dset[dset].ordinal
        else:
            prefix = dset
        for loss_type in loss_curve_by_lt.dtype.fields:
            loss_curve = loss_curve_by_lt[loss_type]
            dest = os.path.join(
                dstore.export_dir, '%s-%s-%s.csv' %
                (prefix, loss_type, ekey[0]))
            writers.write_csv(dest, loss_curve, fmt='%10.6E', header=columns)
            fnames.append(dest)
    return fnames


@ds_export.add(
    ('event_loss', 'individual', 'csv'),
    ('event_loss_asset', 'individual', 'csv'))
def ds_export_event_loss(ekey, dstore):
    name, kind, fmt = ekey
    fnames = []
    for i, data in enumerate(dstore[ekey[:-1]]):
        for loss_type in data.dtype.fields:
            dest = os.path.join(
                dstore.export_dir, 'rlz-%03d-%s-%s.csv' % (i, loss_type, name))
            writers.write_csv(dest, sorted(data[loss_type]), fmt='%10.6E')
            fnames.append(dest)
    return fnames


# TODO: the export is doing too much; probably we should store
# a better data structure
@ds_export.add(('damages_by_key', 'xml'))
def export_damage(ekey, dstore):
    oqparam = dstore['oqparam']
    riskmodel = dstore['riskmodel']
    rlzs = dstore['rlzs_assoc'].realizations
    damages_by_key = dstore['damages_by_key']
    dmg_states = [DmgState(s, i)
                  for i, s in enumerate(riskmodel.damage_states)]
    fnames = []
    for i in sorted(damages_by_key):
        rlz = rlzs[i]
        result = damages_by_key[i]
        dd_taxo = []
        dd_asset = []
        shape = oqparam.number_of_ground_motion_fields, len(dmg_states)
        totals = numpy.zeros(shape)  # R x D matrix
        for (key_type, key), values in result.iteritems():
            if key_type == 'taxonomy':
                # values are fractions, R x D matrix
                totals += values
                means, stds = scientific.mean_std(values)
                for dmg_state, mean, std in zip(dmg_states, means, stds):
                    dd_taxo.append(
                        DmgDistPerTaxonomy(key, dmg_state, mean, std))
            elif key_type == 'asset':
                means, stddevs = values
                for dmg_state, mean, std in zip(dmg_states, means, stddevs):
                    dd_asset.append(
                        DmgDistPerAsset(
                            ExposureData(key.id, Site(*key.location)),
                            dmg_state, mean, std))
        dd_total = []
        for dmg_state, total in zip(dmg_states, totals.T):
            mean, std = scientific.mean_std(total)
            dd_total.append(DmgDistTotal(dmg_state, mean, std))

        suffix = '' if rlz.uid == '*' else '-gsimltp_%s' % rlz.uid
        f1 = export(('dmg_dist_per_asset', 'xml'), oqparam.export_dir,
                    dmg_states, dd_asset, suffix)
        f2 = export(('dmg_dist_per_taxonomy', 'xml'),
                    oqparam.export_dir, dmg_states, dd_taxo, suffix)
        f3 = export(('dmg_dist_total', 'xml'), oqparam.export_dir,
                    dmg_states, dd_total, suffix)
        max_damage = dmg_states[-1]
        # the collapse map is extracted from the damage distribution per asset
        # (dda) by taking the value corresponding to the maximum damage
        collapse_map = [dda for dda in dd_asset if dda.dmg_state == max_damage]
        f4 = export(('collapse_map', 'xml'), oqparam.export_dir,
                    dmg_states, collapse_map, suffix)
        fnames.extend(sum((f1 + f2 + f3 + f4).values(), []))
    return sorted(fnames)


@export.add(('dmg_dist_per_asset', 'xml'), ('dmg_dist_per_taxonomy', 'xml'),
            ('dmg_dist_total', 'xml'), ('collapse_map', 'xml'))
def export_dmg_xml(key, export_dir, damage_states, dmg_data, suffix):
    """
    Export damage outputs in XML format.

    :param key:
        dmg_dist_per_asset|dmg_dist_per_taxonomy|dmg_dist_total|collapse_map
    :param export_dir:
        the export directory
    :param data:
        a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix:
        a suffix specifying the GSIM realization
    """
    dest = os.path.join(export_dir, '%s%s.%s' % (key[0], suffix, key[1]))
    risk_writers.DamageWriter(damage_states).to_nrml(key[0], dmg_data, dest)
    return AccumDict({key: [dest]})


@export.add(('asset-loss', 'csv'), ('asset-ins', 'csv'))
def export_asset_loss_csv(key, export_dir, data, suffix):
    """
    Export aggregate losses in CSV.

    :param key: per_asset_loss|asset-ins
    :param export_dir: the export directory
    :param data: a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix: a suffix specifying the GSIM realization
    """
    dest = os.path.join(export_dir, '%s%s.%s' % (key[0], suffix, key[1]))
    header = ['LossType', 'Unit', 'Asset', 'Mean', 'Standard Deviation']
    data.sort(key=operator.itemgetter(2))  # order by asset_ref
    writers.save_csv(dest, [header] + data, fmt='%11.7E')
    return AccumDict({key: [dest]})


@export.add(('agg', 'csv'), ('ins', 'csv'))
def export_agg_loss_csv(key, export_dir, aggcurves, suffix):
    """
    Export aggregate losses in CSV.

    :param key: agg|ins
    :param export_dir: the export directory
    :param aggcurves: a list [(loss_type, unit, mean, stddev), ...]
    :param suffix: a suffix specifying the GSIM realization
    """
    dest = os.path.join(export_dir, '%s%s.%s' % (key[0], suffix, key[1]))
    header = ['LossType', 'Unit', 'Mean', 'Standard Deviation']
    writers.save_csv(dest, [header] + aggcurves, fmt='%11.7E')
    return AccumDict({key: [dest]})


@ds_export.add(('damages_by_rlz', 'csv'))
def ds_export_classical_damage_csv(ekey, dstore):
    damages_by_rlz = dstore['damages_by_rlz']
    rlzs = dstore['rlzs_assoc'].realizations
    damage_states = dstore['riskmodel'].damage_states
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    fnames = []
    for rlz in rlzs:
        damages = damages_by_rlz[rlz.ordinal]
        fname = 'damage_%d.csv' % rlz.ordinal
        fnames.append(
            export_classical_damage_csv(
                dstore.export_dir, fname, dmg_states, damages))
    return fnames


def export_classical_damage_csv(export_dir, fname, damage_states,
                                fractions_by_asset):
    """
    Export damage fractions in CSV.

    :param export_dir: the export directory
    :param fname: the name of the exported file
    :param damage_states: the damage states
    :fractions_by_asset: a dictionary with the fractions by asset
    """
    dest = os.path.join(export_dir, fname)
    with open(dest, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', lineterminator='\n')
        writer.writerow(['asset_ref'] + [ds.dmg_state for ds in damage_states])
        for asset in sorted(fractions_by_asset):
            writer.writerow(
                [asset.id] + map(scientificformat, fractions_by_asset[asset]))
    return dest


# exports for scenario_risk

AggLoss = collections.namedtuple(
    'AggLoss', 'loss_type unit mean stddev')

PerAssetLoss = collections.namedtuple(  # the loss map
    'PerAssetLoss', 'loss_type unit asset_ref mean stddev')


@ds_export.add(('losses_by_key', 'csv'))
def export_risk(ekey, dstore):
    """
    Export the loss curves of a given realization in CSV format.
    """
    oqparam = dstore['oqparam']
    unit_by_lt = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                  for ct in dstore['cost_types']}
    unit_by_lt['fatalities'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    losses_by_key = dstore['losses_by_key']
    fnames = []
    for i in sorted(losses_by_key):
        rlz = rlzs[i]
        result = losses_by_key[i]
        suffix = '' if rlz.uid == '*' else '-gsimltp_%s' % rlz.uid
        losses = AccumDict()
        for key, values in result.iteritems():
            key_type, loss_type = key
            unit = unit_by_lt[loss_type]
            if key_type in ('agg', 'ins'):
                mean, std = scientific.mean_std(values)
                losses += {key_type: [
                    AggLoss(loss_type, unit, mean, std)]}
            else:
                losses += {key_type: [
                    PerAssetLoss(loss_type, unit, *vals) for vals in values]}
        for key_type in losses:
            out = export((key_type, 'csv'),
                         oqparam.export_dir, losses[key_type], suffix)
            fnames.extend(out.values()[0])
    return sorted(fnames)
