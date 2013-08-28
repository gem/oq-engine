import os
import csv
import json
import zipfile
import itertools
from openquake.nrmllib.utils import node_from_nrml, node_to_nrml, Node


class InvalidFile(Exception):
    pass


def build_node(files, output=None):
    """
    Build a NRML node from a consistent set of .csv and .json files.
    If output is not None, it should be a file-like object where to
    save the corresponding NRML file.
    """
    def prefix(fileobj):
        return os.path.basename(fileobj.name).rsplit('.', 1)[0]
    sorted_files = sorted(files, key=lambda f: f.name)

    all_md = []
    tag = None
    # group pairs of .csv and .json files and build a list of metadata
    for name, group in itertools.groupby(sorted_files, prefix):
        file_csv, file_json = group
        try:
            metadata = json.load(file_json)
        except ValueError:
            raise InvalidFile(file_json.name)
        if tag and tag != metadata['tag']:
            raise ValueError('Found tag=%s in %s, expected %s' % (
                             metadata['tag'], file_json.name, tag))
        else:
            tag = metadata['tag']
        try:
            metadata['filecsv'] = file_csv
            metadata['reader'] = csv.DictReader(file_csv)
        except ValueError:
            raise InvalidFile(file_csv.name)
        if metadata['reader'].fieldnames != metadata['fieldnames']:
            raise ValueError(
                'According to %s the field names should be '
                '%s, but the header in %s says %s' % (
                    file_json.name, metadata['fieldnames'],
                    file_csv.name, metadata['reader'].fieldnames))
        all_md.append(metadata)

    nodebuilder = globals()['%s_from' % metadata['tag'].lower()]
    node = nodebuilder(all_md)
    if output is not None:
        node_to_nrml(node, output)
    return node


def parse_nrml(fname):
    """
    Parse a NRML file and yields metadata, data.

    :param fname: filename or file object
    """
    model = node_from_nrml(fname)[0]
    parser = globals()['parse_%s' % model.tag.lower()]
    for metadata, data in parser(model):
        metadata['tag'] = model.tag
        yield metadata, data


############################# vulnerability #################################

def parse_vulnerabilitymodel(vm):
    """
    A parser for vulnerability models yielding pairs (metadata, data)
    """
    for vset in vm.getnodes('discreteVulnerabilitySet'):
        metadata = dict(losscategory=vset['lossCategory'],
                        assetcategory=vset['assetCategory'],
                        vulnerabilitysetid=vset['vulnerabilitySetID'],
                        imt=vset.IML['IMT'],
                        probabilitydistributions=[],
                        vulnerabilityfunctionids=[],
                        fieldnames=['IML'])
        probabilitydistributions = metadata['probabilitydistributions']
        vulnerabilityfunctionids = metadata['vulnerabilityfunctionids']

        fieldnames = metadata['fieldnames']
        matrix = [vset.IML.text.split()]  # data in transposed form
        for vf in vset.getnodes('discreteVulnerability'):
            vf_id = vf['vulnerabilityFunctionID']
            probabilitydistributions.append(vf['probabilisticDistribution'])
            vulnerabilityfunctionids.append(vf_id)
            fieldnames.append('%s.lossRatio' % vf_id)
            fieldnames.append('%s.coefficientsVariation' % vf_id)
            matrix.append(vf.lossRatio.text.split())
            matrix.append(vf.coefficientsVariation.text.split())
        yield metadata, zip(*matrix)


def _mknode(filecsv, colname, attrib, rows):
    """
    A convenience function for reading vulnerability XML models.
    """
    try:
        func, name = colname.split('.')
    except ValueError:  # no dot
        name = colname
    floats = []
    for i, r in enumerate(rows, 1):
        col = r[colname]
        try:
            float(col)
        except (ValueError, TypeError) as e:
            raise InvalidFile('%s:row #%d:%s:%s' % (
                              filecsv.name, i, colname, e))
        floats.append(col)
    return Node(name, attrib, text=' ' .join(floats))


