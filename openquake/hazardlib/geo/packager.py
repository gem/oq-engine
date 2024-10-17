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
import logging
import time
try:
    import fiona
    from fiona import crs
except ImportError:
    raise ImportError('The geospatial libraries must be installed using our '
                      'requirements.txt files (see https://github.com/gem/oq-engine). '
                      'Only the GEM wheels are tested and guaranteed to work')
from openquake.baselib.node import Node, scientificformat
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


def nogeomdict(row):
    prop = {}
    for k, v in row.items():
        prop[k] = json.dumps(v) if isinstance(v, list) else v
    return {'geometry': None,
            'properties': prop}


def fiona_type(value):
    if isinstance(value, int):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    return 'str'


def build_sfg_geom_nodes(geomprops, coords):
    geom_nodes = []
    geom_nodes.append(
        Node('{%s}LineString' % nrml.GML_NAMESPACE,
             nodes=[Node('{%s}posList' % nrml.GML_NAMESPACE, text=coords)]))
    other_nodes = [Node(k, {}, text=scientificformat(v))
                   for (k, v) in geomprops.items()
                   if not k.startswith('_')]
    geom_nodes.extend(other_nodes)
    return geom_nodes


def build_mpg_geom_nodes(geomprops, coords):
    geom_nodes = []
    # NOTE: posList could also be taken from geomprops, but losing the
    #       namespace
    # FIXME: we can have a mismatch in number of digits in coords and geomprops
    geom_nodes.append(
        Node('{%s}posList' % nrml.GML_NAMESPACE, text=coords))
    other_nodes = [Node(k, {}, text=scientificformat(v))
                   for (k, v) in geomprops.items()
                   if not k.startswith('_')]
    geom_nodes.extend(other_nodes)
    return geom_nodes


def build_nodes(props):
    [(mfd, dic)] = ast.literal_eval(props['mfd']).items()
    mfd_attrs = {k[1:]: scientificformat(v)
                 for k, v in dic.items() if k.startswith('_')}
    mfd_subnodes = [Node(tag, {}, scientificformat(dic[tag]))
                    for tag in dic.keys() if not tag.startswith('_')]
    msr = Node('magScaleRel', text=props['magscalerel'])
    rar = Node('ruptAspectRatio',
               text=scientificformat(props['ruptaspectratio']))
    mfd = Node(mfd, mfd_attrs, nodes=mfd_subnodes)
    nodes = [msr, rar, mfd]
    npd = ast.literal_eval(props['nodalplanedist'])
    if npd:
        nodes.append(
            Node('nodalPlaneDist', nodes=[Node('nodalPlane', dic)
                                          for dic in npd]))
    hdd = ast.literal_eval(props['hypodepthdist'])
    if hdd:
        nodes.append(
            Node('hypoDepthDist', nodes=[Node('hypoDepth', dic)
                                         for dic in hdd]))
    hyl = ast.literal_eval(props['hypoList'])
    if hyl:
        nodes.append(
            Node('hypoList', nodes=[Node('hypo', dic) for dic in hyl]))
    sll = ast.literal_eval(props['slipList'])
    if sll:
        sll_nodes = [
            Node('slip',
                 {k.replace('_', ''): v for k, v in sl.items() if k != 'text'},
                 text=sl['text']) for sl in sll]
        nodes.append(Node('slipList', nodes=sll_nodes))
    if 'rake' in props and props['rake']:
        nodes.append(Node('rake',
                     text=scientificformat(props['rake'])))
    return tuple(nodes)


