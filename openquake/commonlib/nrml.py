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
"""
From Node objects to NRML files and viceversa
------------------------------------------------------

It is possible to save a Node object into a NRML file by using the
function ``write(node, output)`` where output is a file
object. If you want to make sure that the generated file is valid
according to the NRML schema just open it in 'w+' mode: immediately
after writing it will be read and validated. It is also possible to
convert a NRML file into a Node object with the routine
``read(node, input)`` where input is the path name of the
NRML file or a file object opened for reading. The file will be
validated as soon as opened.

For instance an exposure file like the following::

  <?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
        xmlns:gml="http://www.opengis.net/gml">
    <exposureModel
        id="my_exposure_model_for_population"
        category="population"
        taxonomySource="fake population datasource">

      <description>
        Sample population
      </description>

      <assets>
        <asset id="asset_01" number="7" taxonomy="IT-PV">
            <location lon="9.15000" lat="45.16667" />
        </asset>

        <asset id="asset_02" number="7" taxonomy="IT-CE">
            <location lon="9.15333" lat="45.12200" />
        </asset>
      </assets>
    </exposureModel>
  </nrml>

can be converted as follows:

>> nrml = read(<path_to_the_exposure_file.xml>)

Then subnodes and attributes can be conveniently accessed:

>> nrml.exposureModel.assets[0]['taxonomy']
'IT-PV'
>> nrml.exposureModel.assets[0]['id']
'asset_01'
>> nrml.exposureModel.assets[0].location['lon']
'9.15000'
>> nrml.exposureModel.assets[0].location['lat']
'45.16667'

The Node class provides no facility to cast strings into Python types;
this is a job for the LiteralNode class which can be subclassed and
supplemented by a dictionary of validators.
"""

import sys
import collections
from openquake.commonlib import valid
from openquake.commonlib.node import node_to_xml, \
    Node, LiteralNode, iterparse, node_from_elem

NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
GML_NAMESPACE = 'http://www.opengis.net/gml'
SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}
PARSE_NS_MAP = {'nrml': NAMESPACE, 'gml': GML_NAMESPACE}


class NRMLFile(object):
    """
    Context-managed output object which accepts either a path or a file-like
    object.

    Behaves like a file.
    """

    def __init__(self, dest, mode='r'):
        self._dest = dest
        self._mode = mode
        self._file = None

    def __enter__(self):
        if isinstance(self._dest, (basestring, buffer)):
            self._file = open(self._dest, self._mode)
        else:
            # assume it is a file-like; don't change anything
            self._file = self._dest
        return self._file

    def __exit__(self, *args):
        self._file.close()


class Register(collections.OrderedDict):
    def add(self, *tags):
        def dec(obj):
            for tag in tags:
                self[tag] = obj
            return obj
        return dec

registry = Register()


@registry.add('sourceModel', 'simpleFaultRupture', 'complexFaultRupture',
              'singlePlaneRupture', 'multiPlanesRupture')
class ValidNode(LiteralNode):
    """
    A subclass of LiteralNode to be used when parsing sources and
    ruptures from NRML files.
    """
    validators = valid.parameters(
        strike=valid.strike_range,  # needed for the moment
        dip=valid.dip_range,  # needed for the moment
        rake=valid.rake_range,  # needed for the moment
        magnitude=valid.positivefloat,
        lon=valid.longitude,
        lat=valid.latitude,
        depth=valid.positivefloat,
        upperSeismoDepth=valid.positivefloat,
        lowerSeismoDepth=valid.positivefloat,
        posList=valid.posList,
        pos=valid.lon_lat,
        aValue=float,
        bValue=valid.positivefloat,
        magScaleRel=valid.mag_scale_rel,
        tectonicRegion=str,
        ruptAspectRatio=valid.positivefloat,
        maxMag=valid.positivefloat,
        minMag=valid.positivefloat,
        binWidth=valid.positivefloat,
        probability=valid.probability,
        hypocenter=valid.point3d,
        topLeft=valid.point3d,
        topRight=valid.point3d,
        bottomLeft=valid.point3d,
        bottomRight=valid.point3d,
        hypoDepth=valid.probability_depth,
        nodalPlane=valid.nodal_plane,
        occurRates=valid.positivefloats,
        probs_occur=valid.pmf,
        )


@registry.add('siteModel')
class SiteModelNode(LiteralNode):
    validators = valid.parameters(site=valid.site_param)


@registry.add('vulnerabilityModel')
class VulnerabilityNode(LiteralNode):
    """
    Literal Node class used to validate discrete vulnerability functions
    """
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name_with_dashes,
        assetCategory=str,
        # the assetCategory here has nothing to do with the category
        # in the exposure model and it is not used by the engine
        lossCategory=valid.name,
        IML=valid.IML,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
        probabilisticDistribution=valid.Choice('LN', 'BT'),
    )


