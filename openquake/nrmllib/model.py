#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

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

"""
This module contains functions named <model>_fieldnames, <model>_from
and <model>_parse where <model> is one of

- vulnerabilitymodel
- fragilitymodel
- exposuremodel
- gmfset
- gmfcollection

The <model>_fieldnames functions are used to extract the names of the CSV
fields from the metadata file; the <model>_from functions are used to
convert a set of tables into a Node object; the <model>_parse functions
are used to flatten a Node object into a set of (metadata, data) pairs
where metadata is a Node a data a list-valued iterator.
"""

import warnings
import itertools
from openquake.nrmllib.node import node_copy, Node
from openquake.nrmllib import InvalidFile


############################# vulnerability #################################

def vulnerabilitymodel_fieldnames(md):
    """
    Extract the names of the fields of the CSV file from the metadata file

    :param md: metadata node object
    """
    fieldnames = ['IML']
    for vf in md.discreteVulnerabilitySet.getnodes('discreteVulnerability'):
        vf_id = vf.attrib['vulnerabilityFunctionID']
        for node in vf:  # lossRatio and coefficientsVariation
            fieldnames.append('%s.%s' % (vf_id, node.tag))
    return fieldnames


def vulnerabilitymodel_parse(vm):
    """
    A parser for vulnerability models yielding pairs (metadata, data)

    :param vm: vulnerability model Node
    """
    for vset in vm.getnodes('discreteVulnerabilitySet'):
        vset = node_copy(vset)
        metadata = Node(vm.tag, vm.attrib, nodes=[vset])
        matrix = [vset.IML.text.split()]  # data in transposed form
        vset.IML.text = None
        for vf in vset.getnodes('discreteVulnerability'):
            matrix.append(vf.lossRatio.text.split())
            matrix.append(vf.coefficientsVariation.text.split())
            vf.lossRatio.text = None
            vf.coefficientsVariation.text = None
        yield metadata, zip(*matrix)


def _floats_to_text(fname, colname, records):
    """
    A convenience function for reading floats from columns in a
    CSV vulnerability file.

    :param fname: the pathname of the file
    :param colname: the name of the column
    :param records: a list of dictionaries with the CSV data
    """
    floats = []
    for i, r in enumerate(records, 1):
        col = r[colname]
        try:
            float(col)
        except (ValueError, TypeError) as e:
            raise InvalidFile('%s:row #%d:%s:%s' % (
                              fname, i, colname, e))
        floats.append(col)
    return ' ' .join(floats)


def vulnerabilitymodel_from(tables):
    """
    Build a vulnerability Node from a group of tables
    """
    vsets = []
    for table in tables:
        md = table.metadata
        fname = table.name
        rows = list(table)
        if not rows:
            warnings.warn('No data in %s' % table.name)
        vset = md.discreteVulnerabilitySet
        for vf in vset.getnodes('discreteVulnerability'):
            vf_id = vf.attrib['vulnerabilityFunctionID']
            for node in vf:  # lossRatio, coefficientsVariation
                node.text = _floats_to_text(
                    fname, '%s.%s' % (vf_id, node.tag),  rows)
        vset.IML.text = _floats_to_text(fname, 'IML', rows)
        vsets.append(vset)
    # nodes=[Node('config', {})] + vsets
    return Node('vulnerabilityModel', nodes=vsets)


############################# fragility #################################

def fragilitymodel_fieldnames(md):
    """
    Extract the names of the fields of the CSV file from the metadata file

    :param md: metadata node object
    """
    if md['format'] == 'discrete':
        return ['IML'] + md.limitStates.text.split()
    elif md['format'] == 'continuous':
        return ['param'] + md.limitStates.text.split()


def fragilitymodel_parse(fm):
    """
    A parser for fragility models yielding pairs (metadata, data)

    :param fm: fragility model Node object
    """
    format = fm.attrib['format']
    limitStates = fm.limitStates.text.split()
    for ffs in fm.getnodes('ffs'):
        md = Node('fragilityModel', fm.attrib,
                  nodes=[fm.description, fm.limitStates])
        if format == 'discrete':
            matrix = [ffs.IML.text.split()]  # data in transposed form
            for ls, ffd in zip(limitStates, ffs.getnodes('ffd')):
                assert ls == ffd['ls'], 'Expected %s, got %s' % (
                    ls, ffd['ls'])
                matrix.append(ffd.poEs.text.split())
        elif format == 'continuous':
            matrix = ['mean stddev'.split()]
            for ls, ffc in zip(limitStates, ffs.getnodes('ffc')):
                assert ls == ffc['ls'], 'Expected %s, got %s' % (
                    ls, ffc['ls'])
                matrix.append([ffc.params['mean'], ffc.params['stddev']])
        else:
            raise ValueError('Invalid format %r' % format)
        md.append(Node('ffs', ffs.attrib))
        md.ffs.append(ffs.taxonomy)
        md.ffs.append(Node('IML', ffs.IML.attrib))
        # append the two nodes taxonomy and IML
        yield md, zip(*matrix)


