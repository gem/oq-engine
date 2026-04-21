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

import os
import pathlib
import unittest
import pytest
import numpy
from openquake.qa_tests_data.scenario_risk import case_shakemap
from openquake.calculators.base import run_calc, expose_outputs
from openquake.calculators.views import text_table
from openquake.calculators.checkers import check, assert_close
from openquake.calculators.export import export

cd = pathlib.Path(__file__).parent
aac = numpy.testing.assert_allclose


def strip(fname):
    bname = os.path.basename(fname)
    name, ext = bname.rsplit('_', 1)
    return name + '.' + ext.rsplit('.')[1]


def check_export_job_zip(dstore):
    fnames = export(('job', 'zip'), dstore)
    assert [strip(f) for f in fnames] == [
        'job.ini',
        'exposure.xml',
        'rupture.csv',
        'gsim_logic_tree.xml',
        'affectedpop_vulnerability.xml',
        'area_vulnerability.xml',
        'contents_vulnerability.xml',
        'embodied_carbon_vulnerability.xml',
        'injured_vulnerability.xml',
        'number_vulnerability.xml',
        'occupants_vulnerability.xml',
        'residents_vulnerability.xml',
        'structural_vulnerability.xml',
        'taxonomy_mapping.csv',
        'sites.csv',
        'assetcol.csv']

    # there is no gmfs_file, since this is a test without shakemap
    return fnames


def compare(dstore1, dstore2):
    """
    Compare avg_losses and loss_by_event
    """
    ltypes = sorted(dstore1['avg_losses-stats'])
    df1 = dstore1.read_df('loss_by_event')
    df2 = dstore2.read_df('loss_by_event')
    aac(df1.to_numpy(), df2.to_numpy(), rtol=2e-2)

    for ltype in ltypes:
        avg1 = dstore1[f'avg_losses-stats/{ltype}'][:]
        avg2 = dstore2[f'avg_losses-stats/{ltype}'][:]
        for i in range(len(avg1)):
            aac(avg1[i], avg2[i], rtol=2e-2, atol=1e-3)


@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_impact(n):
    # NB: expecting exposure in oq-engine and not in mosaic_dir!
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')
    if n == 3:
        # FIXME: rupture outside Portugal
        return
    calc, log = check(cd / f'impact{n}/job.ini', what='aggrisk_tags')
    with log:  # ensures clean worker shutdown for all n
        if n == 1:
            # test export_aggexp
            fnames = export(('aggexp_tags', 'csv'), calc.datastore)
            assert [strip(f) for f in fnames] == [
                'aggexp_tags-ID_0.csv',
                'aggexp_tags-ID_2.csv']

            # [job.ini, exposure.xml, rupture.csv, ...]
            fnames = check_export_job_zip(calc.datastore)

            # repeat the calculation starting from job.zip unzipped
            calc2, log2 = check(fnames[0])
            with log2:
                expose_outputs(calc.datastore)
                expose_outputs(calc2.datastore)
                # TODO: restore the check
                #  compare(calc.datastore, calc2.datastore)


def test_impact5():
    # this is a case where there are no assets inside the MMI multipolygons
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')

    # importing the exposure around Nepal and aggregating it
    calc, _log = check(cd / 'impact5/job.ini')
    calc.assetcol.array['lon'] = 64.22
    calc.assetcol.array['lat'] = 32.82
    inp = calc.oqparam.inputs
    df = calc.assetcol.get_mmi_values(calc.oqparam.aggregate_by,
                                      inp['mmi'], inp['exposure'][0])
    tt = text_table(df, ext='org')
    assert_close(tt, cd / 'impact5/exposure_by_mmi.org')


# NB: there is another test of export_job_zip in scenario_damage/case_22
def test_shakemap():
    cdir = os.path.dirname(case_shakemap.__file__)
    precalc = run_calc(os.path.join(cdir, 'pre-job.ini'))
    precalc.datastore.close()
    calc = run_calc(os.path.join(cdir, 'job.ini'),
                    hazard_calculation_id=precalc.datastore.calc_id)
    fnames = export(('job', 'zip'), calc.datastore)
    assert [strip(f) for f in fnames] == [
        'gmf-data.csv', 'job.ini', 'exposure.xml',
        'structural_vulnerability.xml', 'taxonomy_mapping.csv',
        'sites.csv', 'assetcol.csv']
    try:
        run_calc(fnames[1])
    finally:
        # with open(fnames[1]) as f:
        #     print(f.read())
        for fname in fnames:
            os.remove(fname)
