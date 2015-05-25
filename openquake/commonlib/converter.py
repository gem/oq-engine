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
import itertools
from openquake.risklib import scientific
from openquake.commonlib.node import Node, node_from_xml, striptag
from openquake.commonlib import record, records


def groupby(records, keyfields):
    """
    Group the records on the underlying CSV according to the given
    keyfield. Assume the records are sorted.
    """
    return itertools.groupby(records, lambda r: [r[k] for k in keyfields])


class Converter(object):
    """
    Base class.
    """

    @classmethod
    def from_node(cls, node):
        """
        Return a specialized Converter instance
        """
        tag = striptag(node.tag)
        name = tag[0].upper() + tag[1:]
        clsname = name[:-5] if name.endswith('Model') else name
        if 'format' in node.attrib:  # for fragility functions
            clsname += node['format'].capitalize()
        if clsname == 'GmfSet':
            clsname = 'GmfCollection'
        convertertype = globals()[clsname]
        tset = record.TableSet(convertertype)
        tset.insert_all(convertertype.node_to_records(node))
        return convertertype(tset)

    @classmethod
    def from_nrml(cls, nrmlfile):
        """
        Return a specialized Converter instance from a file or filename
        """
        [node] = node_from_xml(nrmlfile)
        return cls.from_node(node)

    @classmethod
    def node_to_records(cls, node):
        """Convert the node into a sequence of records"""
        raise NotImplementedError

    @classmethod
    def recordtypes(cls):
        """
        Get the record classes associated to the given converter class,
        in order
        """
        rectypes = []
        for val in vars(records).itervalues():
            if (isinstance(val, record.MetaRecord) and
                    val.convertername == cls.__name__):
                rectypes.append(val)
        return sorted(rectypes, key=lambda rt: rt._ordinal)

    def __init__(self, tableset):
        self.tableset = tableset

    def __repr__(self):
        return '<%s>' % self.__class__.__name__

    def to_node(self):
        raise NotImplementedError


############################# vulnerability #################################

class Vulnerability(Converter):
    """A converter for vulnerabilityModel nodes"""

    @classmethod
    def node_to_records(cls, node):
        """Convert the node into a sequence of Vulnerability records"""
        for vset in node.getnodes('discreteVulnerabilitySet'):
            set_id = vset['vulnerabilitySetID']
            imt, imls, _min, _max, _imlUnit = ~vset.IML
            dvs = records.DiscreteVulnerabilitySet(
                set_id,
                vset['assetCategory'],
                vset['lossCategory'],
                imt)
            yield dvs
            for vf in vset.getnodes('discreteVulnerability'):
                fun_id = vf['vulnerabilityFunctionID']
                ratios = ~vf.lossRatio
                coeffs = ~vf.coefficientsVariation
                dv = records.DiscreteVulnerability(
                    set_id,
                    fun_id,
                    vf['probabilisticDistribution'])
                yield dv
                for iml, ratio, coeff in zip(imls, ratios, coeffs):
                    yield records.DiscreteVulnerabilityData(
                        set_id, fun_id, iml, ratio, coeff)

    def to_node(self):
        tset = self.tableset
        dvs_node = record.nodedict(tset.tableDiscreteVulnerabilitySet)
        dvf_node = record.nodedict(tset.tableDiscreteVulnerability)
        for (set_id, vf_id), group in groupby(
                tset.tableDiscreteVulnerabilityData,
                ['vulnerabilitySetID', 'vulnerabilityFunctionID']):
            dvf = dvf_node[set_id, vf_id]
            imt = dvs_node[(set_id,)].IML['IMT']
            coeffs = []
            ratios = []
            imls = []
            for row in group:
                imls.append(row['IML'])
                coeffs.append(row['coefficientsVariation'])
                ratios.append(row['lossRatio'])

            # check that we can instantiate a VulnerabilityFunction in risklib
            scientific.VulnerabilityFunction(
                vf_id, imt, map(float, imls),
                map(float, ratios), map(float, coeffs))

            dvf.lossRatio.text = ' '.join(ratios)
            dvf.coefficientsVariation.text = ' '.join(coeffs)
            dvs_node[(set_id,)].append(dvf)
            dvs_node[(set_id,)].IML.text = ' '.join(imls)
        return Node('vulnerabilityModel', nodes=dvs_node.values())