def vulnerabilitymodel_from(md_list):
    """
    Build a vulnerability Node from a group of metadata dictionaries.
    """
    vsets = []
    for md in md_list:
        filecsv = md['filecsv']
        rows = list(md['reader'])
        vfs = []  # vulnerability function nodes
        for vf_id, probdist in zip(
                md['vulnerabilityfunctionids'],
                md['probabilitydistributions']):
            nodes = [
                _mknode(filecsv, '%s.lossRatio' % vf_id, {}, rows),
                _mknode(filecsv, '%s.coefficientsVariation' % vf_id, {}, rows)]
            vfs.append(
                Node('discreteVulnerability',
                     dict(vulnerabilityFunctionID=vf_id,
                          probabilisticDistribution=probdist),
                     nodes=nodes))
        nodes = [_mknode(filecsv, 'IML', dict(IMT=md['imt']), rows)] + vfs
        vsets.append(Node('discreteVulnerabilitySet',
                          dict(vulnerabilitySetID=md["vulnerabilitysetid"],
                               assetCategory=md['assetcategory'],
                               lossCategory=md['losscategory']),
                          None, nodes))
    # nodes=[Node('config', {})] + vsets
    return Node('vulnerabilityModel', nodes=vsets)


############################# fragility #################################

def parse_fragilitymodel(fm):
    """
    A parser for fragility models yielding pairs (metadata, data)
    """
    format = fm['format']
    limitStates = fm.limitStates.text.split()
    description = fm.description.text.strip()

    for ffs in fm.getnodes('ffs'):
        metadata = dict(
            format=format,
            limitStates=limitStates,
            description=description,
            noDamageLimit=ffs.attrib.get('noDamageLimit'),
            taxonomy=ffs.taxonomy.text.strip(),
            IMT=ffs.IML['IMT'],
            IML=ffs.IML.text.split() if ffs.IML.text else [],
            imlUnit=ffs.IML['imlUnit'])
        if format == 'discrete':
            metadata['fieldnames'] = ['IML'] + limitStates
            matrix = [metadata['IML']]  # data in transposed form
            for ls, ffd in zip(limitStates, ffs.getnodes('ffd')):
                assert ls == ffd['ls'], 'Expected %s, got %s' % (
                    ls, ffd['ls'])
                matrix.append(ffd.poEs.text.split())
            yield metadata, zip(*matrix)
        elif format == 'continuous':
            metadata['fieldnames'] = ['param'] + limitStates
            metadata['type'] = ffs.attrib.get('type')
            metadata['minIML'] = ffs.IML['minIML']
            metadata['maxIML'] = ffs.IML['maxIML']
            matrix = ['mean stddev'.split()]
            for ls, ffc in zip(limitStates, ffs.getnodes('ffc')):
                assert ls == ffc['ls'], 'Expected %s, got %s' % (
                    ls, ffc['ls'])
                matrix.append([ffc.params['mean'], ffc.params['stddev']])
            yield metadata, zip(*matrix)


def fragilitymodel_from(md_list):
    """
    Build Node objects for the fragility sets.
    """
    md = md_list[0]
    nodes = [Node('description', {}, md['description']),
             Node('limitStates', {}, ' '.join(md['limitStates']))]
    for md in md_list:
        ffs_attrib = dict(noDamageLimit=md['noDamageLimit']) \
            if md['noDamageLimit'] else {}
        if 'type' in md and md['type']:
            ffs_attrib['type'] = md['type']
        iml = Node('IML', dict(IMT=md['IMT'], imlUnit=md['imlUnit']),
                   ' '.join(md['IML']))
        if md['format'] == 'continuous':
            iml['minIML'] = md['minIML']
            iml['maxIML'] = md['maxIML']
        ffs_nodes = [Node('taxonomy', {}, md['taxonomy']), iml]
        rows = list(md['reader'])
        for ls in md['limitStates']:
            if md['format'] == 'discrete':
                poes = ' '.join(row[ls] for row in rows)
                ffs_nodes.append(Node('ffd', dict(ls=ls),
                                      nodes=[Node('poEs', {}, poes)]))
            elif md['format'] == 'continuous':
                mean, stddev = rows  # there are exactly two rows
                params = dict(mean=mean[ls], stddev=stddev[ls])
                ffs_nodes.append(Node('ffc', dict(ls=ls),
                                      nodes=[Node('params', params)]))
        ffs = Node('ffs', ffs_attrib, nodes=ffs_nodes)
        nodes.append(ffs)
    return Node('fragilityModel', dict(format=md['format']),
                nodes=nodes)

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


