# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Helpers for testing the calculators, used in oq-risk-tests
"""
import os
import re
import time
import pathlib
import numpy
import pandas
from openquake.baselib import hdf5
from openquake.commonlib import logs, readinput
from openquake.calculators import base
from openquake.calculators.extract import extract
from openquake.calculators.views import view, text_table

aac = numpy.testing.assert_allclose


def get_calc_log(job_ini, hc_id=None):
    """
    :returns: (Calculator instance, LogContext instance)
    """
    log = logs.init("job", job_ini)
    if hc_id:
        log.params['hazard_calculation_id'] = hc_id
    return base.calculators(log.get_oqparam(), log.calc_id), log


def _data2rows(data):
    # used in assert_close to compare tables
    _header, *lines = data.splitlines()
    rows = []
    for line in lines:
        row = []
        for value in line.split():
            try:
                row.append(float(value))
            except ValueError:
                pass
        if row:
            rows.append(row)
    return rows


def assert_close(tbl, fname, atol=1E-5, rtol=1E-4):
    """
    Compare a text table with a filename containing the expected table
    """
    txt = tbl if isinstance(tbl, str) else text_table(tbl, ext='org')
    if os.environ.get('OQ_OVERWRITE'):
        with open(fname, 'w') as f:
            f.write(txt)
    else:
        with open(str(fname) + '~', 'w') as f:
            f.write(txt)
        with open(fname) as f:
            expected = f.read()
        for exp, got in zip(_data2rows(expected), _data2rows(txt)):
            aac(exp, got, rtol, atol)


def check(ini, hc_id=None, exports='', what='', prefix='',
          atol=1E-5, rtol=1E-4):
    """
    Perform a calculation and compare a view ("what") with the content of
    a corrisponding file (.txt or .org).
    """
    t0 = time.time()
    outdir = pathlib.Path(os.path.dirname(ini))
    calc, log = get_calc_log(ini, hc_id)
    calc.run(export_dir='/tmp', close=False)
    if exports:
        calc.export(exports)
    print('Spent %.1f seconds' % (time.time() - t0))
    if what:
        calc_id = calc.datastore.calc_id
        fname = outdir / ('%s_%s.org' % (what.replace(':', ''), calc_id))
        try:
            tbl = view(what, calc.datastore)
        except KeyError:
            try:
                dset = calc.datastore[what]
                if '__pdcolumns__' in dset.attrs:
                    df = calc.datastore.read_df(what)
                else:
                    df = hdf5.ArrayWrapper.from_(dset).to_dframe()
            except KeyError:
                df = extract(calc.datastore, what)
                if not isinstance(df, pandas.DataFrame):
                    df = df.to_dframe()
            tbl = text_table(df, ext='org')
        bname = prefix + re.sub(r'_\d+\.', '.', os.path.basename(fname))
        assert_close(tbl, outdir / bname, atol, rtol)
    return calc, log


# called in run-demos
def check_ini(path, hc):
    dic = readinput.get_params(path)
    if hc:  # disable hazard checks by setting a fake hazard_calculation_id
        dic['hazard_calculation_id'] = 0
    oq = readinput.get_oqparam(dic)
    ini = oq.to_ini()
    tmp_ini = path[:-3] + 'tmp.ini'
    print('Saving', tmp_ini)
    with open(tmp_ini, 'w') as f:
        f.write(ini)
    dic2 = readinput.get_params(tmp_ini)
    missing = set(dic) - set(dic2) - {'intensity_measure_types', 'export_dir'}
    if missing:
        raise RuntimeError(missing)