############################# fragility #################################

class FragilityDiscrete(Converter):
    """A converter for fragilityModel nodes"""

    @classmethod
    def node_to_records(cls, node):
        """Convert the node into a sequence of Fragility records"""
        fmt = node['format']
        assert fmt == 'discrete'
        limitStates = ~node.limitStates
        yield records.FragilityDiscrete(
            fmt, node.description.text.strip(), ' '.join(limitStates))
        for ls in limitStates:
            yield records.FFLimitStateDiscrete(ls)
        for i, ffs in enumerate(node.getnodes('ffs'), 1):
            ffs_ordinal = str(i)  # there is a ffs for each taxonomy
            imt, imls, _, _, imlUnit = ~ffs.IML
            yield records.FFSetDiscrete(
                ffs_ordinal,
                ffs.taxonomy.text.strip(),
                ffs.attrib.get('noDamageLimit', ''),
                imt,
                imlUnit)
            for ls, ffd in zip(limitStates, ffs.getnodes('ffd')):
                assert ls == ffd['ls'], 'Expected %s, got %s' % (
                    ls, ffd['ls'])
                poEs = ~ffd.poEs
                for iml, poe in zip(imls, poEs):
                    yield records.FFDataDiscrete(ls, ffs_ordinal, iml, poe)

    def to_node(self):
        """
        Build a full discrete fragility node from CSV
        """
        tset = self.tableset
        frag = tset.tableFragilityDiscrete[0].to_node()
        ffs_node = record.nodedict(tset.tableFFSetDiscrete)
        nodamage = float(ffs_node['noDamageLimit']) \
            if 'noDamageLimit' in ffs_node else None
        frag.nodes.extend(ffs_node.values())
        for (ls, ordinal), data in groupby(
                tset.tableFFDataDiscrete, ['limitState', 'ffs_ordinal']):
            data = list(data)

            # check that we can instantiate a FragilityFunction in risklib
            if nodamage:
                scientific.FragilityFunctionDiscrete(
                    ls, [nodamage] + [rec.iml for rec in data],
                    [0.0] + [rec.poe for rec in data], nodamage)
            else:
                scientific.FragilityFunctionDiscrete(
                    ls, [rec.iml for rec in data],
                    [rec.poe for rec in data], nodamage)

            imls = ' '.join(rec['iml'] for rec in data)
            ffs_node[(ordinal,)].IML.text = imls
            poes = ' '.join(rec['poe'] for rec in data)
            n = Node('ffd', dict(ls=ls))
            n.append(Node('poEs', text=poes))
            ffs_node[(ordinal,)].append(n)
        return frag


class FragilityContinuous(Converter):
    """A converter for fragilityModel nodes"""

    @classmethod
    def node_to_records(cls, node):
        """Convert the node into a sequence of Fragility records"""
        fmt = node['format']
        assert fmt == 'continuous', fmt
        limitStates = ~node.limitStates
        yield records.FragilityContinuous(
            fmt, node.description.text.strip(), ' '.join(limitStates))
        for ls in limitStates:
            yield records.FFLimitStateContinuous(ls)
        for i, ffs in enumerate(node.getnodes('ffs'), 1):
            ffs_ordinal = str(i)
            imt, imls, min_iml, max_iml, imlUnit = ~ffs.IML
            yield records.FFSetContinuous(
                ffs_ordinal,
                ffs.taxonomy.text.strip(),
                ffs.attrib.get('noDamageLimit', ''),
                ffs.attrib.get('type', ''),
                imt,
                imlUnit,
                min_iml,
                max_iml)
            for ls, ffc in zip(limitStates, ffs.getnodes('ffc')):
                assert ls == ffc['ls'], 'Expected %s, got %s' % (
                    ls, ffc['ls'])
                mean, stddev = ~ffc.params
                yield records.FFDataContinuous(
                    ls, ffs_ordinal, 'mean', mean)
                yield records.FFDataContinuous(
                    ls, ffs_ordinal, 'stddev', stddev)

    def to_node(self):
        """
        Build a full continuous fragility node from CSV
        """
        tset = self.tableset
        frag = tset.tableFragilityContinuous[0].to_node()
        ffs_node = record.nodedict(tset.tableFFSetContinuous)
        frag.nodes.extend(ffs_node.values())
        for (ls, ordinal), data in groupby(
                tset.tableFFDataContinuous, ['limitState', 'ffs_ordinal']):
            data = list(data)
            n = Node('ffc', dict(ls=ls))
            param = dict(row[2:] for row in data)  # param, value

            # check that we can instantiate a FragilityFunction in risklib
            scientific.FragilityFunctionContinuous(
                ls, float(param['mean']), float(param['stddev']))

            n.append(Node('params', param))
            ffs_node[(ordinal,)].append(n)
        return frag


