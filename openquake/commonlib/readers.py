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


def parse_header(header):
    """
    Convert a list of the form `['fieldname:fieldtype:fieldsize',...]`
    into a numpy composite dtype. Here is an example:

    >>> parse_header(['PGA:float64:3', 'PGV:float64:2', 'avg:float:1'])
    dtype([('PGA', '<f8', (3,)), ('PGV', '<f8', (2,)), ('avg', '<f8', (1,))])

    :params header: a list of type descriptions
    :returns: the corresponding composite dtype
    """
    triples = []
    for col_str in header:
        col = col_str.split(':')
        field = col[0]
        numpytype = getattr(numpy, col[1])
        shape = tuple(map(int, col[2:]))
        triples.append((field, numpytype, shape))
    return numpy.dtype(triples)


def get_subtypes(dtype):
    """
    :param: a composite numpy dtype
    :returns: the subtypes contained in the dtype
    """
    sd = []
    for f in dtype.fields:
        dt = dtype.fields[f][0]
        sd.append(dt.subdtype[0].type)
    return sd


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
        dtype = parse_header(header.split(sep))
        subtypes = get_subtypes(dtype)
        records = []
        for line in f:
            row = line.split(sep)
            record = tuple(map(subtype, col.split())
                           for subtype, col in zip(subtypes, row))
            records.append(record)
        return numpy.array(records, dtype)


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
