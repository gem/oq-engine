# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
import io
import os
import json
import logging

from openquake.baselib import sap
from openquake.baselib import datastore, hdf5
from openquake.commonlib.writers import write_csv
from openquake.commonlib import util
from openquake.calculators.views import view, rst_table
from openquake.calculators.extract import extract


def str_or_int(calc_id):
    try:
        return int(calc_id)
    except ValueError:
        return calc_id


def print_(aw):
    if hasattr(aw, 'json'):
        print(json.dumps(json.loads(aw.json), indent=2))
    elif hasattr(aw, 'shape_descr'):
        print(rst_table(aw.to_table()))
    if hasattr(aw, 'array') and aw.dtype.names:
        print(write_csv(io.StringIO(), aw.array))


@sap.script
def show(what='contents', calc_id=-1, extra=()):
    """
    Show the content of a datastore (by default the last one).
    """
    datadir = datastore.get_datadir()
    if what == 'all':  # show all
        if not os.path.exists(datadir):
            return
        rows = []
        for calc_id in datastore.get_calc_ids(datadir):
            try:
                ds = util.read(calc_id)
                oq = ds['oqparam']
                cmode, descr = oq.calculation_mode, oq.description
            except Exception:
                # invalid datastore file, or missing calculation_mode
                # and description attributes, perhaps due to a manual kill
                f = os.path.join(datadir, 'calc_%s.hdf5' % calc_id)
                logging.warning('Unreadable datastore %s', f)
                continue
            else:
                rows.append((calc_id, cmode, descr.encode('utf-8')))
        for row in sorted(rows, key=lambda row: row[0]):  # by calc_id
            print('#%d %s: %s' % row)
        return

    ds = util.read(calc_id)

    # this part is experimental
    if view.keyfunc(what) in view:
        print(view(what, ds))
    elif what.split('/', 1)[0] in extract:
        obj = extract(ds, what, *extra)
        if isinstance(obj, hdf5.ArrayWrapper):
            print_(obj)
        elif hasattr(obj, 'dtype') and obj.dtype.names:
            print(write_csv(io.StringIO(), obj))
        else:
            print(obj)
    elif what in ds:
        obj = ds.getitem(what)
        if hasattr(obj, 'items'):  # is a group of datasets
            print(obj)
        else:  # is a single dataset
            obj.refresh()  # for SWMR mode
            print_(hdf5.ArrayWrapper.from_(obj))
    else:
        print('%s not found' % what)

    ds.close()


show.arg('what', 'key or view of the datastore')
show.arg('calc_id', 'calculation ID or datastore path', type=str_or_int)
show.arg('extra', 'extra arguments', nargs='*')
