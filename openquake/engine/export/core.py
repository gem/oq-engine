# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

"""Functions for getting information about completed jobs and
calculation outputs, as well as exporting outputs from the database to various
file formats."""


import os
import ast
import zipfile

from openquake.commonlib.export import export as ds_export
from openquake.commonlib import datastore
from openquake.engine import logs


class DataStoreExportError(Exception):
    pass


def zipfiles(fnames, archive):
    """
    Build a zip archive from the given file names.

    :param fnames: list of path names
    :param archive: path of the archive
    """
    z = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    for f in fnames:
        z.write(f, os.path.basename(f))
    z.close()


def export_from_datastore(output_key, calc_id, datadir, target):
    """
    :param output_key: a pair (ds_key, fmt)
    :param calc_id: calculation ID
    :param datadir: directory containing the datastore
    :param target: directory, temporary when called from the engine server
    """
    ds_key, fmt = output_key
    dstore = datastore.read(calc_id, datadir=datadir)
    parent_id = ast.literal_eval(dstore.attrs['hazard_calculation_id'])
    if parent_id:
        dstore.set_parent(datastore.read(parent_id, datadir=datadir))
    dstore.export_dir = target
    try:
        exported = ds_export(output_key, dstore)
    except KeyError:
        raise DataStoreExportError(
            'Could not export %s in %s' % output_key)
    if not exported:
        raise DataStoreExportError(
            'Nothing to export for %s' % ds_key)
    elif len(exported) > 1:
        # NB: I am hiding the archive by starting its name with a '.',
        # to avoid confusing the users, since the unzip files are
        # already in the target directory; the archive is used internally
        # by the WebUI, so it must be there; it would be nice not to
        # generate it when not using the Web UI, but I will leave that
        # feature for after the removal of the old calculators
        archname = '.' + ds_key + '-' + fmt + '.zip'
        zipfiles(exported, os.path.join(target, archname))
        return os.path.join(target, archname)
    else:  # single file
        return exported[0]


def export(output_id, target, export_type='xml,geojson,csv'):
    """
    Export the given calculation `output_id` from the database to the
    specified `target` directory in the specified `export_type`.
    """
    dskey, calc_id, datadir = logs.dbcmd('get_output', output_id)
    if isinstance(target, basestring):  # create target directory
        makedirs(target)
    for exptype in export_type.split(','):
        outkey = (dskey, exptype)
        export_from_datastore(outkey, calc_id, datadir, target)

#: Used to separate node labels in a logic tree path
LT_PATH_JOIN_TOKEN = '_'


def makedirs(path):
    """
    Make all of the directories in the ``path`` using `os.makedirs`.
    """
    if os.path.exists(path):
        if not os.path.isdir(path):
            # If it's not a directory, we can't do anything.
            # This is a problem
            raise RuntimeError('%s already exists and is not a directory.'
                               % path)
    else:
        os.makedirs(path)
