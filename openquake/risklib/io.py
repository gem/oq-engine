#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

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

"""
Routines for the I/O of the risklib calculators
"""

import os
import ast
import csv
import gzip
import zipfile
import ConfigParser
import collections

from openquake.risklib.models.input import FragilityModel
from openquake.risklib.utils import Register
from openquake.risklib.grid import Grid


read = Register()  # dictionary {filetype: function}


def may_be_gz(name, fileobj):
    """
    If fileobj is a regular file returns it unchanged, if it refers to a
    gzipped file returns a :class:`gzip.GzipFile` object. The selection
    is made according to the extension in `name`.
    """
    if name.endswith('.gz'):
        return gzip.GzipFile(name, fileobj=fileobj)
    else:
        return fileobj


class Archive(object):
    """
    Can be a directory or a zipfile, can contain .gz files
    """
    def __init__(self, path):
        self.path = path
        self.zfile = None
        if not os.path.isdir(path):
            assert zipfile.is_zipfile(path), '%r is not a zipfile' % path
            self.zfile = zipfile.ZipFile(path)

    def open(self, name, mode='r'):
        assert name, 'Expected a file name, got %r' % name
        if self.zfile:
            return may_be_gz(name, self.zfile.open(name, mode))
        else:
            return may_be_gz(name, open(os.path.join(self.path, name), mode))


def leval(row):
    for x in row:
        try:
            yield ast.literal_eval(x)
        except ValueError:
            yield x

Asset = collections.namedtuple(
    'Asset', 'site asset_id number_of_units taxonomy')


@read.add('fragility')
def read_fragility(rows):
    return map(leval, rows)
    irows = iter(rows)
    fmt, iml, limit_states = leval(irows.next())
    return FragilityModel(fmt, iml['IMT'], iml['imls'], limit_states,
                          *map(leval, irows))


@read.add('exposure')
def read_exposure(rows):
    """
    Returns a list of assets ordered by taxonomy
    """
    assetlist = []
    by_taxonomy = sorted(rows, key=lambda row: row[-1])
    for lon, lat, asset_id, number_of_units, taxonomy in by_taxonomy:
        assetlist.append(Asset((float(lon), float(lat)), asset_id,
                               float(number_of_units), taxonomy))
    return assetlist


@read.add('gmf')
def read_gmf(rows):
    matrix = [map(float, row) for row in rows]
    return Grid.read_from(matrix)


def write_dmg_dist(rows):
    pass


def read_calculator_input(path, config='job.ini', delimiter='\t'):
    """
    Read a .ini configuration file from a directory or a zip archive
    and then extract the inner files. Keep everything in memory.
    """
    archive = Archive(path)
    conf = archive.open(config)
    try:
        cfp = ConfigParser.RawConfigParser()
        cfp.readfp(conf)
    finally:
        conf.close()
    inputdic = {}
    for parname, parvalue in cfp.items('general'):
        inputdic[parname] = parvalue
        if parname.endswith('_file'):
            filetype = parname[:-5]  # strip _file suffix
            with archive.open(parvalue) as fileobj:
                reader = csv.reader(fileobj, delimiter=delimiter)
                inputdic[filetype] = read[filetype](reader)
    return inputdic
