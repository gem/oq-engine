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

import cStringIO
from xml.sax.saxutils import XMLGenerator, quoteattr


class _PrettyXMLGenerator(XMLGenerator):
    """
    XMLGenerator with pretty print functionality; must be used
    from XMLWriter, which is in charge of setting the correct
    indentation level.
    """
    indentlevel = 0
    indent = '  '

    def _write(self, text):
        """Write text by respecting the current indentlevel"""
        if not isinstance(text, str):
            text = text.encode(self._encoding, 'xmlcharrefreplace')
        self._out.write(self.indent * self.indentlevel + text + '\n')

    def startElement(self, name, attrs):
        """Start an element"""
        if not attrs:
            self._write('<%s>' % name)
        else:
            XMLGenerator.startElement(self, name, attrs)

    def emptyElement(self, name, attrs):
        """Add an empty element (may have attributes)"""
        attr = ' '.join('%s=%s' % (n, quoteattr(v))
                        for n, v in sorted(attrs.iteritems()))
        self._write('<%s %s/>' % (name, attr))


class StreamingXMLWriter(object):
    """
    A stream-based XML writer. The typical usage is something like this::

        with StreamingXMLWriter(output_file) as writer:
            writer.start_tag('root')
            for node in nodegenerator():
                writer.serialize(node)
            writer.end_tag('root')
    """
    def __init__(self, stream, indent='    '):
        """
        :param stream: the stream or a file where to write the XML
        :param indent: the indentation to use in the XML (default 4 spaces)
        """
        self.stream = stream
        self._xgen = _PrettyXMLGenerator(stream, 'utf-8')
        self._xgen.indentlevel = 0
        self._xgen.indent = indent

    def start_tag(self, name, attr=None):
        """Open an XML tag"""
        self._xgen.startElement(name, attr or {})
        self._xgen.indentlevel += 1

    def end_tag(self, name):
        """Close an XML tag"""
        self._xgen.indentlevel -= 1
        self._xgen.endElement(name)

    def tag(self, name, attr=None, value=None):
        """Add a complete XML tag"""
        self.start_tag(name, attr)
        if value:
            self._xgen.characters(value)
        self.end_tag(name)

    def serialize(self, node):
        """Serialize a node object (typically an ElementTree object)"""
        if not node and not node.text:
            self._xgen.emptyElement(node.tag, node.attrib)
            return
        self.start_tag(node.tag, node.attrib)
        if node.text:
            self._xgen.characters(node.text)
        for subnode in node:
            self.serialize(subnode)
        self.end_tag(node.tag)

    def __enter__(self):
        """Write the XML declaration"""
        self._xgen.startDocument()
        return self

    def __exit__(self, etype, exc, tb):
        """Close the XML document"""
        self._xgen.endDocument()


def tostring(node, indent='    '):
    """
    Convert a node into an XML string by using the StreamingXMLWriter.
    This is useful for testing purposes.

    :param node: a node object (typically an ElementTree object)
    :param indent: the indentation to use in the XML (default 4 spaces)
    """
    out = cStringIO.StringIO()
    writer = StreamingXMLWriter(out, indent)
    writer.serialize(node)
    return out.getvalue()
