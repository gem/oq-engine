#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

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
from openquake.baselib.general import import_all, CallableDict
from openquake.commonlib.writers import write_csv


def export_csv(ekey, dstore):
    """
    Default csv exporter for arrays stored in the output.hdf5 file

    :param ekey: export key
    :param dstore: datastore object
    :returns: a list with the path of the exported file
    """
    name = ekey[0][1:] + '.csv'
    try:
        array = dstore[ekey[0]].value
    except AttributeError:
        # this happens if the key correspond to a HDF5 group
        return []  # write a custom exporter in this case
    if len(array.shape) == 1:  # vector
        array = array.reshape((len(array), 1))
    dest = os.path.join(dstore.export_dir, name)
    return [write_csv(dest, array)]


def get_export_csv(ekey):
    """
    If the key corresponds to a HDF5 path and the format is csv,
    return the default csv exporter, otherwise raise a KeyError.
    """
    key, fmt = ekey
    if key.startswith('/') and fmt == 'csv':
        return export_csv
    raise KeyError(ekey)

export = CallableDict(keymissing=get_export_csv)

import_all('openquake.commonlib.export')
