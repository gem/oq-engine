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

from openquake.baselib.general import AccumDict
from openquake.commonlib.export import export
from openquake.commonlib import writers, risk_writers
from openquake.commonlib.writers import scientificformat


@export.add(('dmg_dist_per_asset', 'xml'), ('dmg_dist_per_taxonomy', 'xml'),
            ('dmg_dist_total', 'xml'), ('collapse_map', 'xml'))
def export_dmg_xml(key, export_dir, damage_states, dmg_data):
    dest = os.path.join(export_dir, '%s.%s' % key)
    risk_writers.DamageWriter(damage_states).to_nrml(key[0], dmg_data, dest)
    return AccumDict({key: dest})


@export.add(('agg_loss', 'csv'))
def export_agg_loss_csv(key, export_dir, aggcurves):
    """
    Export aggregate losses in CSV.

    :param key: 'agg_loss_csv'
    :param export_dir: the export directory
    :param aggcurves: a list [(loss_type, unit, mean, stddev), ...]
    """
    dest = os.path.join(export_dir, '%s.%s' % key)
    header = ['LossType', 'Unit', 'Mean', 'Standard Deviation']
    writers.save_csv(dest, [header] + aggcurves)
    return AccumDict({key: dest})


@export.add(('classical_damage', 'csv'))
def export_classical_damage_csv(key, export_dir, fname, damage_states,
                                fractions_by_asset):
    """
    Export damage fractions in CSV.

    :param key: 'classical_damage_csv'
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
    return AccumDict({key: dest})