def parse_exposuremodel(em):
    """
    A parser for exposure models yielding a pair (metadata, data)
    """
    metadata = dict(id=em['id'], category=em['category'],
                    taxonomysource=em['taxonomySource'],
                    description=em.description.text.strip(),
                    fieldnames=['id', 'taxonomy', 'lon', 'lat'])
    if em['category'] == 'population':
        metadata['fieldnames'].append('number')
        data = ([asset['id'], asset['taxonomy'],
                 asset.location['lon'], asset.location['lat'],
                 asset['number']]
                for asset in em.assets)
    elif em['category'] == 'buildings':
        metadata['fieldnames'].extend(['number', 'area'])
        metadata['conversions'] = dict(
            area=em.conversions.area.attrib,
            costTypes=[ct.attrib for ct in
                       em.conversions.costTypes.getnodes('costType')],
            deductible=em.conversions.deductible.attrib,
            insuranceLimit=em.conversions.insuranceLimit.attrib,
        )
        costcolumns = getcostcolumns(metadata['conversions']['costTypes'])
        metadata['fieldnames'].extend(
            costcolumns + ['occupancy.%s' % period for period in PERIODS])
        data = ([asset['id'], asset['taxonomy'],
                 asset.location['lon'], asset.location['lat'],
                 asset['number'], asset['area']]
                + getcosts(asset, costcolumns)
                + getoccupancies(asset)
                for asset in em.assets)

    yield metadata, data


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


def exposuremodel_from(md_list):
    """
    Build a Node object containing a full exposure. The assets are
    lazily read from the associated reader.

    :param md_list: a non-empty list of metadata dictionaries
    """
    assert len(md_list) == 1, 'Exposure files must contain a single node'
    for md in md_list:
        costtypes = []
        subnodes = [Node('description', {}, md['description'])]
        conversions = md.get('conversions')
        if conversions:
            area = Node('area', conversions['area'])
            deductible = Node('deductible', conversions['deductible'])
            ilimit = Node('insuranceLimit', conversions['insuranceLimit'])
            ct = []
            for dic in conversions['costTypes']:
                ct.append(Node('costType', dic))
                costtypes.append(dic['name'])
            costtypes = Node('costTypes', {}, nodes=ct)
            subnodes.append(
                Node('conversions', {},
                     nodes=[area, costtypes, deductible, ilimit]))
        subnodes.append(Node('assets', {},
                             nodes=assetgenerator(md['reader'], costtypes)))
        return Node('exposureModel',
                    dict(id=md['id'],
                         category=md['category'],
                         taxonomySource=md['taxonomysource']),
                    nodes=subnodes)


################################# gmf ##################################

# lon,lat,gmv.PGA,gmv.PGV,gmv.SA(0.1)
def parse_gmf(gmfset):
    """
    A parser for GMF yielding pairs (metadata, data)
    """
    for gmf in gmfset.getnodes('gmf'):
        imt = gmf['IMT']
        period = gmf.attrib.get('saPeriod', '')
        if period:
            imt += '(%s)' % period
        metadata = dict(imt=imt, fieldnames=['lon', 'lat'])
        data = [(n['gmv'], n['lon'], n['lat']) for n in gmf]
        yield metadata, data


def gmf_from(md_list):
    raise NotImplementedError


################################# generic #####################################

def convert_nrml_to_flat(fname, outfname):
    """
    Convert a NRML file into .csv and .json files. Returns the pathnames
    of the generated files.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path, for instance <path>.csv
    """
    tozip = []
    for i, (metadata, data) in enumerate(parse_nrml(fname)):
        with open(outfname[:-4] + '-%d.json' % i, 'w') as jsonfile:
            with open(outfname[:-4] + '-%d.csv' % i, 'w') as csvfile:
                json.dump(metadata, jsonfile)
                tozip.append(jsonfile.name)
                cw = csv.writer(csvfile)
                cw.writerow(metadata['fieldnames'])
                cw.writerows(data)
                tozip.append(csvfile.name)
    return tozip


def convert_nrml_to_zip(fname, outfname=None):
    """
    Convert a NRML file into a zip archive.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path; if None <path>.zip is used instead
    """
    outname = outfname or fname[:-4] + '.zip'
    assert outname.endswith('.zip'), outname
    tozip = convert_nrml_to_flat(fname, outname)
    with zipfile.ZipFile(fname[:-4] + '.zip', 'w') as z:
        for fname in tozip:
            z.write(fname, os.path.basename(fname))
            os.remove(fname)
    return outname