def fragilitymodel_from(tables):
    """
    Build Node objects from tables
    """
    fm = node_copy(tables[0].metadata)
    del fm[2]  # ffs node
    discrete = fm.attrib['format'] == 'discrete'
    for table in tables:
        rows = list(table)
        ffs = node_copy(table.metadata.ffs)
        if discrete:
            ffs.IML.text = ' '.join(row['IML'] for row in rows)
        for ls in fm.limitStates.text.split():
            if discrete:
                poes = ' '.join(row[ls] for row in rows)
                ffs.append(Node('ffd', dict(ls=ls),
                                nodes=[Node('poEs', {}, poes)]))
            else:
                mean, stddev = rows  # there are exactly two rows
                params = dict(mean=mean[ls], stddev=stddev[ls])
                ffs.append(Node('ffc', dict(ls=ls),
                                nodes=[Node('params', params)]))
        fm.append(ffs)
    return fm

############################# exposure #################################

COSTCOLUMNS = 'value deductible insuranceLimit retrofitted'.split()
PERIODS = 'day', 'night', 'transit', 'early morning', 'late afternoon'
## TODO: the occupancy periods should be inferred from the NRML file,
## not hardcoded, exactly as the cost types


def getcosts(asset, costcolumns):
    """
    Extracts different costs from an asset node. If a cost is not available
    returns an empty string for it. Returns a list with the same length of
    the cost columns.
    """
    row = dict.fromkeys(costcolumns, '')
    for cost in asset.costs:
        for kind in COSTCOLUMNS:
            row['%s.%s' % (cost['type'], kind)] = cost.attrib.get(kind, '')
    return [row[cc] for cc in costcolumns]


def getcostcolumns(costtypes):
    """
    Extracts the kind of costs from a CostTypes node. Those will correspond
    to columns names in the .csv representation of the exposure.
    """
    cols = []
    for cost in costtypes:
        for kind in COSTCOLUMNS:
            cols.append('%s.%s' % (cost['name'], kind))
    return cols


def getoccupancies(asset):
    """
    Extracts the occupancies from an asset node.
    """
    dic = dict(('occupancy.' + occ['period'], occ['occupants'])
               for occ in asset.occupancies)
    return [dic.get('occupancy.%s' % period, '') for period in PERIODS]


def exposuremodel_fieldnames(md):
    """
    Extract the names of the fields of the CSV file from the metadata file

    :param md: metadata node object
    """
    fieldnames = ['id', 'taxonomy', 'lon', 'lat', 'number']
    if md['category'] == 'buildings':
        fieldnames.append('area')
        costcolumns = getcostcolumns(md.conversions.costTypes)
        fieldnames.extend(
            costcolumns + ['occupancy.%s' % period for period in PERIODS])
    return fieldnames


def exposuremodel_parse(em):
    """
    A parser for exposure models yielding a pair (metadata, data)

    :param em: exposure model Node object
    """
    metadata = Node('exposureModel', em.attrib, nodes=[em.description])
    if em['category'] == 'population':
        data = ([asset['id'], asset['taxonomy'],
                 asset.location['lon'], asset.location['lat'],
                 asset['number']]
                for asset in em.assets)
    elif em['category'] == 'buildings':
        metadata.append(em.conversions)
        costcolumns = getcostcolumns(em.conversions.costTypes)
        data = ([asset['id'], asset['taxonomy'],
                 asset.location['lon'], asset.location['lat'],
                 asset['number'], asset['area']]
                + getcosts(asset, costcolumns)
                + getoccupancies(asset)
                for asset in em.assets)
    metadata.append(Node('assets'))
    yield metadata, data


