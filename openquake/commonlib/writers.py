# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
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

import re
import logging
import numpy  # this is needed by the doctests, don't remove it
from openquake.hazardlib import InvalidFile
from openquake.baselib.node import scientificformat

FIVEDIGITS = '%.5E'


class HeaderTranslator(object):
    r"""
    An utility to convert the headers in CSV files. When reading,
    the column names are converted into column descriptions with the
    method .read, when writing column descriptions are converted
    into column names with the method .write. The usage is

    >>> htranslator = HeaderTranslator(
    ...     '(asset_ref):\|S100',
    ...     '(eid):uint32',
    ...     '(taxonomy):object')
    >>> htranslator.write('asset_ref:|S100 value:5'.split())
    ['asset_ref', 'value:5']
    >>> htranslator.read('asset_ref value:5'.split())
    ['asset_ref:|S100', 'value:5']
    """
    def __init__(self, *regexps):
        self.suffix = []
        short_regexps = []
        for regex in regexps:
            prefix, suffix = regex.split(')')
            short_regexps.append(prefix + ')$')
            self.suffix.append(suffix)
        self.short_regex = '|'.join(short_regexps)
        self.long_regex = '|'.join(regexps)

    def read(self, names):
        """
        Convert names into descriptions
        """
        descrs = []
        for name in names:
            mo = re.match(self.short_regex, name)
            if mo:
                idx = mo.lastindex  # matching group index, starting from 1
                suffix = self.suffix[idx - 1].replace(r':\|', ':|')
                descrs.append(mo.group(mo.lastindex) + suffix +
                              name[mo.end():])
            else:
                descrs.append(name)
        return descrs

    def write(self, descrs):
        """
        Convert descriptions into names
        """
        # example: '(poe-[\d\.]+):float32' -> 'poe-[\d\.]+'
        names = []
        for descr in descrs:
            mo = re.match(self.long_regex, descr)
            if mo:
                names.append(mo.group(mo.lastindex) + descr[mo.end():])
            else:
                names.append(descr)
        return names

htranslator = HeaderTranslator(
    '(rlzi):uint16',
    '(sid):uint32',
    '(eid):uint64',
    '(imti):uint8',
    '(gmv):float32',
    '(aid):uint32',
    '(boundary):object',
    '(tectonic_region_type):object',
    '(asset_ref):\|S100',
    '(rup_id):uint32',
    '(event_id):uint64',
    '(event_set):uint32',
    '(eid):uint32',
    '(year):uint32',
    '(taxonomy):\|S100',
    '(multiplicity):uint16',
    '(magnitude):float32',
    '(centroid_lon):float32',
    '(centroid_lat):float32',
    '(centroid_depth):float32',
    '(numsites):uint32',
    '(losses):float32',
    '(poes):float32',
    '(avg):float32',
    '(poe-[\d\.]+):float32',
    '(lon):float32',
    '(lat):float32',
    '(depth):float32',
    '(structural.*):float32',
    '(nonstructural.*):float32',
    '(business_interruption.*):float32',
    '(contents.*):float32',
    '(occupants):float32',
    '(occupants~.+):float32',
    '(occupants_ins):float32',
    '(no_damage):float32',
    '(slight):float32',
    '(moderate):float32',
    '(extensive):float32',
    '(complete):float32',
    '(\d+):float32',  # realization column, used in the GMF scenario exporter
)


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


# NB: builds an header that can be read by parse_header
def build_header(dtype):
    """
    Convert a numpy nested dtype into a list of strings suitable as header
    of csv file.

    >>> imt_dt = numpy.dtype([('PGA', float, 3), ('PGV', float, 4)])
    >>> build_header(imt_dt)
    ['PGA:3', 'PGV:4']
    >>> gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
    ...                       ('idx', numpy.uint32)])
    >>> build_header(gmf_dt)
    ['A~PGA:3', 'A~PGV:4', 'B~PGA:3', 'B~PGV:4', 'idx:uint32']
    """
    header = _build_header(dtype, ())
    h = []
    for col in header:
        name = '~'.join(col[:-2])
        numpytype = col[-2]
        shape = col[-1]
        coldescr = name
        if numpytype != 'float64':
            coldescr += ':' + numpytype
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