############################# exposure #################################


class Exposure(Converter):
    """A converter for exposureModel nodes"""

    @classmethod
    def node_to_records(cls, node):
        """
        Convert the node into a sequence of Exposure records
        """
        taxonomysource = node.attrib.get('taxonomySource', 'UNKNOWN')
        if node['category'] == 'buildings':
            for c in node.conversions.costTypes:
                yield records.CostType(c['name'], c['type'], c['unit'],
                                       c.attrib.get('retrofittedType', ''),
                                       c.attrib.get('retrofittedUnit', ''))
            conv = node.conversions
            try:
                area = conv.area
                area_type = area['type']
                area_unit = area['unit']
            except NameError:
                area_type = ''
                area_unit = ''
            try:
                deductible_is_abs = ~conv.deductible
            except NameError:  # no <deductible> node
                deductible_is_abs = ''
            try:
                ins_limit_is_abs = ~conv.insuranceLimit
            except NameError:  # no <insuranceLimit> node
                ins_limit_is_abs = ''
            yield records.Exposure(
                node['id'],
                node['category'],
                taxonomysource,
                node.description.text.strip(),
                area_type,
                area_unit,
                deductible_is_abs,
                ins_limit_is_abs)
        else:
            yield records.Exposure(
                node['id'],
                node['category'],
                taxonomysource,
                node.description.text.strip())

        locations = {}  # location -> id
        loc_counter = itertools.count(1)
        for asset in node.assets:
            asset_ref = asset['id']

            # convert occupancies
            try:
                occupancies = asset.occupancies
            except NameError:
                occupancies = []
            for occupancy in occupancies:
                yield records.Occupancy(
                    asset_ref, occupancy['period'], occupancy['occupants'])

            # convert costs
            try:
                costs = asset.costs
            except NameError:
                costs = []
            for cost in costs:
                yield records.Cost(
                    asset_ref, cost['type'], cost['value'],
                    cost.attrib.get('retrofitted', ''),
                    cost.attrib.get('deductible', ''),
                    cost.attrib.get('insuranceLimit', ''))

            # convert locations
            loc = asset.location['lon'], asset.location['lat']
            try:  # known location
                loc_id = locations[loc]
            except KeyError:  # yield only new locations
                loc_id = locations[loc] = str(loc_counter.next())
                yield records.Location(loc_id, loc[0], loc[1])

            # convert assets
            yield records.Asset(
                loc_id, asset_ref, asset['taxonomy'],  asset['number'],
                asset.attrib.get('area', ''))

    def to_node(self):
        """
        Build a Node object containing a full exposure from a set
        of CSV files. For population exposure the CSV has a form like

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
        t = self.tableset
        exp = t.tableExposure[0].to_node()
        if exp['category'] == 'buildings':
            cost_types = [c.name for c in t.tableCostType]
            exp.conversions.costTypes.nodes = [
                c.to_node() for c in t.tableCostType]
        else:
            cost_types = []
            area_type = t.tableExposure[0].area_type
            area_unit = t.tableExposure[0].area_unit
            if area_type and area_unit:
                # insert after the description node
                exp.nodes.insert(1, Node('conversions', {}, nodes=[
                    Node('area', {'type': area_type, 'unit': area_unit})]))
        if t.tableOccupancy:
            # extract the occupancies corresponding to the first asset
            _asset_ref, occupancies = groupby(
                t.tableOccupancy, ['asset_ref']).next()
            periods = sorted(occ.period for occ in occupancies)
        else:
            periods = []
        exp.assets.nodes = self._assetgenerator(
            t.tableAsset, cost_types, periods)
        return exp

    def _assetgenerator(self, assets, costtypes, periods):
        """
        Convert assets into asset nodes.

        :param assets: asset records
        :param costtypes: the valid cost types
        :param periods: the valid periods

        :returns: an iterable over Node objects describing exposure assets
        """
        # each asset contains the subnodes location, costs and occupancies
        loc_dict = record.nodedict(self.tableset.tableLocation)
        cost_dict = record.nodedict(self.tableset.tableCost)
        occ_dict = record.nodedict(self.tableset.tableOccupancy)
        for asset in assets:
            ref = asset['asset_ref']
            nodes = []
            location = loc_dict[(asset['location_id'],)]
            nodes.append(location)

            costnodes = []
            for ctype in costtypes:
                cost = cost_dict.get((ref, ctype))
                if cost is not None:
                    costnodes.append(cost)
            if costnodes:
                nodes.append(Node('costs', {}, nodes=costnodes))

            occupancynodes = []
            for period in periods:
                occupancy = occ_dict.get((ref, period))
                if occupancy is not None:
                    occupancynodes.append(occupancy)
            if occupancynodes:
                nodes.append(Node('occupancies', {}, nodes=occupancynodes))

            assetnode = asset.to_node()
            assetnode.nodes = nodes
            yield assetnode


################################# gmf ##################################

class GmfCollection(Converter):
    """A converter for gmfSet/GmfCollection nodes"""

    @classmethod
    def node_to_records(cls, node):
        """
        Convert the node into a sequence of Gmf records
        """
        if node.tag == 'gmfSet':
            yield records.GmfSet('0', '')
            for gmf in node.getnodes('gmf'):
                imt = gmf['IMT']
                if imt == 'SA':
                    imt += '(%s)' % gmf['saPeriod']
                yield records.Gmf(1, imt, '')
                for n in gmf:
                    yield records.GmfData(
                        '0', imt, '', n['lon'], n['lat'], n['gmv'])
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

    def _to_node(self):
        """
        Add to a gmfset node all the data from a file GmfData.csv of the form::

         stochasticEventSetId,imtStr,ruptureId,lon,lat,gmv
         1,SA(0.025),,0.0,0.0,0.2
         1,SA(0.025),,1.0,0.0,1.4
         1,SA(0.025),,0.0,1.0,0.6
         1,PGA,,0.0,0.0,0.2
         1,PGA,,1.0,0.0,1.4
         1,PGA,,0.0,1.0,0.6

        The rows are grouped by ses, imt, rupture.
        """
        tset = self.tableset
        gmfset_node = record.nodedict(tset.tableGmfSet)
        for (ses, imt, rupture), rows in groupby(
                tset.tableGmfData,
                ['stochasticEventSetId', 'imtStr', 'ruptureId']):
            if imt.startswith('SA'):
                attr = dict(IMT='SA', saPeriod=imt[3:-1], saDamping='5')
            else:
                attr = dict(IMT=imt)
            if rupture:
                attr['ruptureId'] = rupture
            nodes = [records.GmfData(*r).to_node() for r in rows]
            gmfset_node[(ses,)].append(Node('gmf', attr, nodes=nodes))
        return gmfset_node

    def to_node(self):
        """
        Build a gmfCollection node from GmfCollection.csv,
        GmfSet.csv and GmfData.csv
        """
        tset = self.tableset
        try:
            gmfcoll = tset.tableGmfCollection[0]
        except IndexError:  # no data for GmfCollection
            gmfset_node = self._to_node()
            return gmfset_node.values()[0]  # there is a single node
        gmfset_node = self._to_node()
        gmfcoll_node = gmfcoll.to_node()
        for node in gmfset_node.values():
            gmfcoll_node.append(node)
        return gmfcoll_node
