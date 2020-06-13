# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import json
try:
    import fiona
    from fiona import crs
except ImportError:
    fiona = None


def geodict(row):
    """
    Convert a namedtuple with .geom, .coords fields into a geojson
    """
    prop = {}
    for f in row._fields:
        if f not in ('geom', 'coords'):
            val = getattr(row, f)
            prop[f] = json.dumps(val) if isinstance(val, list) else val
    return {'geometry': {'type': row.geom.replace('3D ', ''),
                         'coordinates': row.coords},
            'properties': prop}


def fiona_type(value):
    if isinstance(value, int):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    return 'str'


class GeoPackager(object):
    """
    An utility to store homogeneous lists of namedtuples as layers
    """
    def __init__(self, fname):
        if not fiona:
            raise ImportError('fiona')
        self.fname = fname
        self.crs = crs.from_string('+proj=longlat +ellps=WGS84 '
                                   '+datum=WGS84 +no_defs')

    def save_layer(self, name, rows):
        """
        :param name:
            layer name
        :param rows:
            a non-empty list of objects with attributes .geom, .coords
        """
        row = rows[0]
        properties = [(f, fiona_type(getattr(row, f))) for f in row._fields
                      if f not in ('geom', 'coords')]
        schema = {'geometry': row.geom, 'properties': properties}
        with fiona.open(self.fname, 'w', 'GPKG', schema,
                        self.crs, 'utf8', layer=name) as f:
            recs = [geodict(row) for row in rows]
            f.writerecords(recs)

    def _save(self, name, dic):
        # Useful for debugging. Example:
        # dic = {'geometry':
        #          {'type': 'Polygon',
        #           'coordinates': [[(-0.5, -0.5), (-0.3, -0.1),
        #                            (0.1, 0.2), (0.3, -0.8), (-0.5, -0.5)]},
        #        'properties': {'id': '1', 'name': 'Area Source'}}
        schema = {'geometry': dic['geometry']['type'],
                  'properties': [(k, fiona_type(v))
                                 for k, v in dic['properties'].items()]}
        with fiona.open(self.fname, 'w', 'GPKG', schema,
                        self.crs, 'utf8', layer=name) as f:
            f.write(dic)
