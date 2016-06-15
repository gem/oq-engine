# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

from openquake.baselib.general import import_all, CallableDict
from openquake.commonlib.writers import write_csv


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
        array = dstore[ekey[0]].value
    except AttributeError:
        # this happens if the key correspond to a HDF5 group
        return []  # write a custom exporter in this case
    if len(array.shape) == 1:  # vector
        array = array.reshape((len(array), 1))
    return [write_csv(dstore.export_path(name), array)]


def dispatch_on_colon(ekey, dstore):
    """
    If the datastore key contains a colon, i.e. it is of the form
    dskey:spec, then call `export(('<dskey>:', fmt), dstore, spec)`.

    :param ekey:
        export key of the form (k0, ext) with k0 of the form <dskey>:<spec>
    :param dstore:
        datastore instance

    This function is called only for ekey not present in the datastore.
    """
    if ':' not in ekey[0]:
        raise MissingExporter(ekey)
    dkey, spec = ekey[0].split(':', 1)
    return export((dkey + ':', ekey[1]), dstore, spec)


export = CallableDict(keymissing=dispatch_on_colon)
export.from_db = False  # overridden when exporting from db

import_all('openquake.commonlib.export')
