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


class AggLossCurve(object):
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        for row in self.data:
            yield row


@export.add('dmg_per_taxonomy_xml')
def export_dmg_per_taxonomy_xml(key, export_dir, damage_states,
                                dmg_by_taxonomy):
    dest = os.path.join(export_dir, 'dmg_dist_per_taxonomy.xml')
    writer = risk_writers.DmgDistPerTaxonomyXMLWriter(dest, damage_states)
    writer.serialize(dmg_by_taxonomy)
    return dest


@export.add('agg_loss_xml')
def export_agg_loss_xml(key, export_dir, sitecol, rupture_tags, gmfs):
    """
    """
    dest = os.path.join(export_dir, 'agg_loss_curves.xml')
    risk_writers.AggregateLossCurveXMLWriter(dest, **args).serialize(
        data)
    return dest