@registry.add('fragilityModel')
class FragilityNode(LiteralNode):
    validators = valid.parameters(
        format=valid.ChoiceCI('discrete', 'continuous'),
        lossCategory=valid.name,
        IML=valid.IML,
        params=valid.fragilityparams,
        limitStates=valid.namelist,
        description=valid.utf8,
        type=valid.ChoiceCI('lognormal'),
        poEs=valid.probabilities,
        noDamageLimit=valid.positivefloat,
    )

valid_loss_types = valid.Choice('structural', 'nonstructural', 'contents',
                                'business_interruption', 'occupants')


@registry.add('aggregateLossCurve', 'hazardCurves', 'hazardMap')
class CurveNode(LiteralNode):
    validators = valid.parameters(
        investigationTime=valid.positivefloat,
        loss_type=valid_loss_types,
        unit=str,
        poEs=valid.probabilities,
        gsimTreePath=lambda v: v.split('_'),
        sourceModelTreePath=lambda v: v.split('_'),
        losses=valid.positivefloats,
        averageLoss=valid.positivefloat,
        stdDevLoss=valid.positivefloat,
        poE=valid.positivefloat,
        IMLs=valid.positivefloats,
        pos=valid.lon_lat,
        IMT=str,
        saPeriod=valid.positivefloat,
        saDamping=valid.positivefloat,
        node=valid.lon_lat_iml,
        quantileValue=valid.positivefloat,
    )


@registry.add('bcrMap')
class BcrNode(LiteralNode):
    validators = valid.parameters(
        assetLifeExpectancy=valid.positivefloat,
        interestRate=valid.positivefloat,
        lossCategory=str,
        lossType=valid_loss_types,
        quantileValue=valid.positivefloat,
        statistics=valid.Choice('quantile'),
        unit=str,
        pos=valid.lon_lat,
        aalOrig=valid.positivefloat,
        aalRetr=valid.positivefloat,
        ratio=valid.positivefloat)


def asset_mean_stddev(value, assetRef, mean, stdDev):
    return assetRef, valid.positivefloat(mean), valid.positivefloat(stdDev)


@registry.add('collapseMap')
class CollapseNode(LiteralNode):
    validators = valid.parameters(
        pos=valid.lon_lat,
        cf=asset_mean_stddev,
    )


def damage_triple(value, ds, mean, stddev):
    return ds, valid.positivefloat(mean), valid.positivefloat(stddev)


@registry.add('totalDmgDist', 'dmgDistPerAsset', 'dmgDistPerTaxonomy')
class DamageNode(LiteralNode):
    validators = valid.parameters(
        damage=damage_triple,
        pos=valid.lon_lat,
        damageStates=valid.namelist,
    )


registry.add('disaggMatrices',
             'exposureModel',
             'gmfCollection',
             'gmfSet',
             'logicTree',
             'lossCurves',
             'lossFraction',
             'lossMap',
             'stochasticEventSet',
             'stochasticEventSetCollection',
             'uniformHazardSpectra',
             )(LiteralNode)


def read(source):
    """
    Convert a NRML file into a validated LiteralNode object.

    :param source:
        a file name or file object open for reading
    """
    elements = iterparse(source, ('start',), remove_comments=True)
    _event, nrml = elements.next()
    assert LiteralNode.strip_fqtag(nrml.tag) == 'nrml', nrml.tag
    _event, content = elements.next()
    tag = LiteralNode.strip_fqtag(content.tag)
    nodecls = registry[tag]
    subnode = node_from_elem(content, nodecls)
    return LiteralNode(
        'nrml', {'xmlns': NAMESPACE, 'xmlns:gml': GML_NAMESPACE},
        nodes=[subnode])


def write(node, output=sys.stdout):
    """
    Convert a node into a NRML file. output must be a file
    object open in write mode. If you want to perform a
    consistency check, open it in read-write mode, then it will
    be read after creation and validated.

    :params node: a Node object
    :params output: a file-like object in write or read-write mode
    """
    assert isinstance(node, Node), node  # better safe than sorry
    root = Node('nrml', nodes=[node])
    root['xmlns'] = NAMESPACE
    root['xmlns:gml'] = GML_NAMESPACE
    node_to_xml(root, output)
    if hasattr(output, 'mode') and '+' in output.mode:  # read-write mode
        output.seek(0)
        read(output)  # validate the written file


if __name__ == '__main__':
    import sys
    for fname in sys.argv[1:]:
        print '****** %s ******' % fname
        print read(fname).to_str()
        print
