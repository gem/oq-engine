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

import os
import csv
import warnings
import zipfile
import itertools
from operator import itemgetter
from openquake.nrmllib.node import (
    node_copy, node_from_nrml, node_to_nrml, node_to_xml, Node)
from openquake.nrmllib import InvalidFile
from openquake.nrmllib.readers import ZipReader, RowReader


def build_node(readers, output=None):
    """
    Build a NRML node from a consistent set of .mdata and .csv files.
    If output is not None, it should be a file-like object where to
    save the corresponding NRML file.
    """
    assert readers
    all_readers = []
    tag = None
    # group pairs of .csv and .mdata files and build a list of metadata
    for reader in readers:
        md = reader.metadata
        if tag and tag != md.tag:
            raise ValueError('Found tag=%s in %s.mdata, expected %s' % (
                             md.tag, reader.name, tag))
        else:
            tag = md.tag
        all_readers.append(reader)

    nodebuilder = globals()['%s_from' % md.tag.lower()]
    node = nodebuilder(all_readers)
    if output is not None:
        node_to_nrml(node, output)
    return node


def getfieldnames(md):
    getfields = globals()['%s_fieldnames' % md.tag.lower()]
    return getfields(md)


def parse_nrml(fname):
    """
    Parse a NRML file and yields metadata dictionaries.

    :param fname: filename or file object
    """
    model = node_from_nrml(fname)[0]
    parse = globals()['%s_parse' % model.tag.lower()]
    return parse(model)


############################# vulnerability #################################

def vulnerabilitymodel_fieldnames(md):
    fieldnames = ['IML']
    for vf in md.discreteVulnerabilitySet.getnodes('discreteVulnerability'):
        vf_id = vf.attrib['vulnerabilityFunctionID']
        for node in vf:  # lossRatio and coefficientsVariation
            fieldnames.append('%s.%s' % (vf_id, node.tag))
    return fieldnames


def vulnerabilitymodel_parse(vm):
    """
    A parser for vulnerability models yielding readers
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
        yield RowReader('vset', metadata, zip(*matrix))


def _floats_to_text(fname, colname, rows):
    """
    A convenience function for reading vulnerability models.
    """
    floats = []
    for i, r in enumerate(rows, 1):
        col = r[colname]
        try:
            float(col)
        except (ValueError, TypeError) as e:
            raise InvalidFile('%s:row #%d:%s:%s' % (
                              fname, i, colname, e))
        floats.append(col)
    return ' ' .join(floats)


def vulnerabilitymodel_from(readers):
    """
    Build a vulnerability Node from a group of readers
    """
    vsets = []
    for reader in readers:
        md = reader.metadata
        fname = reader.name
        rows = list(reader)
        if not rows:
            warnings.warn('No data in %s' % reader.name)
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
    if md['format'] == 'discrete':
        return ['IML'] + md.limitStates.text.split()
    elif md['format'] == 'continuous':
        return ['param'] + md.limitStates.text.split()


def fragilitymodel_parse(fm):
    """
    A parser for fragility models yielding readers
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
        md.append(Node('ffs', ffs.attrib, nodes=ffs.nodes[:2]))
        # append the two nodes taxonomy and IML
        yield RowReader('ffs', md, zip(*matrix))


def fragilitymodel_from(readers):
    """
    Build Node objects from readers
    """
    fm = node_copy(readers[0].metadata)
    del fm[2]  # ffs node
    for reader in readers:
        rows = list(reader)
        ffs = node_copy(reader.metadata.ffs)
        for ls in fm.limitStates.text.split():
            if fm.attrib['format'] == 'discrete':
                poes = ' '.join(row[ls] for row in rows)
                ffs.append(Node('ffd', dict(ls=ls),
                                nodes=[Node('poEs', {}, poes)]))
            elif fm.attrib['format'] == 'continuous':
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
    fieldnames = ['id', 'taxonomy', 'lon', 'lat', 'number']
    if md['category'] == 'buildings':
        fieldnames.append('area')
        costcolumns = getcostcolumns(md.conversions.costTypes)
        fieldnames.extend(
            costcolumns + ['occupancy.%s' % period for period in PERIODS])
    return fieldnames


