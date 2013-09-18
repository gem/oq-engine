#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

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

import os
import csv
import zipfile
from openquake.nrmllib.node import (
    node_from_nrml, node_to_nrml, node_to_xml)
from openquake.nrmllib.tables import ZipTable, collect_tables
from openquake.nrmllib.converter import converter


def build_node(tables, output=None):
    """
    Build a NRML node from a consistent set of table objects (i.e. all
    tables must have the same metadata tag). If output is a file-like
    object open for writing it also saves the node in NRML format.

    :param tables: list of :class:`openquake.nrmllib.tables.Table` instances
    :param output: a file-like object open for writing or None
    """
    assert len(tables) > 0
    tags = set(r.metadata.tag for r in tables)
    if len(tags) > 1:
        raise ValueError(
            'All tables must have the same tag, found %s instead' % tags)
    node = converter(tables[0].metadata).build_node(tables)
    if output is not None:
        node_to_nrml(node, output)
    return node


################################# generic #####################################

def convert_nrml_to_flat(fname, outfname):
    """
    Convert a NRML file into .csv and .mdata files. Returns the path names
    of the generated files.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path, for instance <path>.csv
    """
    # extract the first node inside the <nrml> tag
    node = node_from_nrml(fname)[0]
    tables = list(converter(node).build_tables())
    suffixes = set(t.suffix for t in tables)
    if len(suffixes) < len(tables):
        raise ValueError('Duplicates in %s' % suffixes)
    tozip = []
    for table in tables:
        tozip.extend(table.save(outfname[:-4]))
    return tozip


def convert_nrml_to_zip(fname, outfname=None):
    """
    Convert a NRML file into a zip archive.

    :param fname: path to a NRML file of kind <path>.xml
    :param outfname: output path; if None, <path>.zip is used instead
    """
    outname = outfname or fname[:-4] + '.zip'
    assert outname.endswith('.zip'), outname
    tozip = convert_nrml_to_flat(fname, outname)
    with zipfile.ZipFile(fname[:-4] + '.zip', 'w') as z:
        for fname in tozip:
            z.write(fname, os.path.basename(fname))
            os.remove(fname)
    return outname


def convert_zip_to_nrml(fname, outdir=None):
    """
    Convert a zip archive into one or more NRML files.

    :param fname: path to a zip archive
    :param outdir: output directory; if None the input directory is used
    """
    outdir = outdir or os.path.dirname(fname)
    z = zipfile.ZipFile(fname)
    outputs = []
    for name, tables in collect_tables(ZipTable, z):
        outname = os.path.join(outdir, name + '.xml')
        with open(outname, 'wb+') as out:
            build_node(tables, out)
        outputs.append(outname)
    return outputs
