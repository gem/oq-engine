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
from xml.sax.saxutils import XMLGenerator


class _PrettyXMLGenerator(XMLGenerator):
    """
    XMLGenerator with pretty print functionality; must be used
    from XMLWriter, which is in charging of setting the correct
    indentation level.
    """
    indentlevel = 0
    indent = '  '

    def _write(self, text):
        if not isinstance(text, str):
            text = text.encode(self._encoding, 'xmlcharrefreplace')
        self._out.write(self.indent * self.indentlevel + text + '\n')

    def startElement(self, name, attrs):
        if not attrs:
            self._write('<%s>' % name)
        else:
            XMLGenerator.startElement(self, name, attrs)


class StreamingXMLWriter(object):
    """
    A stream-based XML writer.
    """
    def __init__(self, stream, indent='  '):
        self.stream = stream
        self._xgen = _PrettyXMLGenerator(stream, 'utf-8')
        self._xgen.indentlevel = 0
        self._xgen.indent = indent

    def start_tag(self, name, attr=None):
        self._xgen.startElement(name, attr or {})
        self._xgen.indentlevel += 1

    def end_tag(self, name):
        self._xgen.indentlevel -= 1
        self._xgen.endElement(name)

    def tag(self, name, attr=None, value=None):
        self.start_tag(name, attr)
        if value:
            self._xgen.characters(value)
        self.end_tag(name)

    def serialize(self, node):
        if node.text:  # leaf node
            self.tag(node.tag, node.attrib, node.text)
            return
        self.start_tag(node.tag, node.attrib)
        for subnode in node:
            self.serialize(subnode)
        self.end_tag(node.tag)

    def __enter__(self):
        self._xgen.startDocument()
        return self

    def __exit__(self, etype, exc, tb):
        self._xgen.endDocument()


def tostring(node, indent='    '):
    """
    Convert a node into an XML string by using the StreamingXMLWriter.
    This is useful for testing purposes.
    """
    out = cStringIO.StringIO()
    writer = StreamingXMLWriter(out, indent)
    writer.serialize(node)
    return out.getvalue()
