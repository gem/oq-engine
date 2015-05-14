#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

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

import numpy
from openquake.commonlib import InvalidFile


def parse_header(header):
    """
    Convert a list of the form `['fieldname:fieldtype:fieldsize',...]`
    into a numpy composite dtype. Here is an example:

    >>> parse_header(['PGA:float64:3', 'PGV:float64:2', 'avg:float:1'])
    (['PGA', 'PGV', 'avg'], dtype([('PGA', '<f8', (3,)), ('PGV', '<f8', (2,)), ('avg', '<f8', (1,))]))

    :params header: a list of type descriptions
    :returns: column names and the corresponding composite dtype
    """
    triples = []
    fields = []
    for col_str in header:
        col = col_str.split(':')
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
    >>> fname = writetmp('PGA:float64:3,PGV:float64:2,avg:float64:1\n'
    ...                  '.1 .2 .3,.4 .5,.6\n')
    >>> print read_composite_array(fname)  # array of shape (1,)
    [([0.1, 0.2, 0.3], [0.4, 0.5], [0.6])]
    """
    with open(fname) as f:
        header = next(f)
        fields, dtype = parse_header(header.split(sep))
        ts_pairs = []  # [(type, shape), ...]
        for name in fields:
            dt = dtype.fields[name][0]
            ts_pairs.append((dt.subdtype[0].type if dt.subdtype else dt.type,
                             dt.shape))
        col_ids = range(1, len(ts_pairs) + 1)
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
    >>> print read_array(writetmp('.1 .2, .3 .4, .5 .6\n'))
    [[[ 0.1  0.2]
      [ 0.3  0.4]
      [ 0.5  0.6]]]
    """
    with open(fname) as f:
        records = []
        for line in f:
            row = line.split(sep)
            record = [map(float, col.split()) for col in row]
            records.append(record)
        return numpy.array(records)
