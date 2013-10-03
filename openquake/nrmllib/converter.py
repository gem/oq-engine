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
This module contains converter classes working on nodes of kind

- vulnerabilitymodel
- fragilitymodel
- exposuremodel
- gmfset
- gmfcollection
"""

import os
import inspect
import itertools
from openquake.nrmllib.node import Node, node_to_nrml, node_from_nrml
from openquake.nrmllib import record, records, InvalidFile


class Converter(object):
    """
    Base class.
    """
    def __init__(self, csvmanager):
        self.man = csvmanager

    def __str__(self):
        return '<%s %s>' % (self.__class__.___name__, self.name)

    def node_to_records(self, node):
        """Convert the node into a sequence of records"""
        raise NotImplementedError

    def node_to_csv(self, node, prefix):
        """
        From a node to a set of .csv files with the given prefix
        """
        name = node.tag[0].upper() + node.tag[1:]
        clsname = name[:-5] if name.endswith('Model') else name
        man = record.CSVManager(prefix, self.man.archive)
        conv = globals()[clsname](man)
        with man:
            for rec in conv.node_to_records(node):
                man.write(rec)  # automatically writes the header
        return [f.name for f in man.archive.opened]

    def nrml_to_csv(self, fname):
        """
        From a NRML file to a set of .csv files with the given prefix.
        :returns: the names of the generated files
        """
        assert fname.endswith('.xml'), fname
        return self.node_to_csv(node_from_nrml(fname)[0],
                                os.path.basename(fname)[:-4])

    def csv_to_node(self):
        """For .csv files with a given prefix to a single node"""
        raise NotImplementedError

    def csv_to_nrml(self, out):
        """
        For .csv files with a given prefix to a single .xml file
        """
        with self.man:
            node_to_nrml(self.csv_to_node(), out)
        return out.name

    def get_all(self):
        """
        Returns a list of Converter instances, one for each file group
        in the underlying archive.
        """
        converters = {}  # converter name->class dictionary
        cc = {}
        for name, value in globals().iteritems():
            if inspect.isclass(value) and issubclass(value, Converter):
                cc[name] = value
        for fname in sorted(self.man.archive.extract_filenames()):
            try:
                name, recordcsv = fname.split('__')
            except ValueError:
                continue
            if not recordcsv.endswith('.csv'):
                continue
            recordtype = getattr(records, recordcsv[:-4], None)
            if recordtype is None:
                continue
            if not name in converters:
                converters[name] = cc[recordtype._tag](self.man)
        return converters.values()

    def get(self):
        """
        Extract the appropriate converter to convert the files in
        the underlying archive. Raise an error is no converter is
        found (this happens if there are no files following the
        naming conventions).
        """
        converters = self.get_all()
        if not converters:
            raise RuntimeError(
                'Could not determine the right converter '
                'from files %s' % self.man.archive.extract_filenames())
        elif len(converters) > 2:
            raise RuntimeError(
                'Found %d converters, expected 1' % len(converters))
        return converters[0]


############################# vulnerability #################################

class Vulnerability(Converter):
    """A converter for vulnerabilityModel nodes"""

    def node_to_records(self, node):
        """
        """
        for vset in node.getnodes('discreteVulnerabilitySet'):
            set_id = vset['vulnerabilitySetID']
            dvs = records.DiscreteVulnerabilitySet(
                set_id,
                vset['assetCategory'],
                vset['lossCategory'],
                vset.IML['IMT'])
            yield dvs
            imls = vset.IML.text.split()
            for vf in vset.getnodes('discreteVulnerability'):
                fun_id = vf['vulnerabilityFunctionID']
                ratios = vf.lossRatio.text.split()
                coeffs = vf.coefficientsVariation.text.split()
                dv = records.DiscreteVulnerability(
                    set_id,
                    fun_id,
                    vf['probabilisticDistribution'])
                yield dv
                for iml, ratio, coeff in zip(imls, ratios, coeffs):
                    yield records.DiscreteVulnerabilityData(
                        set_id, fun_id, iml, ratio, coeff)

    def csv_to_node(self):
        """
        Build a full vulnerability Node from a group of tables.
        """
        dvs_node = self.man.readtable(
            records.DiscreteVulnerabilitySet).to_nodedict()
        dvf_node = self.man.readtable(
            records.DiscreteVulnerability).to_nodedict()
        for (set_id, vf_id), group in self.man.groupby(
                ['vulnerabilitySetID', 'vulnerabilityFunctionID'],
                records.DiscreteVulnerabilityData):
            dvf = dvf_node[set_id, vf_id]
            coeffs = []
            ratios = []
            imls = []
            for row in group:
                imls.append(row['IML'])
                coeffs.append(row['coefficientsVariation'])
                ratios.append(row['lossRatio'])
            dvf.lossRatio.text = ' '.join(ratios)
            dvf.coefficientsVariation.text = ' '.join(coeffs)
            dvs_node[set_id].append(dvf)
            dvs_node[set_id].IML.text = ' '.join(imls)
        datafile = self.man.rt2file[records.DiscreteVulnerabilityData]
        for set_id, dvs in dvs_node.iteritems():
            if dvs.IML.text is None:
                raise InvalidFile(
                    '%s: no data for %s' % (datafile.name, set_id))
        return Node('vulnerabilityModel', nodes=dvs_node.values())


############################# fragility #################################

class Fragility(Converter):
    """A converter for fragilityModel nodes"""

    def node_to_records(self, node):
        """
        """
        format = node['format']
        limitStates = node.limitStates.text.split()
        yield records.Fragility(node['format'],
                                node.description.text.strip(),
                                node.limitStates.text.strip())
        for i, ffs in enumerate(node.getnodes('ffs'), 1):
            ffs_ordinal = str(i)

            if format == 'discrete':
                yield records.FFSDiscrete(
                    ffs_ordinal,
                    ffs.taxonomy.text,
                    ffs.attrib.get('noDamageLimit', ''),
                    ffs.IML['IMT'],
                    ffs.IML['imlUnit'])
                imls = ffs.IML.text.split()
                for ls, ffd in zip(limitStates, ffs.getnodes('ffd')):
                    assert ls == ffd['ls'], 'Expected %s, got %s' % (
                        ls, ffd['ls'])
                    poEs = ffd.poEs.text.split()
                    for iml, poe in zip(imls, poEs):
                        yield records.FFDDiscrete(ffs_ordinal, ls, iml, poe)

            elif format == 'continuous':
                yield records.FFSContinuous(
                    ffs_ordinal,
                    ffs.taxonomy.text,
                    ffs.attrib.get('noDamageLimit', ''),
                    ffs.attrib.get('type', ''),
                    ffs.IML['IMT'],
                    ffs.IML['imlUnit'],
                    ffs.IML['minIML'],
                    ffs.IML['maxIML'])
                for ls, ffc in zip(limitStates, ffs.getnodes('ffc')):
                    assert ls == ffc['ls'], 'Expected %s, got %s' % (
                        ls, ffc['ls'])
                    yield records.FFDContinuos(
                        ffs_ordinal, ls, 'mean', ffc.params['mean'])
                    yield records.FFDContinuos(
                        ffs_ordinal, ls, 'stddev', ffc.params['stddev'])

    def csv_to_node(self):
        """
        Build a full fragility node from Fragility.csv and
        FFSDiscrete.csv, FFDDiscrete.csv or
        FFSContinuous.csv, FFDContinuous.csv.
        """
        frag = self.man.read(records.Fragility).next().to_node()
        if frag['format'] == 'discrete':
            FFSRecord = records.FFSDiscrete
            FFDRecord = records.FFDDiscrete
        else:  # 'continuous'
            FFSRecord = records.FFSContinuous
            FFDRecord = records.FFDContinuos
        ffs_node = self.man.readtable(FFSRecord).to_nodedict()
        frag.nodes.extend(ffs_node.values())
        for (ordinal, ls), data in self.man.groupby(
                ['ffs_ordinal', 'limitState'], FFDRecord):
            data = list(data)
            if frag['format'] == 'discrete':
                imls = ' '.join(rec['iml'] for rec in data)
                ffs_node[ordinal].IML.text = imls
                poes = ' '.join(rec['poe'] for rec in data)
                n = Node('ffd', dict(ls=ls))
                n.append(Node('poEs', text=poes))
            else:  # 'continuous' in frag
                n = Node('ffc', dict(ls=ls))
                rows = [row[2:] for row in data]  # param, value
                n.append(Node('params', dict(rows)))
            ffs_node[ordinal].append(n)
        return frag


############################# exposure #################################

COSTCOLUMNS = 'value deductible insuranceLimit retrofitted'.split()
PERIODS = 'day', 'night', 'transit', 'early_morning', 'late_afternoon'
## TODO: the occupancy periods should be inferred from the NRML file,
## not hardcoded, exactly as the cost types
## NB: they must be valid Python names, with no spaces inside


def getcosts(asset, costcolumns):
    """
    Extracts different costs from an asset node. If a cost is not available
    returns an empty string for it. Returns a list with the same length of
    the cost columns.
    """
    row = dict.fromkeys(costcolumns, '')
    for cost in asset.costs:
        for kind in COSTCOLUMNS:
            row['%s__%s' % (cost['type'], kind)] = cost.attrib.get(kind, '')
    return [row[cc] for cc in costcolumns]


def getcostcolumns(costtypes):
    """
    Extracts the kind of costs from a CostTypes node. Those will correspond
    to columns names in the .csv representation of the exposure.
    """
    cols = []
    for cost in costtypes:
        for kind in COSTCOLUMNS:
            cols.append('%s__%s' % (cost['name'], kind))
    return cols


def getoccupancies(asset):
    """
    Extracts the occupancies from an asset node.
    """
    dic = dict(('occupancy__' + occ['period'], occ['occupants'])
               for occ in asset.occupancies)
    return [dic.get('occupancy__%s' % period, '') for period in PERIODS]


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
        has_occupancies = any('occupancy__%s' % period in record
                              for period in PERIODS)
        if has_occupancies:
            occ = []
            for period in PERIODS:
                occupancy = record['occupancy__' + period]
                if occupancy:
                    occ.append(Node('occupancy',
                                    dict(occupants=occupancy, period=period)))
            nodes.append(Node('occupancies', {}, nodes=occ))
        attr = dict(id=record['id'], number=record['number'],
                    taxonomy=record['taxonomy'])
        if 'area' in record:
            attr['area'] = record['area']
        yield Node('asset', attr, nodes=nodes)


def make_asset_class(costcolumns):
    fields = dict((f.name, f) for f in records.AssetPopulation.fields)
    for cc in costcolumns:
        fields[cc] = record.Field(str)
        fields['area'] = record.Field(str)
        for period in PERIODS:
            fields['occupancy__%s' % period] = record.Field(str)
    return type('AssetBuilding', (records.AssetPopulation,), fields)


class Exposure(Converter):
    """A converter for exposureModel nodes"""

    def node_to_records(self, node):
        """
        Yield a single table object. For population exposure a table
        has a form like

          id,taxonomy,lon,lat,number
          asset_01,IT-PV,9.15000,45.16667,7
          asset_02,IT-CE,9.15333,45.12200,7

        whereas for building has a form like

          id,taxonomy,lon,lat,number,area,cost__value,..., occupancy__day
          asset_01,RC/DMRF-D/LR,9.15000,45.16667,7,120,40,.5,...,20
          asset_02,RC/DMRF-D/HR,9.15333,45.12200,7,119,40,,,...,20
          asset_03,RC/DMRF-D/LR,9.14777,45.17999,5,118,,...,,5

        with a variable number of columns depending on the metadata.
        """
        if node['category'] == 'buildings':
            for c in node.conversions.costTypes:
                yield records.CostType(c['name'], c['type'], c['unit'],
                                       c.attrib.get('retrofittedType', ''),
                                       c.attrib.get('retrofittedUnit', ''))
            costcolumns = getcostcolumns(node.conversions.costTypes)
            Asset = make_asset_class(costcolumns)
            conv = node.conversions
            yield records.Exposure(
                node['id'],
                node['category'],
                node['taxonomySource'],
                node.description.text.strip(),
                conv.area['type'],
                conv.area['unit'],
                conv.deductible['isAbsolute'],
                conv.insuranceLimit['isAbsolute'])
        else:
            Asset = records.AssetPopulation
            yield records.Exposure(
                node['id'],
                node['category'],
                node['taxonomySource'],
                node.description.text.strip())

        locations = {}  # location -> id
        loc_counter = itertools.count(1)
        for asset in node.assets:
            if node['category'] == 'buildings':
                extras = [asset['area']] + getcosts(asset, costcolumns) + \
                    getoccupancies(asset)
            else:
                extras = []
            loc = asset.location['lon'], asset.location['lat']
            try:
                loc_id = locations[loc]
            except KeyError:
                loc_id = locations[loc] = loc_counter.next()

            yield records.Location(loc_id, loc[0], loc[1])
            yield Asset(asset['id'], asset['taxonomy'], loc_id,
                        asset['number'], *extras)

    def csv_to_node(self):
        """
        Build a Node object containing a full exposure from a set
        of tables. The assets are lazily read.
        """
        exp = self.man.read(records.Exposure).next().to_node()
        if exp['category'] == 'buildings':
            exp.conversions.costTypes.nodes = ctypes = [
                c.to_node() for c in self.man.read(records.CostType)]
            costcolumns = getcostcolumns(exp.conversions.costTypes)
            Asset = make_asset_class(costcolumns)
        else:
            Asset = records.AssetPopulation
            ctypes = []
        assets = (a.to_node() for a in self.man.read(Asset))
        exp.assets.nodes = assetgenerator(assets, ctypes)
        return exp


################################# gmf ##################################

class GmfSet(Converter):
    """A converter for gmfSet/GmfCollection nodes"""

    def node_to_records(self, node):
        """
        Yield a table for each gmf node. The table has a form like

          lon,lat,gmv
          0.0,0.0,0.2
          1.0,0.0,1.4
          0.0,1.0,0.6
        """
        if node.tag == 'gmfSet':
            for gmf in node.getnodes('gmf'):
                imt = gmf['IMT']
                if imt == 'SA':
                    imt += '(%s)' % gmf['saPeriod']
                yield records.Gmf(1, imt, '')
                for n in gmf:
                    yield records.GmfData(
                        1, imt, '', n['lon'], n['lat'], n['gmv'])
            return
        yield records.GmfCollection(
            node['sourceModelTreePath'],
            node['gsimTreePath'])
        for gmfset in node.getnodes('gmfSet'):
            ses_id = gmfset['stochasticEventSetId']
            yield records.GmfSet(ses_id, gmfset['investigationTime'])
            for gmf in gmfset.getnodes('gmf'):
                rup = gmf['ruptureId']
                imt = gmf['IMT']
                if imt == 'SA':
                    imt += '(%s)' % gmf['saPeriod']
                yield records.Gmf(ses_id, imt, rup)
                for n in gmf:
                    yield records.GmfData(
                        ses_id, imt, rup, n['lon'], n['lat'], n['gmv'])

    def _csv_to_node(self, gmfset):
        """
        Build a gmfSet node from GmfData.csv
        """
        for (ses, imt, rupture), rows in self.man.groupby(
                ['stochasticEventSetId', 'imtStr', 'ruptureId'],
                records.GmfData):
            if imt.startswith('SA'):
                attr = dict(IMT='SA', saPeriod=imt[3:-1], saDamping='5')
            else:
                attr = dict(IMT=imt)
            if rupture:
                attr['ruptureId'] = rupture
            nodes = [records.GmfData(*r).to_node() for r in rows]
            gmfset.append(Node('gmf', attr, nodes=nodes))
        return gmfset

    def csv_to_node(self):
        """
        Build a gmfCollection node from GmfCollection.csv,
        GmfSet.csv and GmfData.csv
        """
        try:
            gmfcoll = self.man.read(records.GmfCollection).next()
        except Exception:  # no data for GmfCollection
            return self._csv_to_node(Node('gmfSet'))
        gmfcoll_node = gmfcoll.to_node()
        for gmfset in self.man.read(records.GmfSet):
            node = self._csv_to_node(gmfset.to_node())
            node['stochasticEventSetId'] = gmfset['stochasticEventSetId']
            node['investigationTime'] = gmfset['investigationTime']
            if node:  # the node is empty when EOF is reached
                gmfcoll_node.append(node)
        return gmfcoll_node

GmfCollection = GmfSet
