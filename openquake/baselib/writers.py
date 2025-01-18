# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
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
import tempfile
import numpy  # this is needed by the doctests, don't remove it
import pandas
from openquake.baselib.node import scientificformat

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
        comment = ', '.join('%s=%r' % item for item in comment.items())
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


if __name__ == '__main__':  # pretty print of NRML files
    import sys
    import shutil
    from openquake.hazardlib import nrml
    nrmlfiles = sys.argv[1:]
    for fname in nrmlfiles:
        node = nrml.read(fname)
        shutil.copy(fname, fname + '.bak')
        with open(fname, 'w') as out:
            nrml.write(list(node), out)
