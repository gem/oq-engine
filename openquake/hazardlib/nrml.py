# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""\
It is possible to save a Node object into a NRML file by using the
function ``write(nodes, output)`` where output is a file
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
this is a job for the Node class which can be subclassed and
supplemented by a dictionary of validators.
"""
import io
import re
import sys
import logging
import operator
import collections

import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import CallableDict, groupby
from openquake.baselib.node import (
    node_to_xml, Node, striptag, ValidatingXmlParser, floatformat)
from openquake.hazardlib import valid, sourceconverter, InvalidFile

F64 = numpy.float64
NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
NRML05 = 'http://openquake.org/xmlns/nrml/0.5'
GML_NAMESPACE = 'http://www.opengis.net/gml'
SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}
PARSE_NS_MAP = {'nrml': NAMESPACE, 'gml': GML_NAMESPACE}


class DuplicatedID(Exception):
    """Raised when two sources with the same ID are found in a source model"""


class SourceModel(collections.Sequence):
    """
    A container of source groups with attributes name, investigation_time
    and start_time. It is serialize on hdf5 as follows:

    >> with openquake.baselib.hdf5.File('/tmp/sm.hdf5', 'w') as f:
    ..    f['/'] = source_model
    """
    def __init__(self, src_groups, name='', investigation_time='',
                 start_time=''):
        self.src_groups = src_groups
        self.name = name
        self.investigation_time = investigation_time
        self.start_time = start_time

    def __getitem__(self, i):
        return self.src_groups[i]

    def __len__(self):
        return len(self.src_groups)

    def __toh5__(self):
        dic = {}
        for i, grp in enumerate(self.src_groups):
            grpname = grp.name or 'group-%d' % i
            srcs = [(src.source_id, src) for src in grp
                    if hasattr(src, '__toh5__')]
            if srcs:
                dic[grpname] = hdf5.Group(srcs, {'trt': grp.trt})
        attrs = dict(name=self.name,
                     investigation_time=self.investigation_time or 'NA',
                     start_time=self.start_time or 'NA')
        if not dic:
            raise ValueError('There are no serializable sources in %s' % self)
        return dic, attrs

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        self.src_groups = []
        for grp_name, grp in dic.items():
            trt = grp.attrs['trt']
            srcs = []
            for src_id in sorted(grp):
                src = grp[src_id]
                src.num_ruptures = src.count_ruptures()
                srcs.append(src)
            grp = sourceconverter.SourceGroup(trt, srcs, grp_name)
            self.src_groups.append(grp)


def get_tag_version(nrml_node):
    """
    Extract from a node of kind NRML the tag and the version. For instance
    from '{http://openquake.org/xmlns/nrml/0.4}fragilityModel' one gets
    the pair ('fragilityModel', 'nrml/0.4').
    """
    version, tag = re.search(r'(nrml/[\d\.]+)\}(\w+)', nrml_node.tag).groups()
    return tag, version


def to_python(fname, *args):
    """
    Parse a NRML file and return an associated Python object. It works by
    calling nrml.read() and node_to_obj() in sequence.
    """
    [node] = read(fname)
    return node_to_obj(node, fname, *args)


node_to_obj = CallableDict(keyfunc=get_tag_version, keymissing=lambda n, f: n)
# dictionary of functions with at least two arguments, node and fname


@node_to_obj.add(('ruptureCollection', 'nrml/0.5'))
def get_rupture_collection(node, fname, converter):
    return converter.convert_node(node)


default = sourceconverter.SourceConverter()  # rupture_mesh_spacing=10


@node_to_obj.add(('sourceModel', 'nrml/0.4'))
def get_source_model_04(node, fname, converter=default):
    sources = []
    source_ids = set()
    converter.fname = fname
    for src_node in node:
        src = converter.convert_node(src_node)
        if src.source_id in source_ids:
            raise DuplicatedID(
                'The source ID %s is duplicated!' % src.source_id)
        sources.append(src)
        source_ids.add(src.source_id)
    groups = groupby(
        sources, operator.attrgetter('tectonic_region_type'))
    src_groups = sorted(sourceconverter.SourceGroup(
        trt, srcs, min_mag=converter.minimum_magnitude)
                        for trt, srcs in groups.items())
    return SourceModel(src_groups, node.get('name', ''))


@node_to_obj.add(('sourceModel', 'nrml/0.5'))
def get_source_model_05(node, fname, converter=default):
    converter.fname = fname
    groups = []  # expect a sequence of sourceGroup nodes
    for src_group in node:
        if 'sourceGroup' not in src_group.tag:
            raise InvalidFile(
                '%s: you have an incorrect declaration '
                'xmlns="http://openquake.org/xmlns/nrml/0.5"; it should be '
                'xmlns="http://openquake.org/xmlns/nrml/0.4"' % fname)
        sg = converter.convert_node(src_group)
        if len(sg):
            # a source group can be empty if the source_id filtering is on
            groups.append(sg)
    itime = node.get('investigation_time')
    if itime is not None:
        itime = valid.positivefloat(itime)
    stime = node.get('start_time')
    if stime is not None:
        stime = valid.positivefloat(stime)
    return SourceModel(sorted(groups), node.get('name'), itime, stime)


validators = {
    'backarc': valid.boolean,
    'strike': valid.strike_range,
    'dip': valid.dip_range,
    'rake': valid.rake_range,
    'magnitude': valid.positivefloat,
    'lon': valid.longitude,
    'lat': valid.latitude,
    'depth': valid.float_,
    'upperSeismoDepth': valid.float_,
    'lowerSeismoDepth': valid.float_,
    'posList': valid.posList,
    'pos': valid.lon_lat,
    'aValue': float,
    'a_val': valid.floats32,
    'bValue': valid.positivefloat,
    'b_val': valid.positivefloats,
    'magScaleRel': valid.mag_scale_rel,
    'tectonicRegion': str,
    'ruptAspectRatio': valid.positivefloat,
    'maxMag': valid.positivefloat,
    'minMag': valid.positivefloat,
    'min_mag': valid.positivefloats,
    'max_mag': valid.positivefloats,
    'lengths': valid.positiveints,
    'size': valid.positiveint,
    'binWidth': valid.positivefloat,
    'bin_width': valid.positivefloats,
    'probability': valid.probability,
    'occurRates': valid.positivefloats,  # they can be > 1
    'weight': valid.probability,
    'uncertaintyWeight': float,
    'alongStrike': valid.probability,
    'downDip': valid.probability,
    'totalMomentRate': valid.positivefloat,
    'characteristicRate': valid.positivefloat,
    'char_rate': valid.positivefloats,
    'characteristicMag': valid.positivefloat,
    'char_mag': valid.positivefloats,
    'magnitudes': valid.positivefloats,
    'id': valid.simple_id,
    'occurrence_rate': valid.positivefloat,
    'rupture.id': valid.positiveint,
    'ruptureId': valid.positiveint,
    'discretization': valid.compose(valid.positivefloat, valid.nonzero),
    'IML': valid.positivefloats,  # used in NRML 0.4
    'imt': valid.intensity_measure_type,
    'imls': valid.positivefloats,
    'poes': valid.positivefloats,
    'description': valid.utf8_not_empty,
    'noDamageLimit': valid.NoneOr(valid.positivefloat),
    'poEs': valid.probabilities,
    'gsimTreePath': lambda v: v.split('_'),
    'sourceModelTreePath': lambda v: v.split('_'),
    'IMT': str,
    'saPeriod': valid.positivefloat,
    'saDamping': valid.positivefloat,
    'quantileValue': valid.positivefloat,
    'investigationTime': valid.positivefloat,
    'poE': valid.probability,
    'periods': valid.positivefloats,
    'IMLs': valid.positivefloats,
    'magBinEdges': valid.integers,
    'distBinEdges': valid.integers,
    'epsBinEdges': valid.integers,
    'lonBinEdges': valid.longitudes,
    'latBinEdges': valid.latitudes,
    'type': valid.simple_id,
    'dims': valid.positiveints,
    'iml': valid.positivefloat,
    'index': valid.positiveints,
    'value': valid.positivefloat,
    'assetLifeExpectancy': valid.positivefloat,
    'interestRate': valid.positivefloat,
    'statistics': valid.Choice('mean', 'quantile'),
    'gmv': valid.positivefloat,
    'spacing': valid.positivefloat,
    'srcs_weights': valid.positivefloats,
    'grp_probability': valid.probability,
}


def read_source_models(fnames, converter, monitor):
    """
    :param fnames:
        list of source model files
    :param converter:
        a SourceConverter instance
    :param monitor:
        a :class:`openquake.performance.Monitor` instance
    :yields:
        SourceModel instances
    """
    for fname in fnames:
        if fname.endswith(('.xml', '.nrml')):
            sm = to_python(fname, converter)
        elif fname.endswith('.hdf5'):
            sm = sourceconverter.to_python(fname, converter)
        else:
            raise ValueError('Unrecognized extension in %s' % fname)
        sm.fname = fname
        yield sm


def read(source, chatty=True, stop=None):
    """
    Convert a NRML file into a validated Node object. Keeps
    the entire tree in memory.

    :param source:
        a file name or file object open for reading
    """
    vparser = ValidatingXmlParser(validators, stop)
    nrml = vparser.parse_file(source)
    if striptag(nrml.tag) != 'nrml':
        raise ValueError('%s: expected a node of kind nrml, got %s' %
                         (source, nrml.tag))
    # extract the XML namespace URL ('http://openquake.org/xmlns/nrml/0.5')
    xmlns = nrml.tag.split('}')[0][1:]
    if xmlns != NRML05 and chatty:
        # for the moment NRML04 is still supported, so we hide the warning
        logging.debug('%s is at an outdated version: %s', source, xmlns)
    nrml['xmlns'] = xmlns
    nrml['xmlns:gml'] = GML_NAMESPACE
    return nrml


def write(nodes, output=sys.stdout, fmt='%.7E', gml=True, xmlns=None):
    """
    Convert nodes into a NRML file. output must be a file
    object open in write mode. If you want to perform a
    consistency check, open it in read-write mode, then it will
    be read after creation and validated.

    :params nodes: an iterable over Node objects
    :params output: a file-like object in write or read-write mode
    :param fmt: format used for writing the floats (default '%.7E')
    :param gml: add the http://www.opengis.net/gml namespace
    :param xmlns: NRML namespace like http://openquake.org/xmlns/nrml/0.4
    """
    root = Node('nrml', nodes=nodes)
    namespaces = {xmlns or NRML05: ''}
    if gml:
        namespaces[GML_NAMESPACE] = 'gml:'
    with floatformat(fmt):
        node_to_xml(root, output, namespaces)
    if hasattr(output, 'mode') and '+' in output.mode:  # read-write mode
        output.seek(0)
        read(output)  # validate the written file


def to_string(node):
    """
    Convert a node into a string in NRML format
    """
    with io.BytesIO() as f:
        write([node], f)
        return f.getvalue().decode('utf-8')


if __name__ == '__main__':
    import sys
    for fname in sys.argv[1:]:
        print('****** %s ******' % fname)
        print(read(fname).to_str())
        print()