def write_csv(dest, data, sep=',', fmt='%.6E', header=None, comment=None):
    """
    :param dest: file, filename or io.StringIO instance
    :param data: array to save
    :param sep: separator to use (default comma)
    :param fmt: formatting string (default '%12.8E')
    :param header:
       optional list with the names of the columns to display
    :param comment:
       optional first line starting with a # character
    """
    close = True
    if len(data) == 0:
        logging.warn('%s is empty', dest)
    if hasattr(dest, 'write'):
        # file-like object in append mode
        # it must be closed by client code
        close = False
    elif not hasattr(dest, 'getvalue'):
        # not a StringIO, assume dest is a filename
        dest = open(dest, 'w')
    try:
        # see if data is a composite numpy array
        data.dtype.fields
    except AttributeError:
        # not a composite array
        autoheader = []
    else:
        autoheader = build_header(data.dtype)

    if comment:
        dest.write('# %s\n' % comment)

    someheader = header or autoheader
    if header != 'no-header' and someheader:
        dest.write(sep.join(htranslator.write(someheader)) + u'\n')

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
                    row.append(scientificformat(val, fmt))
            dest.write(sep.join(row) + u'\n')
    else:
        for row in data:
            dest.write(sep.join(scientificformat(col, fmt)
                                for col in row) + u'\n')
    if hasattr(dest, 'getvalue'):
        return dest.getvalue()[:-1]  # a newline is strangely added
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

    def save(self, data, fname, header=None):
        """
        Save data on fname.

        :param data: numpy array or list of lists
        :param fname: path name
        :param header: header to use
        """
        write_csv(fname, data, self.sep, self.fmt, header)
        self.fnames.add(getattr(fname, 'name', fname))

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
    by :func:`openquake.commonlib.writers.build_header`.
    Here is an example:

    >>> parse_header(['PGA:float32', 'PGV', 'avg:float32:2'])
    (['PGA', 'PGV', 'avg'], dtype([('PGA', '<f4'), ('PGV', '<f8'), ('avg', '<f4', (2,))]))

    :params header: a list of type descriptions
    :returns: column names and the corresponding composite dtype
    """
    triples = []
    fields = []
    for col_str in header:
        col = col_str.strip().split(':')
        n = len(col)
        if n == 1:  # default dtype and no shape
            col = [col[0], 'float64', '']
        elif n == 2:
            if castable_to_int(col[1]):  # default dtype and shape
                col = [col[0], 'float64', col[1]]
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


def _cast(col, ntype, shape, lineno, fname):
    # convert strings into tuples or numbers, used inside read_composite_array
    if shape:
        return tuple(map(ntype, col.split()))
    else:
        return ntype(col)


# NB: this only works with flat composite arrays
def read_composite_array(fname, sep=','):
    r"""
    Convert a CSV file with header into a numpy array of records.

    >>> from openquake.baselib.general import writetmp
    >>> fname = writetmp('PGA:3,PGV:2,avg:1\n'
    ...                  '.1 .2 .3,.4 .5,.6\n')
    >>> print(read_composite_array(fname))  # array of shape (1,)
    [([0.1, 0.2, 0.3], [0.4, 0.5], [0.6])]
    """
    with open(fname) as f:
        header = next(f)
        transheader = htranslator.read(header.split(sep))
        fields, dtype = parse_header(transheader)
        ts_pairs = []  # [(type, shape), ...]
        for name in fields:
            dt = dtype.fields[name][0]
            ts_pairs.append((dt.subdtype[0].type if dt.subdtype else dt.type,
                             dt.shape))
        col_ids = list(range(1, len(ts_pairs) + 1))
        num_columns = len(col_ids)
        records = []
        col, col_id = '', 0
        for i, line in enumerate(f, 2):
            row = line.split(sep)
            if len(row) != num_columns:
                raise InvalidFile(
                    'expected %d columns, found %d in file %s, line %d' %
                    (num_columns, len(row), fname, i))
            try:
                record = []
                for (ntype, shape), col, col_id in zip(ts_pairs, row, col_ids):
                    record.append(_cast(col, ntype, shape, i, fname))
                records.append(tuple(record))
            except Exception as e:
                raise InvalidFile(
                    'Could not cast %r in file %s, line %d, column %d '
                    'using %s: %s' % (col, fname, i, col_id,
                                      (ntype.__name__,) + shape, e))
        return numpy.array(records, dtype)


# this is simple and without error checking for the moment
def read_array(fname, sep=','):
    r"""
    Convert a CSV file without header into a numpy array of floats.

    >>> from openquake.baselib.general import writetmp
    >>> print(read_array(writetmp('.1 .2, .3 .4, .5 .6\n')))
    [[[ 0.1  0.2]
      [ 0.3  0.4]
      [ 0.5  0.6]]]
    """
    with open(fname) as f:
        records = []
        for line in f:
            row = line.split(sep)
            record = [list(map(float, col.split())) for col in row]
            records.append(record)
        return numpy.array(records)


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
