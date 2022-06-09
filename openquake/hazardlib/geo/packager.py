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
import ast
import json
try:
    import fiona
    from fiona import crs
except ImportError:
    fiona = None
from openquake.baselib.node import Node
from openquake.hazardlib import nrml


def geodict(row):
    """
    Convert a namedtuple with .geom, .coords fields into a geojson
    """
    prop = {}
    for f in row.__class__.__annotations__:
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


def build_nodes(props):
    [(mfd, dic)] = ast.literal_eval(props['mfd']).items()
    mfd_dic = {k.replace('_', ''): v for k, v in dic.items()}
    msr = Node('magScaleRel', text=props['magscalerel'])
    rar = Node('ruptAspectRatio', text=props['ruptaspectratio'])
    mfd = Node(mfd, mfd_dic)
    npd = ast.literal_eval(props['nodalplanedist'])
    npd = Node('nodalPlaneDist', nodes=[Node('nodalPlane', dic)
                                        for dic in npd])
    hdd = ast.literal_eval(props['hypodepthdist'])
    hdd = Node('hypoDepthDist', nodes=[Node('hypoDepth', dic)
                                       for dic in hdd])
    return msr, rar, mfd, npd, hdd


def edge(name, coords):
    return Node(name + 'Edge', nodes=[
        Node('LineString', nodes=[Node('posList', text=coords)])])


def build_edges(coords):
    return ([edge('faultTop', coords[0])] +
            [edge('intermediate', c) for c in coords[1:-1]] +
            [edge('faultBottom', coords[-1])])


def geodic2node(geodic):
    """
    Convert a geojson dictionary into a Node object suitable for conversion
    into NRML format.
    """
    coords = geodic['geometry']['coordinates']
    props = geodic['properties']
    code = props['code']
    attr = dict(id=props['id'], name=props['name'],
                tectonicRegion=props['tectonicregion'])
    if code == 'P':
        point = Node('Point', nodes=[Node('pos', text=coords)])
        usd = Node('upperSeismoDepth', text=props['upperseismodepth'])
        lsd = Node('lowerSeismoDepth', text=props['lowerseismodepth'])
        nodes = [Node('pointGeometry', nodes=[point, usd, lsd])]
        nodes.extend(build_nodes(props))
        return Node('pointSource', attr, nodes=nodes)
    elif code == 'C':
        cplx = Node('complexFaultGeometry', nodes=build_edges(coords))
        nodes = (cplx,) + build_nodes(props)
        return Node('complexFaultSource', attr, nodes=nodes)
    elif code == 'A':
        pol = Node('Polygon', nodes=[
            Node('exterior', nodes=[
                Node('LinearRing', nodes=[
                    Node('posList', text=coords)])])])
        usd = Node('upperSeismoDepth', text=props['upperseismodepth'])
        lsd = Node('lowerSeismoDepth', text=props['lowerseismodepth'])
        area = Node('areaGeometry', nodes=[pol, usd, lsd])
        nodes = (area,) + build_nodes(props)
        return Node('areaSource', attr, nodes=nodes)
    elif code == 'S':
        splx = Node('simpleFaultGeometry', nodes=[
            Node('LineString', nodes=[Node('posList', text=coords)])])
        nodes = (splx,) + build_nodes(props)
        return Node('simpleFaultSource', attr, nodes=nodes)
    else:
        return Node('NotImplemented', attr)


class GeoPackager(object):
    """
    An utility to store homogeneous lists of records as layers
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
            a non-empty list of records with attributes .geom, .coords
        """
        row = rows[0]
        properties = [(f, fiona_type(getattr(row, f)))
                      for f in row.__class__.__annotations__
                      if f not in ('geom', 'coords')]
        schema = {'geometry': row.geom, 'properties': properties}
        with fiona.open(self.fname, 'w', 'GPKG', schema,
                        self.crs, 'utf8', layer=name) as f:
            recs = [geodict(row) for row in rows]
            f.writerecords(recs)

    def read_all(self):
        """
        :returns: a list of geojson dictionaries
        """
        data = []
        for layer in fiona.listlayers(self.fname):
            with fiona.open(self.fname, 'r', 'GPKG',
                            encoding='utf8', layer=layer) as col:
                data.extend(col)
        return data

    def to_nrml(self, out=None):
        out = out or self.fname.replace('.gpkg', '.xml')
        nodes = [geodic2node(dic) for dic in self.read_all()]
        smodel = Node("sourceModel", {}, nodes=nodes)
        with open(out, 'wb') as f:
            nrml.write([smodel], f, '%s')

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
