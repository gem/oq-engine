# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
import inspect
import logging
from urllib.parse import quote_plus
from urllib.request import urlopen

import numpy
from openquake.baselib import performance, sap, hdf5, datastore
from openquake.commonlib.logs import dbcmd
from openquake.calculators.extract import extract as extract_
from openquake.server import dbserver


def quote(url_like):
    try:
        path, query = url_like.split('?', 1)
    except ValueError:  # no question mark
        return url_like
    namevals = []
    for nv in query.split('&'):
        n, v = nv.split('=')
        namevals.append('%s=%s' % (n, quote_plus(v)))
    return path + '?' + '&'.join(namevals)


# `oq extract` is tested in the demos
@sap.Script
def extract(what, calc_id=-1, server_url=None):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    """
    logging.basicConfig(level=logging.INFO)
    if calc_id < 0:
        calc_id = datastore.get_calc_ids()[calc_id]
    hdf5path = None
    if dbserver.get_status() == 'running':
        job = dbcmd('get_job', calc_id)
        if job is not None:
            hdf5path = job.ds_calc_dir + '.hdf5'
    dstore = datastore.read(hdf5path or calc_id)
    parent_id = dstore['oqparam'].hazard_calculation_id
    if parent_id:
        dstore.parent = datastore.read(parent_id)
    urlpath = '/v1/calc/%d/extract/%s' % (calc_id, quote(what))
    with performance.Monitor('extract', measuremem=True) as mon, dstore:
        if server_url:
            print('Calling %s%s' % (server_url, urlpath))
            data = urlopen(server_url.rstrip('/') + urlpath).read()
            items = (item for item in numpy.load(io.BytesIO(data)).items())
        else:
            print('Emulating call to %s' % urlpath)
            items = extract_(dstore, what)
        if not inspect.isgenerator(items):
            items = [(items.__class__.__name__, items)]
        fname = '%s_%d.hdf5' % (what.replace('/', '-').replace('?', '-'),
                                dstore.calc_id)
        hdf5.save(fname, items)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)


extract.arg('what', 'string specifying what to export')
extract.arg('calc_id', 'number of the calculation', type=int)
extract.opt('server_url', 'URL of the webui', '-u')
