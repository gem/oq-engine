# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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

from __future__ import print_function
import inspect
import logging

from openquake.baselib import performance, sap, hdf5, datastore

from openquake.commonlib.logs import dbcmd
from openquake.calculators.extract import extract as extract_
from openquake.server import dbserver


# `oq extract` is tested in the demos
@sap.Script
def extract(calc_id, what, extra):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    """
    logging.basicConfig(level=logging.INFO)
    if dbserver.get_status() == 'running':
        job = dbcmd('get_job', calc_id)
        if job is not None:
            calc_id = job.ds_calc_dir + '.hdf5'
    dstore = datastore.read(calc_id)
    parent_id = dstore['oqparam'].hazard_calculation_id
    if parent_id:
        dstore.parent = datastore.read(parent_id)
    with performance.Monitor('extract', measuremem=True) as mon, dstore:
        items = extract_(dstore, what, *extra)
        if not inspect.isgenerator(items):
            items = [(items.__class__.__name__, items)]
        fname = '%s_%d.hdf5' % (what.replace('/', '-'), dstore.calc_id)
        hdf5.save(fname, items)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)


extract.arg('calc_id', 'number of the calculation', type=int)
extract.arg('what', 'string specifying what to export')
extract.arg('extra', 'extra arguments', nargs='*')