def exposuremodel_parse(em):
    """
    A parser for exposure models yielding readers
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
    yield RowReader('exposure', metadata, data)


def assetgenerator(rows, costtypes):
    """
    Convert rows into asset nodes.

    :param rows: something like a DictReader instance
    :param costtypes: list of dictionaries with the cost types

    :returns: an iterable over Node objects describing exposure assets
    """
    for row in rows:
        nodes = [Node('location', dict(lon=row['lon'], lat=row['lat']))]
        costnodes = []
        for costtype in costtypes:
            keepnode = True
            attr = dict(type=costtype['name'])
            for costcol in COSTCOLUMNS:
                value = row['%s.%s' % (costtype['name'], costcol)]
                if value:
                    attr[costcol] = value
                elif costcol == 'value':
                    keepnode = False  # ignore costs without value
            if keepnode:
                costnodes.append(Node('cost', attr))
        if costnodes:
            nodes.append(Node('costs', {}, nodes=costnodes))
        has_occupancies = any('occupancy.%s' % period in row
                              for period in PERIODS)
        if has_occupancies:
            occ = []
            for period in PERIODS:
                occupancy = row['occupancy.' + period]
                if occupancy:
                    occ.append(Node('occupancy',
                                    dict(occupants=occupancy, period=period)))
            nodes.append(Node('occupancies', {}, nodes=occ))
        attr = dict(
            id=row['id'], number=row['number'], taxonomy=row['taxonomy'])
        if 'area' in row:
            attr['area'] = row['area']
        yield Node('asset', attr, nodes=nodes)


def exposuremodel_from(readers):
    """
    Build a Node object containing a full exposure. The assets are
    lazily read from the associated reader.

    :param readers: a non-empty list of metadata dictionaries
    """
    assert len(readers) == 1, 'Exposure files must contain a single node'
    reader = readers[0]
    em = node_copy(reader.metadata)
    ctypes = em.conversions.costTypes if em.attrib['category'] == 'buildings' \
        else []
    em.assets.nodes = assetgenerator(reader, ctypes)
    return em


################################# gmf ##################################

def gmfset_fieldnames(md):
    return ['lon', 'lat', 'gmv']


def gmfset_parse(gmfset):
    """
    A parser for GMF scenario yielding a reader
    for each node <gmf>.
    """
    for gmf in gmfset.getnodes('gmf'):
        metadata = Node('gmfSet', gmfset.attrib,
                        nodes=[Node('gmf', gmf.attrib)])
        data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
        yield RowReader('gmf', metadata, data)


def gmfcollection_parse(gmfcoll):
    """
    A parser for GMF event based yielding a reader
    for each node <gmf>.
    """
    for gmfset in gmfcoll.getnodes('gmfSet'):
        for gmf in gmfset.getnodes('gmf'):
            metadata = Node('gmfCollection', gmfcoll.attrib)
            gs = Node('gmfSet', gmfset.attrib, nodes=[Node('gmf', gmf.attrib)])
            metadata.append(gs)
            data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
            yield RowReader('gmf', metadata, data)


def gmfcollection_fieldnames(md):
    return ['lon', 'lat', 'gmv']


def gmfcollection_from(readers):
    """
    Build a node from a list of metadata dictionaries with readers
    """
    assert len(readers) >= 1
    md = readers[0].metadata
    gmfcoll = Node('gmfCollection', dict(
        sourceModelTreePath=md.attrib['sourceModelTreePath'],
        gsimTreePath=md.attrib['gsimTreePath']))

    def get_ses_id(reader):
        return reader.metadata.gmfSet.attrib['stochasticEventSetId']
    for ses_id, readergroup in itertools.groupby(readers, get_ses_id):
        readerlist = list(readergroup)
        gmfset = Node('gmfSet', readerlist[0].metadata.gmfSet.attrib)
        for reader in readerlist:
            gmf = Node('gmf', reader.metadata.gmfSet.gmf.attrib,
                       nodes=[Node('node', row) for row in reader])
            gmfset.append(gmf)
        gmfcoll.append(gmfset)
    return gmfcoll


def gmfset_from(readers):
    """
    Build a node from a list of metadata dictionaries with readers
    """
    assert len(readers) > 1
    gmfcoll = Node('gmfSet')
    for reader in readers:
        md = reader.metadata
        gmf = node_copy(md.gmf)
        for row in reader:
            gmf.append(Node('node', row))
        gmfcoll.append(gmf)
    return gmfcoll


################################# generic #####################################

def convert_nrml_to_flat(fname, outfname):
    """
    Convert a NRML file into .csv and .mdata files. Returns the path names
    of the generated files.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path, for instance <path>.csv
    """
    tozip = []
    for i, reader in enumerate(parse_nrml(fname)):
        with open(outfname[:-4] + '__%d.mdata' % i, 'w') as mdatafile:
            with open(outfname[:-4] + '__%d.csv' % i, 'w') as csvfile:
                node_to_xml(reader.metadata, mdatafile)
                tozip.append(mdatafile.name)
                cw = csv.writer(csvfile)
                cw.writerow(reader.fieldnames)
                cw.writerows(reader.rows)
                tozip.append(csvfile.name)
    return tozip


def convert_nrml_to_zip(fname, outfname=None):
    """
    Convert a NRML file into a zip archive.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path; if None, <path>.zip is used instead
    """
    outname = outfname or fname[:-4] + '.zip'
    assert outname.endswith('.zip'), outname
    tozip = convert_nrml_to_flat(fname, outname)
    with zipfile.ZipFile(fname[:-4] + '.zip', 'w') as z:
        for fname in tozip:
            z.write(fname, os.path.basename(fname))
            os.remove(fname)
    return outname


def convert_zip_to_nrml(fname, outdir=None):
    """
    Convert a zip archive into one or more NRML files.

    :param fname: path to a zip archive
    :param outdir: output directory; if None the input directory is used
    """
    outdir = outdir or os.path.dirname(fname)
    z = zipfile.ZipFile(fname)
    outputs = []
    for name, readers in ZipReader.getall(z):
        outname = os.path.join(outdir, name + '.xml')
        with open(outname, 'wb+') as out:
            build_node(readers, out)
        outputs.append(outname)
    return outputs
