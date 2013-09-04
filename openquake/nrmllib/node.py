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
This module defines a Node class, together with a few conversion
functions which are able to convert NRML files into hierarchical
objects (DOM). That makes it easier to read and write XML from Python
and viceversa. Such features are used in the command-line conversion
tools. The Node class is kept intentionally similar to an
Element class, however it overcomes the limitation of ElementTree: in
particular a node can manage a lazy iterable of subnodes, whereas
ElementTree wants to keep everything in memory. Moreover the Node
class provides a convenient dot notation to access subnodes.

The Node class is instantiated with four arguments:

1. the node tag (a mandatory string)
2. the node attributes (a dictionary)
3. the node value (a string or None)
4. the subnodes (an iterable over nodes)

If a node has subnodes, its value should be None.

For instance, here is an example of instantiating a root node
with two subnodes a and b:

>>> from openquake.nrmllib.node import Node
>>> a = Node('a', {}, 'A1')
>>> b = Node('b', {'attrb': 'B'}, 'B1')
>>> root = Node('root', nodes=[a, b])
>>> root
<root {} None ...>

Node objects can be converted into nicely indented strings:

>>> print root.to_str()
root
  a A1
  b{attrb=B} B1
<BLANKLINE>

The subnodes can be retrieved with the dot notation:

>>> root.a
<a {} A1 >

If there are multiple subnodes with the same name

>>> root.append(Node('a', {}, 'A2'))  # add another 'a' node

the dot notation will retrieve the first node.
It is possible to retrieve the other nodes from the ordinal
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

Then is trivial to generate the XML representation of a node:

>>> from lxml import etree
>>> print etree.tostring(node_to_elem(root))
<root><a>A1</a><b attrb="B">B1</b></root>

Generating XML files larger than the available memory require some
care. The trick is to use a node generator, such that it is not
necessary to keep the entire tree in memory. Here is an example:

>>> def gen_many_nodes(N):
...     for i in xrange(N):
...         yield Node('a', {}, 'Text for node %d' % i)

>>> lazytree = Node('lazytree', {}, nodes=gen_many_nodes(10))

The lazytree object defined here consumes no memory, because the
nodes are not created a instantiation time. They are created as
soon as you start iterating on the lazytree. In particular
list(lazytree) will generated all of them. If your goal is to
store the tree on the filesystem in XML format you should use
a writing routing converting a subnode at the time, without
requiring the full list of them. The routines provided by lxml
and ElementTree are no good, however nrmllib.writers
provide an StreamingXMLWriter just for that purpose.

Lazy trees should *not* be used unless it is necessary to save
memory; the problem is that if you use a lazy tree the slice
notation will not work (the underlying generator will not accept
it); moreover it will not be possible to iterate twice on the
subnodes, since the generator will be exhausted. Notice that
even accessing a subnode with the dot notation will avance the
generator.

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

>> from openquake.nrmllib.utils import node_from_nrml
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
this is a job for a separate library which should be able to
understand the types defined in the XSD schema.
"""

import sys
import cStringIO
import ConfigParser
from openquake.hazardlib.slots import with_slots
from openquake import nrmllib
from openquake.nrmllib.writers import StreamingXMLWriter
from lxml import etree


########################## various utilities ##############################

def strip_fqtag(tag):
    """
    Get the short representation of a fully qualified tag

    :param str tag: a (fully qualified or not) XML tag
    """
    s = str(tag)
    pieces = s.rsplit('}', 1)  # split on '}', to remove the namespace part
    if len(pieces) == 2:
        s = pieces[1]
    return s


def _displayattrs(attrib, expandattrs):
    """
    Helper function to display the attributes of a Node object in lexicographic
    order.

    :param attrib: dictionary with the attributes
    :param expandattrs: if True also displays the value of the attributes
    """
    if not attrib:
        return ''
    if expandattrs:
        alist = ['%s=%s' % item for item in sorted(attrib.iteritems())]
    else:
        alist = attrib.keys()
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
    this is intended for testing/debugging purposes.

    :param root: a Node object
    :param bool expandattrs: if True, the values of the attributes are
                             also printed, not only the names
    :param bool expandvals: if True, the values of the tags are also printed,
                            not only the names.
    :param output: stream where to write the string representation of the node
    """
    _display(root, '', expandattrs, expandvals, output)


@with_slots
class Node(object):
    """
    A class to make it easy to edit hierarchical structures with attributes,
    such as XML files. Node objects must be pickleable and must consume as
    little memory as possible. Moreover they must be easily converted from
    and to ElementTree objects. The advantage over ElementTree objects
    is that subnodes can be lazily generated and that they can be accessed
    with the dot notation.
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
        for node in self.nodes:
            if node.tag == name:
                return node
        raise NameError('No subnode named %r found in %r' %
                        (name, self.tag))

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


def node_to_dict(node):
    """
    Convert a Node object into a (nested) dictionary
    with attributes tag, attrib, text, nodes.

    :param node: a Node-compatible object
    """
    dic = dict(tag=node.tag, attrib=node.attrib, text=node.text)
    if node.nodes:
        dic['nodes'] = [node_to_dict(n) for n in node]
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

    :param xmlfile: a file name or file object open for reading
    """
    root = etree.parse(xmlfile, parser).getroot()
    return node_from_elem(root, nodecls)


def node_to_xml(node, output=sys.stdout):
    """
    Convert a Node object into a pretty .xml file without keeping
    everything in memory. If you just want the string representation
    use nrml.writers.tostring(node).

    :param node: a Node-compatible object
                 (lxml nodes and ElementTree nodes are fine)

    """
    with StreamingXMLWriter(output) as w:
        w.serialize(node)


def node_from_nrml(xmlfile, nodecls=Node):
    """
    Convert a NRML file into a Node object.

    :param xmlfile: a file name or file object open for reading
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

    :param ini_file: a filename or a file like object in read mode
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
