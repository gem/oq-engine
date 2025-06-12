# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

>>> from openquake.baselib.node import Node
>>> a = Node('a', {}, 'A1')
>>> b = Node('b', {'attrb': 'B'}, 'B1')
>>> root = Node('root', nodes=[a, b])
>>> root
<root {} None ...>

Node objects can be converted into nicely indented strings:

>>> print(root.to_str())
root
  a 'A1'
  b{attrb='B'} 'B1'
<BLANKLINE>

The subnodes can be retrieved with the dot notation:

>>> root.a
<a {} A1 >

The value of a node can be extracted with the `~` operator:

>>> ~root.a
'A1'

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
<Element 'root' at ...>

Then is trivial to generate the XML representation of a node:

>>> from xml.etree import ElementTree
>>> print(ElementTree.tostring(node_to_elem(root)).decode('utf-8'))
<root><a>A1</a><b attrb="B">B1</b></root>

Generating XML files larger than the available memory requires some
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
a writing routine converting a subnode at the time, without
requiring the full list of them. The routines provided by
ElementTree are no good, however baselib.writers
provide an StreamingXMLWriter just for that purpose.

Lazy trees should *not* be used unless it is absolutely necessary in
order to save memory; the problem is that if you use a lazy tree the
slice notation will not work (the underlying generator will not accept
it); moreover it will not be possible to iterate twice on the
subnodes, since the generator will be exhausted. Notice that even
accessing a subnode with the dot notation will avance the
generator. Finally, nodes containing lazy nodes will not be pickleable.
"""
import io
import sys
import copy
import types
import warnings
import itertools
import pprint as pp
import configparser
from contextlib import contextmanager
from openquake.baselib.python3compat import raise_, decode, encode
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr
from xml.parsers.expat import ParserCreate, ExpatError, ErrorString

import numpy


@contextmanager
def floatformat(fmt_string):
    """
    Context manager to change the default format string for the
    function :func:`openquake.baselib.writers.write_csv`.

    :param fmt_string: the format to use; for instance '%13.9E'
    """
    fmt_defaults = scientificformat.__defaults__
    scientificformat.__defaults__ = (fmt_string,) + fmt_defaults[1:]
    try:
        yield
    finally:
        scientificformat.__defaults__ = fmt_defaults


zeroset = set(['E', '-', '+', '.', '0'])


def scientificformat(value, fmt='%13.9E', sep=' ', sep2=':'):
    """
    :param value: the value to convert into a string
    :param fmt: the formatting string to use for float values
    :param sep: separator to use for vector-like values
    :param sep2: second separator to use for matrix-like values

    Convert a float or an array into a string by using the scientific notation
    and a fixed precision (by default 10 decimal digits). For instance:

    >>> scientificformat(-0E0)
    '0.000000000E+00'
    >>> scientificformat(-0.004)
    '-4.000000000E-03'
    >>> scientificformat([0.004])
    '4.000000000E-03'
    >>> scientificformat([0.01, 0.02], '%10.6E')
    '1.000000E-02 2.000000E-02'
    >>> scientificformat([[0.1, 0.2], [0.3, 0.4]], '%4.1E')
    '1.0E-01:2.0E-01 3.0E-01:4.0E-01'
    """
    if isinstance(value, numpy.bool_):
        return '1' if value else '0'
    elif isinstance(value, bytes):
        return value.decode('utf8', 'ignore')
    elif isinstance(value, str):
        return value
    elif hasattr(value, '__len__'):
        return sep.join((scientificformat(f, fmt, sep2) for f in value))
    elif isinstance(value, (float, numpy.float64, numpy.float32)):
        fmt_value = fmt % value
        if set(fmt_value) <= zeroset:
            # '-0.0000000E+00' is converted into '0.0000000E+00
            fmt_value = fmt_value.replace('-', '')
        return fmt_value
    return str(value)


def tostring(node, indent=4, nsmap=None):
    """
    Convert a node into an XML string by using the StreamingXMLWriter.
    This is useful for testing purposes.

    :param node: a node object (typically an ElementTree object)
    :param indent: the indentation to use in the XML (default 4 spaces)
    """
    out = io.BytesIO()
    writer = StreamingXMLWriter(out, indent, nsmap=nsmap)
    writer.serialize(node)
    return out.getvalue()


class StreamingXMLWriter(object):
    """
    A bynary stream XML writer. The typical usage is something like this::

        with StreamingXMLWriter(output_file) as writer:
            writer.start_tag('root')
            for node in nodegenerator():
                writer.serialize(node)
            writer.end_tag('root')
    """
    def __init__(self, bytestream, indent=4, encoding='utf-8', nsmap=None):
        """
        :param bytestream: the stream or file where to write the XML
        :param int indent: the indentation to use in the XML (default 4 spaces)
        """
        # guard against a common error, one must use io.BytesIO
        if isinstance(bytestream, (io.StringIO, io.TextIOWrapper)):
            raise TypeError('%r is not a byte stream' % bytestream)
        self.stream = bytestream
        self.indent = indent
        self.encoding = encoding
        self.indentlevel = 0
        self.nsmap = nsmap

    def shorten(self, tag):
        """
        Get the short representation of a fully qualified tag

        :param str tag: a (fully qualified or not) XML tag
        """
        if tag.startswith('{'):
            ns, _tag = tag.rsplit('}')
            tag = self.nsmap.get(ns[1:], '') + _tag
        return tag

    def _write(self, text):
        """
        Write text by respecting the current indentlevel
        """
        spaces = ' ' * (self.indent * self.indentlevel)
        t = spaces + text.strip() + '\n'
        if hasattr(t, 'encode'):
            t = t.encode(self.encoding, 'xmlcharrefreplace')
        self.stream.write(t)  # expected bytes

    def emptyElement(self, name, attrs):
        """
        Add an empty element (may have attributes)
        """
        attr = ' '.join('%s=%s' % (n, quoteattr(scientificformat(v)))
                        for n, v in sorted(attrs.items()))
        self._write('<%s %s/>' % (name, attr))

    def start_tag(self, name, attrs=None):
        """
        Open an XML tag
        """
        if not attrs:
            self._write('<%s>' % name)
        else:
            self._write('<' + name)
            for (name, value) in sorted(attrs.items()):
                self._write(
                    ' %s=%s' % (name, quoteattr(scientificformat(value))))
            self._write('>')
        self.indentlevel += 1

    def end_tag(self, name):
        """
        Close an XML tag
        """
        self.indentlevel -= 1
        self._write('</%s>' % name)

    def serialize(self, node):
        """
        Serialize a node object (typically an ElementTree object)
        """
        if isinstance(node.tag, types.FunctionType):
            # this looks like a bug of ElementTree: comments are stored as
            # functions!?? see https://hg.python.org/sandbox/python2.7/file/tip/Lib/xml/etree/ElementTree.py#l458
            return
        if self.nsmap is not None:
            tag = self.shorten(node.tag)
        else:
            tag = node.tag
        with warnings.catch_warnings():  # unwanted ElementTree warning
            warnings.simplefilter('ignore')
            leafnode = not node
        # NB: we cannot use len(node) to identify leafs since nodes containing
        # an iterator have no length. They are always True, even if empty :-(
        if leafnode and node.text is None:
            self.emptyElement(tag, node.attrib)
            return
        self.start_tag(tag, node.attrib)
        if node.text is not None:
            if striptag(node.tag) == 'posList':
                # NOTE: by convention, posList must be a flat list of
                #   space-separated coordinates, so we need to flatten any
                #   nested lists or tuples, producing a single list of values
                obj = node.text
                while (isinstance(obj, (list, tuple))
                       and isinstance(obj[0], (list, tuple))):
                    obj = list(itertools.chain(*obj))
                txt = escape(scientificformat(obj).strip())
            else:
                txt = scientificformat(node.text).strip()
            if txt:
                self._write(txt)
        for subnode in node:
            self.serialize(subnode)
        self.end_tag(tag)

    def __enter__(self):
        """
        Write the XML declaration
        """
        self._write('<?xml version="1.0" encoding="%s"?>\n' %
                    self.encoding)
        return self

    def __exit__(self, etype, exc, tb):
        """
        Close the XML document
        """


class SourceLineParser(ElementTree.XMLParser):
    """
    A custom parser managing line numbers: works for Python <= 3.3
    """
    def _start_list(self, tag, attrib_in):
        elem = super()._start_list(tag, attrib_in)
        elem.lineno = self.parser.CurrentLineNumber
        # there is also CurrentColumnNumber available, if wanted
        return elem


def fromstring(text):
    """Parse an XML string and return a tree"""
    return ElementTree.fromstring(text, SourceLineParser())


def parse(source, remove_comments=True, **kw):
    """Thin wrapper around ElementTree.parse"""
    return ElementTree.parse(source, SourceLineParser(), **kw)


def iterparse(source, events=('end',), remove_comments=True, **kw):
    """Thin wrapper around ElementTree.iterparse"""
    return ElementTree.iterparse(source, events, SourceLineParser(), **kw)


# ###################### utilities for the Node class ####################### #


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
        alist = ['%s=%r' % item for item in sorted(attrib.items())]
    else:
        alist = list(attrib)
    return '{%s}' % ', '.join(alist)


def _display(node, indent, expandattrs, expandvals, output,
             striptags=True, shortentags=False, nsmap=None):
    """Core function to display a Node object"""
    attrs = _displayattrs(node.attrib, expandattrs)
    if node.text is None or not expandvals:
        val = ''
    elif isinstance(node.text, str):
        val = ' %s' % repr(node.text.strip())
    else:
        val = ' %s' % repr(node.text)  # node.text can be a tuple
    tag = node.tag
    if shortentags and nsmap:
        if tag.startswith('{'):
            ns, _tag = tag.rsplit('}')
            tag = '{' + nsmap.get(ns[1:], '') + '}' + _tag
    elif striptags:
        tag = striptag(node.tag)
    output.write(encode(indent + tag + attrs + val + '\n'))
    for sub_node in node:
        _display(sub_node, indent + '  ', expandattrs, expandvals, output,
                 striptags, shortentags, nsmap)


def node_display(root, expandattrs=False, expandvals=False, output=sys.stdout,
                 striptags=True, shortentags=False, nsmap=None):
    """
    Write an indented representation of the Node object on the output;
    this is intended for testing/debugging purposes.

    :param root: a Node object
    :param bool expandattrs: if True, the values of the attributes are
                             also printed, not only the names
    :param bool expandvals: if True, the values of the tags are also printed,
                            not only the names.
    :param output: stream where to write the string representation of the node
    :param bool striptags: do not display fully qualified tag names
    :param bool shortentags: display a shorter representation of the namespace
                             (overriding the striptags parameter)
    :param dict nsmap: map of namespaces (keys are full names, values are the
                       corresponding aliases)
    """
    _display(root, '', expandattrs, expandvals, output, striptags,
             shortentags, nsmap)


def striptag(tag):
    """
    Get the short representation of a fully qualified tag

    :param str tag: a (fully qualified or not) XML tag
    """
    if tag.startswith('{'):
        return tag.rsplit('}')[1]
    return tag


class Node(object):
    """
    A class to make it easy to edit hierarchical structures with attributes,
    such as XML files. Node objects must be pickleable and must consume as
    little memory as possible. Moreover they must be easily converted from
    and to ElementTree objects. The advantage over ElementTree objects
    is that subnodes can be lazily generated and that they can be accessed
    with the dot notation.
    """
    __slots__ = ('tag', 'attrib', 'text', 'nodes', 'lineno')

    def __init__(self, fulltag, attrib=None, text=None,
                 nodes=None, lineno=None):
        """
        :param str fulltag: the Node name
        :param dict attrib: the Node attributes
        :param str text: the Node text (default None)
        :param nodes: an iterable of subnodes (default empty list)
        :param lineno: line number where the tag was read in the source xml
        """
        self.tag = fulltag
        self.attrib = {} if attrib is None else attrib
        self.text = text
        self.nodes = [] if nodes is None else nodes
        self.lineno = lineno
        if self.nodes and self.text is not None:
            raise ValueError(
                'A branch node cannot have a value, got %r' % self.text)

    def __getattr__(self, name):
        if name.startswith('_'):
            # do the magic only for public names
            raise AttributeError(name)
        for node in self.nodes:
            if striptag(node.tag) == name:
                return node
        raise AttributeError("No subnode named '%s' found in '%s'" %
                             (name, striptag(self.tag)))

    def getnodes(self, name):
        "Return the direct subnodes with name 'name'"
        for node in self.nodes:
            if striptag(node.tag) == name:
                yield node

    def append(self, node):
        "Append a new subnode"
        if not isinstance(node, self.__class__):
            raise TypeError('Expected Node instance, got %r' % node)
        self.nodes.append(node)

    def get_nsmap(self):
        return {v: k for k, v in self.attrib.items() if k.startswith('xmlns')}

    def to_str(self, expandattrs=True, expandvals=True, striptags=True,
               shortentags=False):
        """
        Convert the node into a string, intended for testing/debugging purposes

        :param expandattrs:
          print the values of the attributes if True, else print only the names
        :param expandvals:
          print the values if True, else print only the tag names
        :param bool striptags: do not display fully qualified tag names
        :param bool shortentags: display a shorter representation of the
                                 namespace (overriding the striptags parameter)
        """
        out = io.BytesIO()
        node_display(self, expandattrs, expandvals, out, striptags,
                     shortentags, self.get_nsmap())
        return decode(out.getvalue())

    def __iter__(self):
        """Iterate over subnodes"""
        return iter(self.nodes)

    def __repr__(self):
        """A condensed representation for debugging purposes"""
        return '<%s %s %s %s>' % (striptag(self.tag), self.attrib, self.text,
                                  '' if not self.nodes else '...')

    def __getitem__(self, i):
        """
        Retrieve a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, str):
            return self.attrib[i]
        else:  # assume an integer or a slice
            return self.nodes[i]

    def get(self, attr, value=None):
        """
        Get the given `attr`; if missing, returns `value` or `None`.
        """
        return self.attrib.get(attr, value)

    def __setitem__(self, i, value):
        """
        Update a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, str):
            self.attrib[i] = value
        else:  # assume an integer or a slice
            self.nodes[i] = value

    def __delitem__(self, i):
        """
        Remove a subnode, if i is an integer, or an attribute, if i
        is a string.
        """
        if isinstance(i, str):
            del self.attrib[i]
        else:  # assume an integer or a slice
            del self.nodes[i]

    def __invert__(self):
        """
        Return the value of a leaf; raise a TypeError if the node is not a leaf
        """
        if self:
            raise TypeError('%s is a composite node, not a leaf' % self)
        return self.text

    def __len__(self):
        """Return the number of subnodes"""
        return len(self.nodes)

    def __bool__(self):
        """
        Return True if there are subnodes; it does not iter on the
        subnodes, so for lazy nodes it returns True even if the
        generator is empty.
        """
        return bool(self.nodes)

    def __deepcopy__(self, memo):
        new = object.__new__(self.__class__)
        new.tag = self.tag
        new.attrib = self.attrib.copy()
        new.text = copy.copy(self.text)
        new.nodes = [copy.deepcopy(n, memo) for n in self.nodes]
        new.lineno = self.lineno
        return new

    def __getstate__(self):
        return dict((slot, getattr(self, slot))
                    for slot in self.__class__.__slots__)

    def __setstate__(self, state):
        for slot in self.__class__.__slots__:
            setattr(self, slot, state[slot])

    def __eq__(self, other):
        assert other is not None
        return all(getattr(self, slot) == getattr(other, slot)
                   for slot in self.__class__.__slots__)

    def __ne__(self, other):
        return not self.__eq__(other)


def to_literal(self):
    """
    Convert the node into a literal Python object
    """
    if not self.nodes:
        return (self.tag, self.attrib, self.text, [])
    else:
        return (self.tag, self.attrib, self.text,
                list(map(to_literal, self.nodes)))


def pprint(self, stream=None, indent=1, width=80, depth=None):
    """
    Pretty print the underlying literal Python object
    """
    pp.pprint(to_literal(self), stream, indent, width, depth)


def node_from_dict(dic, nodefactory=Node):
    """
    Convert a (nested) dictionary into a Node object.
    """
    [(tag, dic)] = dic.items()
    if isinstance(dic, dict):
        dic = dic.copy()
        text = dic.pop('text', None)
        attrib = {n[1:]: dic.pop(n) for n in sorted(dic) if n.startswith('_')}
    else:
        return nodefactory(tag, {}, dic)
    if not dic:
        return nodefactory(tag, attrib, text)
    [(k, vs)] = dic.items()
    if isinstance(vs, list):
        nodes = [node_from_dict({k: v}) for v in vs]
    else:
        nodes = [node_from_dict(dic)]
    return nodefactory(tag, attrib, nodes=nodes)


def _group(one_key_dicts):
    items = []
    for one_key_dict in one_key_dicts:
        [(k, v)] = one_key_dict.items()
        items.append((k, v))
    dic = {}
    for k, group in itertools.groupby(items, lambda item: item[0]):
        vs = []
        for k, v in group:
            vs.append(v)
        if len(vs) == 1:
            dic[k] = vs[0]
        else:
            dic[k] = vs
    return dic


def node_to_dict(node):
    """
    Convert a Node object into a (nested) dictionary
    with attributes tag, attrib, text, nodes.

    :param node: a Node-compatible object
    """
    tag = striptag(node.tag)
    dic = {}
    if node.attrib:
        for nam, val in node.attrib.items():
            dic['_' + nam] = (float(val)
                              if isinstance(val, numpy.float64) else val)
    if isinstance(node.text, str) and node.text.strip() == '':
        pass
    elif node.text is not None:
        if node.attrib:
            dic['text'] = node.text
        else:
            # TODO: ugly, dic sometimes is a dic and sometimes a scalar??
            dic = node.text
    if node.nodes:
        dic.update(_group([node_to_dict(n) for n in node]))
    return {tag: dic}


def node_from_elem(elem, nodefactory=Node, lazy=()):
    """
    Convert (recursively) an ElementTree object into a Node object.
    """
    children = list(elem)
    lineno = getattr(elem, 'lineno', None)
    if not children:
        return nodefactory(elem.tag, dict(elem.attrib), elem.text,
                           lineno=lineno)
    if striptag(elem.tag) in lazy:
        nodes = (node_from_elem(ch, nodefactory, lazy) for ch in children)
    else:
        nodes = [node_from_elem(ch, nodefactory, lazy) for ch in children]
    return nodefactory(elem.tag, dict(elem.attrib), nodes=nodes, lineno=lineno)


# taken from https://gist.github.com/651801, which comes for the effbot
def node_to_elem(root):
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
    generate_elem(output.append, root, 1)  # print "\n".join(output)
    namespace = {"Element": ElementTree.Element,
                 "SubElement": ElementTree.SubElement}
    exec("\n".join(output), globals(), namespace)
    return namespace["e1"]


def read_nodes(fname, filter_elem, nodefactory=Node, remove_comments=True):
    """
    Convert an XML file into a lazy iterator over Node objects
    satifying the given specification, i.e. a function element -> boolean.

    :param fname: file name of file object
    :param filter_elem: element specification

    In case of errors, add the file name to the error message.
    """
    try:
        for _, el in iterparse(fname, remove_comments=remove_comments):
            if filter_elem(el):
                yield node_from_elem(el, nodefactory)
                el.clear()  # save memory
    except Exception:
        etype, exc, tb = sys.exc_info()
        msg = str(exc)
        if str(fname) not in msg:
            msg = '%s in %s' % (msg, fname)
        raise_(etype, msg, tb)


def node_from_xml(xmlfile, nodefactory=Node):
    """
    Convert a .xml file into a Node object.

    :param xmlfile: a file name or file object open for reading
    """
    root = parse(xmlfile).getroot()
    return node_from_elem(root, nodefactory)


def node_to_xml(node, output, nsmap=None):
    """
    Convert a Node object into a pretty .xml file without keeping
    everything in memory. If you just want the string representation
    use tostring(node).

    :param node: a Node-compatible object (ElementTree nodes are fine)
    :param output: a binary output file
    :param nsmap: if given, shorten the tags with aliases

    """
    if nsmap:
        for ns, prefix in nsmap.items():
            if prefix:
                node['xmlns:' + prefix[:-1]] = ns
            else:
                node['xmlns'] = ns
    with StreamingXMLWriter(output, nsmap=nsmap) as w:
        w.serialize(node)


def node_from_ini(ini_file, nodefactory=Node, root_name='ini'):
    """
    Convert a .ini file into a Node object.

    :param ini_file: a filename or a file like object in read mode
    """
    fileobj = open(ini_file) if isinstance(ini_file, str) else ini_file
    cfp = configparser.ConfigParser(interpolation=None)
    cfp.read_file(fileobj)
    root = nodefactory(root_name)
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
        for name, value in sorted(subnode.attrib.items()):
            output.write(u'%s=%s\n' % (name, value))
    output.flush()


def node_copy(node, nodefactory=Node):
    """Make a deep copy of the node"""
    return nodefactory(node.tag, node.attrib.copy(), node.text,
                       [node_copy(n, nodefactory) for n in node])


@contextmanager
def context(fname, node):
    """
    Context manager managing exceptions and adding line number of the
    current node and name of the current file to the error message.

    :param fname: the current file being processed
    :param node: the current node being processed
    """
    try:
        yield node
    except Exception:
        etype, exc, tb = sys.exc_info()
        msg = 'node %s: %s, line %s of %s' % (
            striptag(node.tag), exc, getattr(node, 'lineno', '?'), fname)
        raise_(etype, msg, tb)


class ValidatingXmlParser(object):
    """
    Validating XML Parser based on Expat. It has two methods `.parse_file`
    and `.parse_bytes` returning a validated :class:`Node` object.

    :param validators: a dictionary of validation functions
    :param stop: the tag where to stop the parsing (if any)
    """
    class Exit(Exception):
        """Raised when the parsing is stopped before the end on purpose"""

    def __init__(self, validators, stop=None):
        self.validators = validators
        self.stop = stop

    @contextmanager
    def _context(self):
        self.p = ParserCreate(namespace_separator='}')
        self.p.StartElementHandler = self._start_element
        self.p.EndElementHandler = self._end_element
        self.p.CharacterDataHandler = self._char_data
        self._ancestors = []
        self._root = None
        try:
            yield
        except ExpatError as err:
            msg = '%s: %s: %s' % (self.filename, err.lineno,
                                  ErrorString(err.code))
            e = ExpatError(msg)
            e.lineno = err.lineno
            e.offset = err.offset
            e.filename = self.filename
            raise e
        except ValueError as err:
            err.lineno = self.p.CurrentLineNumber
            err.offset = self.p.CurrentColumnNumber
            err.filename = self.filename
            raise err
        except self.Exit:
            pass

    def parse_bytes(self, bytestr, isfinal=True):
        """
        Parse a byte string. If the string is very large, split it in chuncks
        and parse each chunk with isfinal=False, then parse an empty chunk
        with isfinal=True.
        """
        with self._context():
            self.filename = None
            self.p.Parse(bytestr, isfinal)
        return self._root

    def parse_file(self, file_or_fname):
        """
        Parse a file or a filename
        """
        with self._context():
            if hasattr(file_or_fname, 'read'):
                self.filename = getattr(
                    file_or_fname, 'name', file_or_fname.__class__.__name__)
                self.p.ParseFile(file_or_fname)
            else:
                self.filename = file_or_fname
                with open(file_or_fname, 'rb') as f:
                    self.p.ParseFile(f)
        return self._root

    def _start_element(self, longname, attrs):
        try:
            _xmlns, name = longname.split('}')
        except ValueError:  # no namespace in the longname
            name = tag = longname
        else:  # fix the tag with an opening brace
            tag = '{' + longname
        self._ancestors.append(
            Node(tag, attrs, lineno=self.p.CurrentLineNumber))
        if self.stop and name == self.stop:
            for anc in reversed(self._ancestors):
                self._end_element(anc.tag)
            raise self.Exit

    def _end_element(self, name):
        node = self._ancestors[-1]
        if isinstance(node.text, list):
            node.text = ''.join(node.text)
        with context(self.filename, node):
            self._root = self._literalnode(node)
        del self._ancestors[-1]
        if self._ancestors:
            self._ancestors[-1].append(self._root)

    def _char_data(self, data):
        if data:
            parent = self._ancestors[-1]
            if parent.text is None:
                parent.text = [data]
            else:
                parent.text.append(data)

    def _set_text(self, node, text, tag):
        if text is None:
            return
        try:
            val = self.validators[tag]
        except KeyError:
            return
        try:
            node.text = val(decode(text.strip()))
        except Exception as exc:
            raise ValueError('Could not convert %s->%s: %s' %
                             (tag, val.__name__, exc))

    def _set_attrib(self, node, n, tn, v):
        val = self.validators[tn]
        try:
            node.attrib[n] = val(decode(v))
        except Exception as exc:
            # NOTE: the line number and the file name are added by the
            # 'context' contextmanager
            raise ValueError(
                'Could not convert %s->%s: %s' %
                (tn, val.__name__, exc))

    def _literalnode(self, node):
        tag = striptag(node.tag)

        # cast the text
        self._set_text(node, node.text, tag)

        # cast the attributes
        for n, v in node.attrib.items():
            tn = '%s.%s' % (tag, n)
            if tn in self.validators:
                self._set_attrib(node, n, tn, v)
            elif n in self.validators:
                self._set_attrib(node, n, n, v)
        return node
