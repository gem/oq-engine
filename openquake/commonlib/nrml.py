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
function ``node_to_nrml(node, output)`` where output is a file
object. If you want to make sure that the generated file is valid
according to the NRML schema just open it in 'w+' mode: immediately
after writing it will be read and validated. It is also possible to
convert a NRML file into a Node object with the routine
``node_from_nrml(node, input)`` where input is the path name of the
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

>> from openquake.nrmllib.node import node_from_nrml
>> nrml = node_from_nrml(<path_to_the_exposure_file.xml>)

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
from openquake.nrmllib.node import read_nodes, node_to_xml, Node, LiteralNode
from openquake import nrmllib


def node_from_nrml(source):
    """
    Convert a NRML file into a Node object.

    :param source: a file name or file object open for reading
    """
    [node] = read_nodes(source, lambda node: node.tag.endswith('nrml'),
                        LiteralNode)
    node['xmlns'] = nrmllib.NAMESPACE
    node['xmlns:gml'] = nrmllib.GML_NAMESPACE
    return node


def node_to_nrml(node, output=sys.stdout):
    """
    Convert a node into a NRML file. output must be a file
    object open in write mode. If you want to perform a
    consistency check, open it in read-write mode, then it will
    be read after creation and checked against the NRML schema.

    :params node: a Node object
    :params output: a file-like object in write or read-write mode
    """
    assert isinstance(node, Node), node  # better safe than sorry
    root = Node('nrml', nodes=[node])
    root['xmlns'] = nrmllib.NAMESPACE
    root['xmlns:gml'] = nrmllib.GML_NAMESPACE
    node_to_xml(root, output)
    if hasattr(output, 'mode') and '+' in output.mode:  # read-write mode
        output.seek(0)
        # node_from_nrml(output)  # validate the written file
