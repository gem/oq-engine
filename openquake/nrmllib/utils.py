# Copyright (c) 2010-2013, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

"""
General utility functions for NRML. The most important one is the Node
class, together with a few convertion functions which are able to
convert NRML files into a hierarchical Document Object Model (DOM).
That makes it easier to read and write XML from Python. Such features
are used in the PyQt user interface to the engine input files and in
the command line convertion tools CSV<->XML. The Node class is
kept intentionally similar to an Element class, however it overcomes
the limitation of ElementTree: in particular a node can keep a lazy
iterable of subnodes, whereas ElementTree wants to keep everything
in memory.

Examples
----------------------------

The Node class is instantiated with four arguments:

1. the node tag (a mandatory string)
2. the node attributes (a mandatory dictionary)
3. the node value (a string or None)
4. the subnodes (an iterable over nodes)

If a node has subnodes, its value must be None; on the contrary, if
a node has no subnodes, its value cannot be None: this is a way
to distinguish branch nodes from leaf nodes which does not
require traversing the leafs.

For instance, here is an example of instantiating a root node
with two subnodes a and b:

>>> from openquake.nrmllib.utils import Node
>>> a = Node('a', {}, text='A1')
>>> b = Node('b', {'attrb': 'B'}, 'B1')
>>> root = Node('root', nodes=[a, b])
>>> print root.to_str()
root
  a A1
  b{attrb=B} B1
<BLANKLINE>

The subnodes can be retrieved with the dot notation:

>>> root.a
<a {} A1 >

It is possible to have multiple subnodes with the same name:

>>> root.append(Node('a', {}, 'A2'))  # add another 'a' node

Now the dot notation will not work anymore:

>>> root.a
Traceback (most recent call last):
   ...
ValueError: There are several subnodes named 'a' in 'root'

However it is possible to retrieve the node from its ordinal
index:

>>> root[0], root[1], root[2]
(<a {} A1 >, <b {'attrb': 'B'} B1 >, <a {} A2 >)

The list of all subnodes with a given name can be retrieved
as follows:

>>> list(root.getnodes('a'))
[<a {} A1 >, <a {} A2 >]

It is also possible to delete a node given its index:

>>> del root[2]

A node is an iterable object yielding its subnodes:

>>> list(root)
[<a {} A1 >, <b {'attrb': 'B'} B1 >]

The attributes of a node can be retrieved with the square bracket notation:

>>> root.b['attrb']
'B'

It is possible to add and remove attributes freely:

>>> root.b['attr'] = 'new attr'
>>> del root.b['attr']

Node objects can be easily converted into ElementTree objects:

>>> node_to_elem(root)  #doctest: +ELLIPSIS
<Element root at ...>

Thus it is trivial to generate the XML representation of a node:

>>> from lxml import etree
>>> print etree.tostring(node_to_elem(root))
<root><a>A1</a><b attrb="B">B1</b></root>

Generating large XML files is not an issue: the trick is to use a
node generator, such that it is not necessary to keep the entire
tree in memory. Here is an example:

>>> def gen_many_nodes(N):
...     for i in xrange(N):
...         yield Node('a', {}, text=str(i))

>>> lazytree = Node('lazytree', {}, nodes=gen_many_nodes(10))

The lazytree object defined here consumes no memory, because the
nodes are not created a instantiation time. They are created as
soon as you start iterating on the lazytree. In particular
list(lazytree) would generated all of them. If your goal is to
store the tree on the filesystem in XML format, you should use
a saving routing converting a subnode at the time, without
requiring the full list of them. For convenience, nrmllib.writers
provide an StreamingXMLWriter just for that purpose.

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

>> from openquake.nrmllib.utils import node_from_nrml
>> nrml = node_from_nrml(<path_to_the_exposure_file.xml>)


Then nrml will be an instance of the Node class, which defines
methods __getattr__, __getitem__, __setitem__, __delitem__ in
such a way that a nice syntax to access the tree is possible.

For instance

>> nrml.exposureModel.description
<description {} 
      Sample population
     []>
>> nrml.exposureModel.assets[0]['taxonomy']
'IT-PV'
>> nrml.exposureModel.assets[0]['id']
'asset_01'
>> nrml.exposureModel.assets[0].location['lon']
'9.15000'
>> nrml.exposureModel.assets[0].location['lat']
'45.16667'
"""

import sys
import cStringIO
import ConfigParser
from openquake.hazardlib.slots import with_slots
from openquake import nrmllib
from openquake.nrmllib.writers import StreamingXMLWriter
from lxml import etree


######################## Node management ##############################

def strip_fqtag(tag):
    "Convert a (fully qualified) tag into a valid Python identifier"
    s = str(tag)
    pieces = s.rsplit('}', 1)  # split on '}', to remove the namespace part
    if len(pieces) == 2:
        s = pieces[1]
    return s


def _displayattrs(attrib, expandattrs):
    """Helper function to display the attributes of a Node object"""
    if not attrib:
        return ''
    if expandattrs:
        alist = ['%s=%s' % (strip_fqtag(k), v)
                 for (k, v) in attrib.iteritems()]
    else:
        alist = map(strip_fqtag, attrib)
    return '{%s}' % ', '.join(alist)


