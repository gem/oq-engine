# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import zipfile
import logging
from openquake.baselib.general import CallableDict
from openquake.baselib.writers import write_csv


class MissingExporter(Exception):
    """
    Raised when there is not exporter for the given pair (dskey, fmt)
    """


def export_csv(ekey, dstore):
    """
    Default csv exporter for arrays stored in the output.hdf5 file

    :param ekey: export key
    :param dstore: datastore object
    :returns: a list with the path of the exported file
    """
    name = ekey[0] + '.csv'
    try:
        array = dstore[ekey[0]][()]
    except AttributeError:
        # this happens if the key correspond to a HDF5 group
        return []  # write a custom exporter in this case
    if len(array.shape) == 1:  # vector
        array = array.reshape((len(array), 1))
    return [write_csv(dstore.export_path(name), array)]


def keyfunc(ekey):
    """
    Extract the name before the slash:

    >>> keyfunc(('risk_by_event', 'csv'))
    ('risk_by_event', 'csv')
    >>> keyfunc(('risk_by_event/1', 'csv'))
    ('risk_by_event', 'csv')
    >>> keyfunc(('risk_by_event/1/0', 'csv'))
    ('risk_by_event', 'csv')
    """
    fullname, ext = ekey
    return (fullname.split('/', 1)[0], ext)


export = CallableDict(keyfunc)
export.sanity_check = False  # overridden in the tests
export.from_db = False  # overridden when exporting from db


@export.add(('input', 'zip'))
def export_input_zip(ekey, dstore):
    """
    Export the data in the `input` datagroup as a .zip file
    """
    dest = dstore.export_path('input.zip')
    with zipfile.ZipFile(
            dest, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for k, data in dstore.retrieve_files():
            logging.info('Archiving %s' % k)
            z.writestr(k, data)
    return [dest]
