# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

import os
import json
import logging
import numpy

from openquake.baselib import hdf5
from openquake.commonlib import datastore, logs
from openquake.calculators.views import view, text_table
from openquake.calculators.extract import extract


def str_or_int(calc_id):
    try:
        return int(calc_id)
    except ValueError:
        return calc_id


def print_(aw):
    if hasattr(aw, 'json'):
        try:
            attrs = hdf5.get_shape_descr(aw.json)
        except KeyError:  # no shape_descr, for instance for oqparam
            print(json.dumps(json.loads(aw.json), indent=2))
            return
        vars(aw).update(attrs)
    if hasattr(aw, 'shape_descr'):
        print(text_table(aw.to_dframe(), ext='org'))
    elif hasattr(aw, 'array'):
        if aw.array.dtype.name == 'object':  # array of objects
            for el in aw.array:
                print(el.decode('utf-8') if isinstance(el, bytes) else el)
        elif aw.array.dtype.names:  # structured array
            print(text_table(aw.array, ext='org'))
        else:  # regular array
            print(aw.array)
    elif isinstance(aw, numpy.ndarray):
        print(text_table(aw, ext='org'))
    else:
        print(aw)


def main(what='contents', calc_id: str_or_int = -1, extra=()):
    """
    Show the content of a datastore (by default the last one).
    """
    datadir = datastore.get_datadir()
    if what == 'all':  # show all
        if not os.path.exists(datadir):
            return
        rows = []
        for calc_id in logs.get_calc_ids(datadir):
            try:
                ds = datastore.read(calc_id)
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

    ds = datastore.read(calc_id)

    # this part is experimental
    if view.keyfunc(what) in view:
        print_(view(what, ds))
    elif what.split('/', 1)[0] in extract:
        print_(extract(ds, what, *extra))
    elif what in ds:
        obj = ds.getitem(what)
        if '__pdcolumns__' in obj.attrs:
            df = ds.read_df(what)
            print(df)
        elif hasattr(obj, 'items'):  # is a group of datasets
            print(obj)
        else:  # is a single dataset
            obj.refresh()  # for SWMR mode
            print_(hdf5.ArrayWrapper.from_(obj))
    else:
        print('%s not found' % what)

    ds.close()


main.what = 'key or view of the datastore'
main.calc_id = 'calculation ID or datastore path'
main.extra = dict(help='extra arguments', nargs='*')