def _display(node, indent, expandattrs, expandvals, output):
    """Core function to display a Node object"""
    attrs = _displayattrs(node.attrib, expandattrs)
    val = ' ' + node.text if expandvals and node.text else ''
    output.write(indent + node.tag + attrs + val + '\n')
    for sub_node in node:
        _display(sub_node, indent + '  ', expandattrs, expandvals, output)


def node_display(root, expandattrs=False, expandvals=False, output=sys.stdout):
    """
    Write an indented representation of the Node object on the output;
    this is intended for debugging purposes. If expandattrs is True,
    the values of the attributes are also printed, not only the names;
    if expandvals is true, the values of the tags are also printed,
    not only the names.
    """
    _display(root, '', expandattrs, expandvals, output)


@with_slots
class Node(object):
    """
    A class to make it easy to edit hierarchical structures with attributes,
    such as XML files. Node objects must be pickleable and must consume as
    little memory as possible. Moreover they must be easily converted from
    and to ElementTree objects. The advantage over ElementTree objects
    is that subnodes can be accessed with the dot notation (if their name
    is unique) or the square notation (if there are multiple nodes with
    the same name).
    """
    __slots__ = ('tag', 'attrib', 'text', 'nodes')

    def __init__(self, fulltag, attrib=None, text=None, nodes=None):
        """
        :param str tag: the Node name
        :param dict attrib: the Node attributes
        :param unicode text: the Node text (default None)
        :param nodes: an iterable of subnodes (default empty list)
        """
        self.tag = strip_fqtag(fulltag)
        self.attrib = {} if attrib is None else attrib
        self.text = text
        self.nodes = [] if nodes is None else nodes
        if self.nodes and self.text is not None:
            raise ValueError(
                'A branch node cannot have a value, got %r' % self.text)

    def __getattr__(self, name):
        subnodes = list(self.getnodes(name))
        if len(subnodes) == 0:
            raise NameError('No subnode named %r found in %r' %
                            (name, self.tag))
        elif len(subnodes) > 1:
            raise ValueError(
                'There are several subnodes named %r in %r' %
                (name, self.tag))
        return subnodes[0]

    def getnodes(self, name):
        "Return the direct subnodes with name 'name'"
        for node in self.nodes:
            if node.tag == name:
                yield node

    def append(self, node):
        "Append a new subnode"
        if not isinstance(node, self.__class__):
            raise TypeError('Expected Node instance, got %r' % node)
        self.nodes.append(node)

    def to_str(self, expandattrs=True, expandvals=True):
        """
        Convert the node into a string, intended for testing/debugging purposes

        :param expandattrs:
          print the values of the attributes if True, else print only the names
        :param expandvals:
          print the values if True, else print only the tag names
        """
        out = cStringIO.StringIO()
        node_display(self, expandattrs, expandvals, out)
        return out.getvalue()

    def __iter__(self):
        """Iterate over subnodes"""
        return iter(self.nodes)

    def __repr__(self):
        """A condensed representation for debugging purposes"""
        return '<%s %s %s %s>' % (self.tag, self.attrib, self.text,
                                  '' if not self.nodes else '...')

    def __getitem__(self, i):
        """
        Retrieve a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, basestring):
            return self.attrib[i]
        else:  # assume an integer or a slice
            return self.nodes[i]

    def __setitem__(self, i, value):
        """
        Update a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, basestring):
            self.attrib[i] = value
        else:  # assume an integer or a slice
            self.nodes[i] = value

    def __delitem__(self, i):
        """
        Remove a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, basestring):
            del self.attrib[i]
        else:  # assume an integer or a slice
            del self.nodes[i]

    def __len__(self):
        """Return the number of subnodes"""
        return len(self.nodes)

    def __nonzero__(self):
        """
        Return True if there are subnodes; it does not iter on the
        subnodes, so for lazy nodes it returns True even if the
        generator is empty.
        """
        return bool(self.nodes)


def node_from_dict(dic, nodecls=Node):
    """
    Convert a (nested) dictionary with attributes tag, attrib, text, nodes
    into a Node object.
    """
    tag = dic['tag']
    text = dic.get('text')
    attrib = dic.get('attrib', {})
    nodes = dic.get('nodes', [])
    if not nodes:
        return nodecls(tag, attrib, text)
    return nodecls(tag, attrib, nodes=map(node_from_dict, nodes))


def node_to_dict(self):
    """
    Convert a Node object into a (nested) dictionary
    with attributes tag, attrib, text, nodes.
    """
    dic = dict(tag=self.tag, attrib=self.attrib, text=self.text)
    if self.nodes:
        dic['nodes'] = [node_to_dict(n) for n in self]
    return dic


def node_from_elem(elem, nodecls=Node):
    """
    Convert (recursively) an ElementTree object into a Node object.
    """
    children = list(elem)
    if not children:
        return nodecls(elem.tag, dict(elem.attrib), elem.text)
    return nodecls(elem.tag, dict(elem.attrib),
                   nodes=map(node_from_elem, children))


# taken from https://gist.github.com/651801, which comes for the effbot
def node_to_elem(self):
    """
    Convert (recursively) a Node object into an ElementTree object.
    """
    def generate_elem(append, node, level):
        var = "e" + str(level)
        arg = repr(node.tag)
        if node.attrib:
            arg += ", **%r" % node.attrib
        if level == 1:
            append("e1 = Element(%s)" % arg)
        else:
            append("%s = SubElement(e%d, %s)" % (var, level - 1, arg))
        if not node.nodes:
            append("%s.text = %r" % (var, node.text))
        for x in node:
            generate_elem(append, x, level + 1)
    # generate code to create a tree
    output = []
    generate_elem(output.append, self, 1)  # print "\n".join(output)
    namespace = {"Element": etree.Element, "SubElement": etree.SubElement}
    exec "\n".join(output) in namespace
    return namespace["e1"]


def node_from_xml(xmlfile, nodecls=Node, parser=nrmllib.COMPATPARSER):
    """
    Convert a .xml file into a Node object.
    """
    root = etree.parse(xmlfile, parser).getroot()
    return node_from_elem(root, nodecls)


def node_to_xml(node, output=sys.stdout):
    """
    Convert a Node object into a pretty .xml file without keeping
    everything in memory. If you just want the string representation
    of a small tree use etree.tostring(node_to_elem(root)).
    """
    with StreamingXMLWriter(output, indent='    ') as w:
        w.serialize(node)


def node_from_nrml(xmlfile, nodecls=Node):
    """
    Convert a NRML file into a Node object.
    """
    root = nrmllib.assert_valid(xmlfile).getroot()
    node = node_from_elem(root, nodecls)
    for nsname, nsvalue in root.nsmap.iteritems():
        if nsname is None:
            node['xmlns'] = nsvalue
        else:
            node['xmlns:%s' % nsname] = nsvalue
    return node


def node_to_nrml(node, output=sys.stdout, nsmap=None):
    """
    Convert a node into a NRML file. output must be a file
    object open in write mode. If you want to perform a
    consistency check, open it in read-write mode, then it will
    be read after creation and checked against the NRML schema.

    :params node: a Node object
    :params output: a file-like object in write or read-write mode
    :params nsmap: a dictionary with the XML namespaces (default the NRML ones)
    """
    nsmap = nsmap or nrmllib.SERIALIZE_NS_MAP
    root = Node('nrml', nodes=[node])
    for nsname, nsvalue in nsmap.iteritems():
        if nsname is None:
            root['xmlns'] = nsvalue
        else:
            root['xmlns:%s' % nsname] = nsvalue
    node_to_xml(root, output)
    if hasattr(output, 'mode') and '+' in output.mode:  # read-write mode
        output.seek(0)
        nrmllib.assert_valid(output)


def node_from_ini(ini_file, nodecls=Node, root_name='ini'):
    """
    Convert a .ini file into a Node object.

    :params ini_file: a filename or a file like object in read mode

    """
    fileobj = open(ini_file) if isinstance(ini_file, basestring) else ini_file
    cfp = ConfigParser.RawConfigParser()
    cfp.readfp(fileobj)
    root = nodecls(root_name)
    sections = cfp.sections()
    for section in sections:
        params = dict(cfp.items(section))
        root.append(Node(section, params))
    return root


def node_to_ini(node, output=sys.stdout):
    """
    Convert a Node object with the right structure into a .ini file.

    :params node: a Node object
    :params output: a file-like object opened in write mode
    """
    for subnode in node:
        output.write(u'\n[%s]\n' % subnode.tag)
        for name, value in sorted(subnode.attrib.iteritems()):
            output.write(u'%s=%s\n' % (name, value))
    output.flush()


################### string manipulation routines for NRML ####################

_LINESTRING_FMT = 'LINESTRING(%s)'
_POLYGON_FMT = 'POLYGON((%s))'


def _group_point_coords(coords, dims):
    """
    Given a 1D `list` of coordinates, group them into blocks of points with a
    block size equal to ``dims``, return a 2D `list`.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    coords = [str(x) for x in coords]
    return [coords[i:i + dims] for i in xrange(0, len(coords), dims)]


def _make_wkt(fmt, points):
    """
    Given a format string and a `list` of point pairs or triples, generate a
    WKT representation of the geometry.

    :param str fmt:
        Format string for the desired type of geometry to represent with WKT.
    :param points:
        Sequence of point pairs or triples, as `list` or `tuple` objects.
    """
    wkt = fmt % ', '.join(
        [' '.join(pt) for pt in points])
    return wkt


def coords_to_poly_wkt(coords, dims):
    """
    Given a 1D list of coordinates and the desired number of dimensions,
    generate POLYGON WKT.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    points = _group_point_coords(coords, dims)
    # Form a closed loop:
    points.append(points[0])

    return _make_wkt(_POLYGON_FMT, points)


def coords_to_linestr_wkt(coords, dims):
    """
    Given a 1D list of coordinates and the desired number of dimensions,
    generate LINESTRING WKT.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    points = _group_point_coords(coords, dims)

    return _make_wkt(_LINESTRING_FMT, points)
