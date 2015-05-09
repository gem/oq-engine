# Copyright (c) 2010-2014, GEM Foundation.
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
from contextlib import contextmanager
from xml.sax.saxutils import escape, quoteattr

import numpy  # this is needed by the doctests, don't remove it


@contextmanager
def floatformat(fmt_string):
    """
    Context manager to change the default format string for the
    function :func:`openquake.commonlib.writers.scientificformat`.

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
    if isinstance(value, basestring):
        return value
    elif isinstance(value, (int, long)):
        return str(value)
    elif hasattr(value, '__len__'):
        return sep.join((scientificformat(f, fmt, sep2) for f in value))
    elif isinstance(value, float):
        fmt_value = fmt % value
        if set(fmt_value) <= zeroset:
            # '-0.0000000E+00' is converted into '0.0000000E+00
            fmt_value = fmt_value.replace('-', '')
        return fmt_value
    return str(value)


class StreamingXMLWriter(object):
    """
    A stream-based XML writer. The typical usage is something like this::

        with StreamingXMLWriter(output_file) as writer:
            writer.start_tag('root')
            for node in nodegenerator():
                writer.serialize(node)
            writer.end_tag('root')
    """
    def __init__(self, stream, indent=4, encoding='utf-8', nsmap=None):
        """
        :param stream: the stream or a file where to write the XML
        :param int indent: the indentation to use in the XML (default 4 spaces)
        """
        self.stream = stream
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
        """Write text by respecting the current indentlevel"""
        if not isinstance(text, str):
            text = text.encode(self.encoding, 'xmlcharrefreplace')
        spaces = ' ' * (self.indent * self.indentlevel)
        self.stream.write(spaces + text.strip() + '\n')

    def emptyElement(self, name, attrs):
        """Add an empty element (may have attributes)"""
        attr = ' '.join('%s=%s' % (n, quoteattr(scientificformat(v)))
                        for n, v in sorted(attrs.iteritems()))
        self._write('<%s %s/>' % (name, attr))

    def start_tag(self, name, attrs=None):
        """Open an XML tag"""
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
        """Close an XML tag"""
        self.indentlevel -= 1
        self._write('</%s>' % name)

    def serialize(self, node):
        """Serialize a node object (typically an ElementTree object)"""
        if self.nsmap is not None:
            tag = self.shorten(node.tag)
        else:
            tag = node.tag
        if not node and node.text is None:
            self.emptyElement(tag, node.attrib)
            return
        self.start_tag(tag, node.attrib)
        if node.text is not None:
            self._write(escape(scientificformat(node.text).strip()))
        for subnode in node:
            self.serialize(subnode)
        self.end_tag(tag)

    def __enter__(self):
        """Write the XML declaration"""
        self._write('<?xml version="1.0" encoding="%s"?>\n' %
                    self.encoding)
        return self

    def __exit__(self, etype, exc, tb):
        """Close the XML document"""
        pass


def tostring(node, indent=4):
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


def save_csv(dest, header_rows, sep=',', fmt='%12.8E', mode='wb'):
    """
    :param dest: destination filename
    :param header_rows: header + rows to save
    :param sep: separator to use (default comma)
    :param fmt: formatting string (default '%12.8E')
    :param mode: file open mode (default 'wb')
    """
    with open(dest, mode) as f:
        for row in header_rows:
            f.write(sep.join(scientificformat(col, fmt) for col in row) + '\n')
    return dest


# recursive function used internally by build_header
def _build_header(dtype, root):
    header = []
    if dtype.fields is None:
        if not root:
            return []
        return [root + (str(dtype), dtype.shape)]
    for field in dtype.fields:
        dt = dtype.fields[field][0]
        if dt.subdtype is None:  # nested
            header.extend(_build_header(dt, root + (field,)))
        else:
            numpytype = str(dt.subdtype[0])
            header.append(root + (field, numpytype, dt.shape))
    return header


def build_header(dtype):
    """
    Convert a numpy nested dtype into a list of strings suitable as header
    of csv file.

    >>> imt_dt = numpy.dtype([('PGA', float, 3), ('PGV', float, 4)])
    >>> build_header(imt_dt)
    ['PGV:float64:4', 'PGA:float64:3']
    >>> gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
    ...                       ('idx', numpy.uint32)])
    >>> build_header(gmf_dt)
    ['A-PGV:float64:4', 'A-PGA:float64:3', 'B-PGV:float64:4', 'B-PGA:float64:3', 'idx:uint32:']
    """
    header = _build_header(dtype, ())
    h = []
    for col in header:
        name = '-'.join(col[:-2])
        numpytype = col[-2]
        shape = col[-1]
        h.append(':'.join([name, numpytype, ':'.join(map(str, shape))]))
    return h


def extract_from(data, fields):
    """
    Extract data from numpy arrays with nested records.

    >>> imt_dt = numpy.dtype([('PGA', float, 3), ('PGV', float, 4)])
    >>> a = numpy.array([([1, 2, 3], [4, 5, 6, 7])], imt_dt)
    >>> extract_from(a, ['PGA'])
    array([[ 1.,  2.,  3.]])

    >>> gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
    ...                       ('idx', numpy.uint32)])
    >>> b = numpy.array([(([1, 2, 3], [4, 5, 6, 7]),
    ...                  ([1, 2, 4], [3, 5, 6, 7]), 8)], gmf_dt)
    >>> extract_from(b, ['idx'])
    array([8], dtype=uint32)
    >>> extract_from(b, ['B', 'PGV'])
    array([[ 3.,  5.,  6.,  7.]])
    """
    for f in fields:
        data = data[f]
    return data


def write_csv(dest, data, sep=',', fmt='%12.8E', header=None):
    """
    :param dest: destination filename
    :param data: array to save
    :param sep: separator to use (default comma)
    :param fmt: formatting string (default '%12.8E')
    :param header:
       optional list with the names of the columns to display
    """
    try:
        # see if data is a composite numpy array
        data.dtype.fields
    except AttributeError:
        # not a composite array
        header = header or []
    else:
        header = header or build_header(data.dtype)
    with open(dest, 'wb') as f:
        if header:
            f.write(sep.join(header) + '\n')
            all_fields = [col.split(':', 1)[0].split('-')
                          for col in header]
            for record in data:
                row = []
                for fields in all_fields:
                    row.append(extract_from(record, fields))
                f.write(sep.join(scientificformat(col, fmt)
                                 for col in row) + '\n')
        else:
            for row in data:
                f.write(sep.join(scientificformat(col, fmt)
                                 for col in row) + '\n')
    return dest
