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
from openquake.lite.export import export
from openquake.commonlib import risk_writers

writercls = dict(
    dmg_per_asset_xml=risk_writers.DmgDistPerAssetXMLWriter,
    dmg_per_taxonomy_xml=risk_writers.DmgDistPerTaxonomyXMLWriter,
    dmg_total_xml=risk_writers.DmgDistTotalXMLWriter)


@export.add('dmg_per_asset_xml', 'dmg_per_taxonomy_xml', 'dmg_total_xml')
def export_dmg_xml(key, export_dir, damage_states, dmg_data):
    dest = os.path.join(export_dir, key.replace('_xml', '.xml'))
    writercls[key](dest, damage_states).serialize(dmg_data)
    return dest


@export.add('agg_loss_xml')
def export_agg_loss_xml(key, export_dir, loss_type, unit, agg_loss_curve):
    dest = os.path.join(export_dir, key=key.replace('_xml', '.xml'))
    risk_writers.AggregateLossCurveXMLWriter(
        dest, investigation_time=0, loss_type=loss_type, unit=unit,
    ).serialize(agg_loss_curve)
    return dest
