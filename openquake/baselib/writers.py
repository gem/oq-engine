# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2026 GEM Foundation
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

import os
import csv
import html
import functools
import tempfile
import numpy  # this is needed by the doctests, don't remove it
import pandas
from openquake.baselib.node import scientificformat
from openquake.baselib.general import decode
from openquake.baselib.hdf5 import FLOAT, INT

FIVEDIGITS = '%.5E'


# recursive function used internally by build_header
def _build_header(dtype, root):
    header = []
    if dtype.fields is None:
        if not root:
            return []
        return [root + (str(dtype), dtype.shape)]
    for field in dtype.names:
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

    >>> imt_dt = numpy.dtype([('PGA', numpy.float32, 3),
    ...                       ('PGV', numpy.float32, 4)])
    >>> build_header(imt_dt)
    ['PGA:3', 'PGV:4']
    >>> gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
    ...                       ('idx', numpy.uint32)])
    >>> build_header(gmf_dt)
    ['A~PGA:3', 'A~PGV:4', 'B~PGA:3', 'B~PGV:4', 'idx']
    """
    header = _build_header(dtype, ())
    h = []
    for col in header:
        name = '~'.join(col[:-2])
        shape = col[-1]
        coldescr = name
        if shape:
            coldescr += ':' + ':'.join(map(str, shape))
        h.append(coldescr)
    return h


def extract_from(data, fields):
    """
    Extract data from numpy arrays with nested records.

    >>> imt_dt = numpy.dtype([('PGA', float, 3), ('PGV', float, 4)])
    >>> a = numpy.array([([1, 2, 3], [4, 5, 6, 7])], imt_dt)
    >>> extract_from(a, ['PGA'])
    array([[1., 2., 3.]])

    >>> gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
    ...                       ('idx', numpy.uint32)])
    >>> b = numpy.array([(([1, 2, 3], [4, 5, 6, 7]),
    ...                  ([1, 2, 4], [3, 5, 6, 7]), 8)], gmf_dt)
    >>> extract_from(b, ['idx'])
    array([8], dtype=uint32)
    >>> extract_from(b, ['B', 'PGV'])
    array([[3., 5., 6., 7.]])
    """
    for f in fields:
        data = data[f]
    return data


def _header(fields, renamedict):
    if renamedict:
        fields = [renamedict.get(f, f) for f in fields]
    return fields


def convert_item(item):
    # avoids numpy v2 conversion issues
    name, value = item
    if isinstance(value, (numpy.float32, numpy.float64)):
        value = float(value)
    if isinstance(value, (numpy.uint32, numpy.uint64,
                          numpy.int32, numpy.int64)):
        value = int(value)
    return '%s=%r' % (name, value)


def write_csv(dest, data, sep=',', fmt='%.6E', header=(), comment=None,
              renamedict=None):
    """
    :param dest: None, file, filename or io.StringIO instance
    :param data: array to save
    :param sep: separator to use (default comma)
    :param fmt: formatting string (default '%12.8E')
    :param header:
       optional list with the names of the columns to display
    :param comment:
       optional comment dictionary
    """
    if comment is not None:
        comment = ', '.join(convert_item(item) for item in comment.items()
                            if item[1] is not None)
    close = True
    if dest is None:  # write on a temporary file
        fd, dest = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
    if hasattr(dest, 'write'):
        # file-like object in append mode
        # it must be closed by client code
        close = False
    elif not hasattr(dest, 'getvalue'):
        # assume dest is a filename
        dest = open(dest, 'w', newline='', encoding='utf-8')
    w = csv.writer(dest, delimiter=sep)
    try:
        # see if data is a composite numpy array
        data.dtype.fields
    except AttributeError:
        # not a composite array
        autoheader = []
    else:
        autoheader = build_header(data.dtype)

    nfields = len(autoheader) or len(header) or len(data[0])
    if comment:
        w.writerow(['#'] + [''] * (nfields - 2) + [comment])

    someheader = header or autoheader
    if header != 'no-header' and someheader:
        w.writerow(_header(someheader, renamedict))

    def format(val):
        return scientificformat(val, fmt)

    if autoheader:
        all_fields = [col.split(':', 1)[0].split('~')
                      for col in autoheader]
        for record in data:
            row = []
            for fields in all_fields:
                val = extract_from(record, fields)
                if fields[0] in ('lon', 'lat', 'depth'):
                    row.append('%.5f' % val)
                else:
                    row.append(format(val))
            w.writerow(_header(row, renamedict))
    else:
        for row in data:
            w.writerow([format(col) for col in row])
    if hasattr(dest, 'getvalue'):
        return
    elif close:
        dest.close()
    return dest.name


class CsvWriter(object):
    """
    Class used in the exporters to save a bunch of CSV files
    """
    def __init__(self, sep=',', fmt='%12.8E'):
        self.sep = sep
        self.fmt = fmt
        self.fnames = set()

    def save(self, data, fname, header=(), comment=None, renamedict=None):
        """
        Save data on fname.

        :param data: numpy array, list of lists or pandas DataFrame
        :param fname: path name
        :param header: header to use
        :param comment: optional dictionary to be converted in a comment
        :param renamedict: a dictionary for renaming the columns
        """
        if isinstance(data, pandas.DataFrame):
            if comment is None:
                data.to_csv(fname, index=False, float_format=self.fmt,
                            lineterminator='\r\n', na_rep='nan')
            else:
                write_csv(fname, [], self.sep, self.fmt, list(data.columns),
                          comment=comment)
                data.to_csv(fname, index=False, float_format=self.fmt,
                            lineterminator='\r\n', na_rep='nan',
                            header=False, mode='a')
        else:
            write_csv(fname, data, self.sep, self.fmt, header, comment,
                      renamedict)
        self.fnames.add(getattr(fname, 'name', fname))

    def save_block(self, data, dest):
        """
        Save data on dest, which is a file open in 'a' mode
        """
        write_csv(dest, data, self.sep, self.fmt, 'no-header')

    def getsaved(self):
        """
        Returns the list of files saved by this CsvWriter
        """
        return sorted(self.fnames)


def castable_to_int(s):
    """
    Return True if the string `s` can be interpreted as an integer
    """
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


def parse_header(header):
    """
    Convert a list of the form `['fieldname:fieldtype:fieldsize',...]`
    into a numpy composite dtype. The parser understands headers generated
    by :func:`openquake.baselib.writers.build_header`.
    Here is an example:

    >>> parse_header(['PGA:float32', 'PGV', 'avg:float32:2'])
    (['PGA', 'PGV', 'avg'], dtype([('PGA', '<f4'), ('PGV', '<f4'), ('avg', '<f4', (2,))]))

    :params header: a list of type descriptions
    :returns: column names and the corresponding composite dtype
    """
    triples = []
    fields = []
    for col_str in header:
        col = col_str.strip().split(':')
        n = len(col)
        if n == 1:  # default dtype and no shape
            col = [col[0], 'float32', '']
        elif n == 2:
            if castable_to_int(col[1]):  # default dtype and shape
                col = [col[0], 'float32', col[1]]
            else:  # dtype and no shape
                col = [col[0], col[1], '']
        elif n > 3:
            raise ValueError('Invalid column description: %s' % col_str)
        field = col[0]
        numpytype = col[1]
        shape = () if not col[2].strip() else (int(col[2]),)
        triples.append((field, numpytype, shape))
        fields.append(field)
    return fields, numpy.dtype(triples)


def form(value):
    """
    Format numbers in a nice way.

    >>> form(0)
    '0'
    >>> form(0.0)
    '0.0'
    >>> form(0.0001)
    '1.000E-04'
    >>> form(1003.4)
    '1_003'
    >>> form(103.41)
    '103.4100'
    >>> form(9.3)
    '9.3000'
    >>> form(-1.2)
    '-1.2'
    """
    if isinstance(value, FLOAT + INT):
        if not numpy.isfinite(value):
            return str(value)
        elif value <= 0:
            return str(value)
        elif value < .001:
            return '%.3E' % value
        elif value <= 180 and isinstance(value, FLOAT):
            return '%.4f' % value
        elif value > 1000:
            return '{:_d}'.format(int(round(value)))
        else:  # in the range 10-1000
            return str(round(value, 1))
    elif isinstance(value, bytes):
        return decode(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, numpy.object_):
        return str(value)
    elif hasattr(value, '__len__') and len(value) > 1:
        return ' '.join(map(form, value))
    return str(value)


class HtmlTable(object):
    """
    Convert a sequence header+body into a HTML table.
    """
    css = """\
    tr.evenRow { background-color: lightgreen }
    tr.oddRow { }
    th { background-color: lightblue }
    """
    maxrows = 5000
    border = "1"
    summary = ""

    def __init__(self, header_plus_body, name='noname',
                 empty_table='Empty table'):
        header, body = header_plus_body[0], header_plus_body[1:]
        self.name = name
        self.empty_table = empty_table
        rows = []  # rows is a finite sequence of tuples
        for i, row in enumerate(body):
            if i == self.maxrows:
                rows.append(
                    ["Table truncated because too big: more than %s rows" % i])
                break
            rows.append(row)
        self.rows = rows
        self.header = tuple(header)  # horizontal header

    def render(self, dummy_ctxt=None):
        out = "\n%s\n" % "".join(list(self._gen_table()))
        if not self.rows:
            out += '<em>%s</em>' % html.escape(self.empty_table, quote=True)
        return out

    def _gen_table(self):
        yield '<table id="%s" border="%s" summary="%s" class="tablesorter">\n'\
              % (self.name, self.border, self.summary)
        yield '<thead>\n'
        yield '<tr>%s</tr>\n' % ''.join(
            '<th>%s</th>\n' % h for h in self.header)
        yield '</thead>\n'
        yield '<tbody\n>'
        for r, row in enumerate(self.rows):
            yield '<tr class="%s">\n' % ["even", "odd"][r % 2]
            for col in row:
                yield '<td>%s</td>\n' % col
            yield '</tr>\n'
        yield '</tbody>\n'
        yield '</table>\n'


def fix_newlines(row):
    return tuple(col.replace('\n', '\\n') for col in row)


def text_table(data, header=None, fmt=None, ext='rst'):
    """
    Build a .rst (or .org) table from a matrix or a DataFrame

    >>> tbl = [['a', 1], ['b', 2]]
    >>> print(text_table(tbl, header=['Name', 'Value']))
    +------+-------+
    | Name | Value |
    +------+-------+
    | a    | 1     |
    +------+-------+
    | b    | 2     |
    +------+-------+
    """
    assert ext in 'csv rst org md', ext
    if isinstance(data, pandas.DataFrame):
        if data.index.name:
            data = data.reset_index()
        header = header or list(data.columns)
        data = zip(*[data[col].to_numpy() for col in data.columns])
    if header is None and hasattr(data, '_fields'):
        header = data._fields
    try:
        # see if data is a composite numpy array
        data.dtype.fields
    except AttributeError:
        # not a composite array
        header = header or ()
    else:
        if not header:
            header = [col.split(':')[0] for col in build_header(data.dtype)]
    if header:
        col_sizes = [len(col) for col in header]
    else:
        col_sizes = [len(str(col)) for col in data[0]]
    body = []
    fmt = functools.partial(scientificformat, fmt=fmt) if fmt else form
    for row in data:
        tup = tuple(fmt(c) for c in row)
        if ext in 'rst org md':
            tup = fix_newlines(tup)
        for (i, col) in enumerate(tup):
            col_sizes[i] = max(col_sizes[i], len(col))
        if len(tup) != len(col_sizes):
            raise ValueError('The header has %d fields but the row %d fields!'
                             % (len(col_sizes), len(tup)))
        body.append(tup)
    if ext == 'html':
        return HtmlTable([header] + body).render()

    if ext == 'md':
        wrap = '|-%s-|'
        sepline = wrap % '-|-'.join('-' * size for size in col_sizes)
    else:
        wrap = '+-%s-+' if ext == 'rst' else '|-%s-|'
        sepline = wrap % '-+-'.join('-' * size for size in col_sizes)

    sep = ',' if ext == 'csv' else ' | '
    templ = sep.join('%-{}s'.format(size) for size in col_sizes)
    if ext != 'csv':
        templ = '| %s |' % templ
    if header and ext == 'rst':
        lines = [sepline, templ % tuple(header), sepline]
    elif header and ext == 'org':
        lines = [templ % tuple(header), sepline]
    elif header and ext == 'md':
        lines = [templ % tuple(header), sepline]
    elif header and ext == 'csv':
        lines = [','.join(header)]
    else:
        lines = [sepline]
    for tup in body:
        lines.append(templ % tup)
        if ext == 'rst':
            lines.append(sepline)
    return '\n'.join(lines)


if __name__ == '__main__':  # pretty print of NRML files
    import sys
    import shutil
    # keep local: baselib must not depend on hazardlib
    from openquake.hazardlib import nrml
    nrmlfiles = sys.argv[1:]
    for fname in nrmlfiles:
        node = nrml.read(fname)
        shutil.copy(fname, fname + '.bak')
        with open(fname, 'w', encoding='utf8') as out:
            nrml.write(list(node), out)
