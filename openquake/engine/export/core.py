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

"""Functions for getting information about completed jobs and
calculation outputs, as well as exporting outputs from the database to various
file formats."""


import os
import sys
import traceback

from openquake.calculators.export import export
from openquake.commonlib import logs, datastore, __version__


class DataStoreExportError(Exception):
    pass


def check_version(dstore):
    """
    :param dstore: a DataStore instance
    :returns:
        a message if the stored version is different from the current version
    """
    ds_version = dstore.hdf5.attrs['engine_version']
    if ds_version != __version__:
        return (': the datastore is at version %s, but the exporter at '
                'version %s' % (ds_version, __version__))
    else:
        return ''


def export_from_db(output_key, calc_id, datadir, target):
    """
    :param output_key: a pair (ds_key, fmt)
    :param calc_id: calculation ID
    :param datadir: directory containing the datastore
    :param target: directory, temporary when called from the engine server
    :returns: the list of exported path names
    """
    makedirs(target)
    export.from_db = True
    with datastore.read(calc_id, datadir=datadir) as dstore:
        dstore.export_dir = target
        try:
            exported = export(output_key, dstore)
        except Exception:
            _etype, err, tb = sys.exc_info()
            tb_str = ''.join(traceback.format_tb(tb))
            version = check_version(dstore)
            raise DataStoreExportError(
                'Could not export %s in %s%s\n%s%s' %
                (output_key + (version, tb_str, err)))
        return exported


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


def export_outputs(job_id, target_dir, export_types):
    # make it possible commands like `oq engine --eos -1 /tmp`
    datadir, dskeys = logs.dbcmd('get_results', job_id)
    if not dskeys:
        yield 'Found nothing to export for job %s' % job_id
    for dskey in dskeys:
        yield 'Exporting %s...' % dskey
        for line in export_output(
                dskey, job_id, datadir, target_dir, export_types):
            yield line


def get_outkey(dskey, export_types):
    """
    Extract the first pair (dskey, exptype) found in export
    """
    for exptype in export_types:
        if (dskey, exptype) in export:
            return (dskey, exptype)


def export_output(dskey, calc_id, datadir, target_dir, export_types):
    """
    Simple UI wrapper around
    :func:`openquake.engine.export.core.export_from_db` yielding
    a summary of files exported, if any.
    """
    outkey = get_outkey(dskey, export_types.split(','))
    if export_types and not outkey:
        yield 'There is no exporter for %s, %s' % (dskey, export_types)
        return
    yield from export_from_db(outkey, calc_id, datadir, target_dir)