def assetgenerator(records, costtypes):
    """
    Convert records into asset nodes.

    :param records: an iterable over dictionaries
    :param costtypes: list of dictionaries with the cost types

    :returns: an iterable over Node objects describing exposure assets
    """
    for record in records:
        nodes = [Node('location', dict(lon=record['lon'], lat=record['lat']))]
        costnodes = []
        for costtype in costtypes:
            keepnode = True
            attr = dict(type=costtype['name'])
            for costcol in COSTCOLUMNS:
                value = record['%s.%s' % (costtype['name'], costcol)]
                if value:
                    attr[costcol] = value
                elif costcol == 'value':
                    keepnode = False  # ignore costs without value
            if keepnode:
                costnodes.append(Node('cost', attr))
        if costnodes:
            nodes.append(Node('costs', {}, nodes=costnodes))
        has_occupancies = any('occupancy.%s' % period in record
                              for period in PERIODS)
        if has_occupancies:
            occ = []
            for period in PERIODS:
                occupancy = record['occupancy.' + period]
                if occupancy:
                    occ.append(Node('occupancy',
                                    dict(occupants=occupancy, period=period)))
            nodes.append(Node('occupancies', {}, nodes=occ))
        attr = dict(id=record['id'], number=record['number'],
                    taxonomy=record['taxonomy'])
        if 'area' in record:
            attr['area'] = record['area']
        yield Node('asset', attr, nodes=nodes)


def exposuremodel_from(tables):
    """
    Build a Node object containing a full exposure. The assets are
    lazily read from the associated table.

    :param tables: a non-empty list of metadata dictionaries
    """
    assert len(tables) == 1, 'Exposure files must contain a single node'
    table = tables[0]
    em = node_copy(table.metadata)
    ctypes = em.conversions.costTypes if em.attrib['category'] == 'buildings' \
        else []
    em.assets.nodes = assetgenerator(table, ctypes)
    return em


################################# gmf ##################################

def gmfset_fieldnames(md):
    """
    The fields in a GMF CSV file (lon, lat, gmv)

    :param md: metadata node object (for API compatibility, but ignored)
    """
    return ['lon', 'lat', 'gmv']


def gmfset_parse(gmfset):
    """
    A parser for GMF scenario yielding a pair (metadata, data)
    for each node <gmf>.
    """
    for gmf in gmfset.getnodes('gmf'):
        metadata = Node('gmfSet', gmfset.attrib,
                        nodes=[Node('gmf', gmf.attrib)])
        data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
        yield metadata, data


def gmfcollection_parse(gmfcoll):
    """
    A parser for GMF event based yielding a pair (metadata, data)
    for each node <gmf>.
    """
    for gmfset in gmfcoll.getnodes('gmfSet'):
        for gmf in gmfset.getnodes('gmf'):
            metadata = Node('gmfCollection', gmfcoll.attrib)
            gs = Node('gmfSet', gmfset.attrib, nodes=[Node('gmf', gmf.attrib)])
            metadata.append(gs)
            data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
            yield metadata, data


def gmfcollection_fieldnames(md):
    """
    The fields in a GMF CSV file (lon, lat, gmv)

    :param md: metadata node object (for API compatibility, but ignored)
    """
    return ['lon', 'lat', 'gmv']


def gmfcollection_from(tables):
    """
    Build a node from a list of metadata dictionaries with tables
    """
    assert len(tables) >= 1
    md = tables[0].metadata
    gmfcoll = Node('gmfCollection', dict(
        sourceModelTreePath=md.attrib['sourceModelTreePath'],
        gsimTreePath=md.attrib['gsimTreePath']))

    def get_ses_id(table):
        return table.metadata.gmfSet.attrib['stochasticEventSetId']
    for ses_id, tablegroup in itertools.groupby(tables, get_ses_id):
        tablelist = list(tablegroup)
        gmfset = Node('gmfSet', tablelist[0].metadata.gmfSet.attrib)
        for table in tablelist:
            gmf = Node('gmf', table.metadata.gmfSet.gmf.attrib,
                       nodes=[Node('node', record) for record in table])
            gmfset.append(gmf)
        gmfcoll.append(gmfset)
    return gmfcoll


def gmfset_from(tables):
    """
    Build a node from a list of metadata dictionaries with tables
    """
    assert len(tables) > 1
    gmfcoll = Node('gmfSet')
    for table in tables:
        md = table.metadata
        gmf = node_copy(md.gmf)
        for record in table:
            gmf.append(Node('node', record))
        gmfcoll.append(gmf)
    return gmfcoll