def edge(name, coords):
    return Node(name + 'Edge', nodes=[
        Node('{%s}LineString' % nrml.GML_NAMESPACE,
             nodes=[Node('{%s}posList' % nrml.GML_NAMESPACE, text=coords)])])


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
    attr = dict(id=props['id'], name=props['name'])
    if props['tectonicregion']:
        attr['tectonicRegion'] = props['tectonicregion']
    geomprops = ast.literal_eval(props['geomprops'])
    geomattrs = {k[1:]: scientificformat(v) for (k, v) in geomprops.items()
                 if k.startswith('_')}
    if code == 'P':
        point = Node('{%s}Point' % nrml.GML_NAMESPACE,
                     nodes=[Node('{%s}pos' % nrml.GML_NAMESPACE, text=coords)])
        usd = Node('upperSeismoDepth',
                   text=scientificformat(props['upperseismodepth']))
        lsd = Node('lowerSeismoDepth',
                   text=scientificformat(props['lowerseismodepth']))
        nodes = [Node('pointGeometry', geomattrs, nodes=[point, usd, lsd])]
        nodes.extend(build_nodes(props))
        return Node('pointSource', attr, nodes=nodes)
    elif code == 'C':
        cplx = Node(
            'complexFaultGeometry', geomattrs, nodes=build_edges(coords))
        nodes = (cplx,) + build_nodes(props)
        return Node('complexFaultSource', attr, nodes=nodes)
    elif code == 'A':
        pol = Node('{%s}Polygon' % nrml.GML_NAMESPACE, nodes=[
            Node('{%s}exterior' % nrml.GML_NAMESPACE, nodes=[
                Node('{%s}LinearRing' % nrml.GML_NAMESPACE,
                     nodes=[Node('{%s}posList' % nrml.GML_NAMESPACE,
                            text=coords)])])])
        usd = Node('upperSeismoDepth',
                   text=scientificformat(props['upperseismodepth']))
        lsd = Node('lowerSeismoDepth',
                   text=scientificformat(props['lowerseismodepth']))
        area = Node('areaGeometry', geomattrs, nodes=[pol, usd, lsd])
        nodes = (area,) + build_nodes(props)
        return Node('areaSource', attr, nodes=nodes)
    elif code == 'S':
        geom_nodes = build_sfg_geom_nodes(geomprops, coords)
        splx = Node('simpleFaultGeometry', geomattrs, nodes=geom_nodes)
        nodes = (splx,) + build_nodes(props)
        return Node('simpleFaultSource', attr, nodes=nodes)
    elif code == 'M':
        geom_nodes = build_mpg_geom_nodes(geomprops, coords)
        mpg = Node('multiPointGeometry', geomattrs, nodes=geom_nodes)
        nodes = (mpg,) + build_nodes(props)
        return Node('multiPointSource', attr, nodes=nodes)
    else:
        logging.error(f'Skipping source of code "{code}" and attributes '
                      f'"{attr}" (the converter is not implemented yet)')
        return None


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

    def save_table(self, name, dicts):
        """
        :param name: table name
        :param dicts: a non-empty list of dicts
        """
        row = dicts[0]
        properties = [(k, fiona_type(v))
                      for k, v in row.items()]
        schema = {'geometry': None,
                  'properties': properties}
        with fiona.open(self.fname, 'w', 'GPKG', schema,
                        self.crs, 'utf8', layer=name) as f:
            recs = [nogeomdict(dic) for dic in dicts]
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
        t0 = time.time()
        out = out or self.fname.replace('.gpkg', '.xml')
        all = self.read_all()
        src_groups_attrs = {}
        srcs_by_grp = {}
        smodel_attrs = {}
        for dic in all:
            if dic['geometry'] is None:
                kind = dic['properties']['kind']
                if kind == 'sourceModel':
                    smodel_attrs = dic['properties']
                    smodel_attrs.pop('kind', None)
                elif kind == 'sourceGroup':
                    try:
                        groupname = dic['properties']['name']
                    except KeyError:
                        groupname = ''
                    src_group_attrs = dic['properties']
                    src_group_attrs.pop('kind', None)
                    src_groups_attrs[groupname] = src_group_attrs
            else:
                try:
                    groupname = dic['properties']['groupname']
                except KeyError:
                    groupname = ''
                node = geodic2node(dic)
                if node is not None:
                    try:
                        srcs_by_grp[groupname].append(node)
                    except KeyError:
                        srcs_by_grp[groupname] = [node]
        all_sgroups = []
        for src_group_name in srcs_by_grp:
            src_group_nodes = srcs_by_grp[src_group_name]
            if src_group_name:
                src_group_attrs = src_groups_attrs[src_group_name]
                sgroup = Node(
                    'sourceGroup', src_group_attrs, nodes=src_group_nodes)
                all_sgroups.append(sgroup)
            else:
                all_sgroups.extend(src_group_nodes)
        smodel = Node("sourceModel", smodel_attrs, nodes=all_sgroups)
        with open(out, 'wb') as f:
            nrml.write([smodel], f, '%s')
        logging.info('%s was created' % out)
        logging.info('Finished in %d seconds', time.time() - t0)

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
