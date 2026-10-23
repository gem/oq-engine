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
import sys
import shutil
import tempfile
import numpy
import pandas
from openquake.baselib import hdf5
from openquake.qa_tests_data import mosaic_for_ses
from openquake.commonlib.datastore import read
from openquake.calculators import base
from openquake.calculators.export import export
from openquake.calculators.views import view
from openquake.engine import global_ses
from openquake.commands.sample import reduce_rupture_file

MOSAIC_DIR = os.path.dirname(mosaic_for_ses.__file__)
RUP_HDF5 = os.path.join(MOSAIC_DIR, 'rups.hdf5')
aac = numpy.testing.assert_allclose
ae = numpy.testing.assert_equal

last_job = None

def path(job_ini):
    return os.path.join(MOSAIC_DIR, job_ini)


def count_rups(dstore, model):
    arr = dstore['ruptures'][:]
    return (arr['model'] == model.encode('ascii')).sum()


def check(dstore, calcs):
    with hdf5.File(RUP_HDF5) as ds, \
         read(calcs[0]) as ds_EUR, \
         read(calcs[1]) as ds_MIE:

        # count the ruptures outside the models
        mie_unknown = count_rups(ds_MIE, '???')
        assert mie_unknown == 0
        eur_unknown = count_rups(ds_EUR, '???')
        assert eur_unknown == 0
        
        nrup_EUR = count_rups(ds_EUR, 'EUR')
        nrup_MIE = count_rups(ds_MIE, 'MIE')
        rups = ds['ruptures'][:]
        nrup = len(rups)
        assert nrup == nrup_EUR + nrup_MIE  # no double counting


def setup_module():
    worflow_id = global_ses.main(
        MOSAIC_DIR, 'rups.hdf5', 'EUR,MIE',
        number_of_logic_tree_samples='200')

    with read(os.path.join(MOSAIC_DIR, 'rups.hdf5')) as parent:
        evs = parent['events'][:]
        assert evs.dtype.names == ('id', 'rup_id', 'rlz_id', 'year', 'ses_id')
        ae(evs['id'], numpy.arange(33965))  # sequential indices
        e0s = parent['ruptures']['e0']
        ae(e0s[-3:], [23127, 23128, 23129])  # large enough e0

    wdf = read(worflow_id).read_df('workflow')
    # case with a region
    dstore = base.run_calc(
        path('job.ini'), hazard_calculation_id='rups.hdf5',
    ).datastore
    check(dstore, list(wdf.calc_id))
    ae(dstore['source_info/EUR']['source_id'],
       [b'IF-CFS-0', b'IF-CFS-1', b'IF-CFS-2', b'IF-CFS-3'])
    ae(dstore['source_info/MIE']['source_id'],
       [b'DS-AS-AZEAS300', b'DS-AS-AZEAS301', b'DS-AS-IRNAS300',
        b'DS-AS-IRNAS301', b'DS-AS-IRNAS302', b'DS-AS-PAKAS300',
        b'IF-CFS-3', b'IF-CFS-CYSD05', b'IF-CFS-GRID03', b'IF-CFS-TRID04',
        b'SL-AS-GRIDAS08', b'SL-AS-PAKAS202', b'SL-AS-TRIDAS09',
        b'SSC-mps-0', b'SSC-mps-1:0', b'SSC-mps-1:1', b'SSC-mps-1:2',
        b'SSC-mps-1:3', b'SSC-mps-2', b'SSC-mps-3:0', b'SSC-mps-3:1',
        b'SSC-mps-4:0', b'SSC-mps-4:1'])


def test_one_site():
    global last_job
    calc = base.run_calc(
        path('job1.ini'), hazard_calculation_id='rups.hdf5')
    last_job = calc.datastore.calc_id
    df = calc.datastore.read_df('gmf_data', 'sid')
    assert len(df) == 14
    assert df.index.max() < 1

    # test multi-model rupture exporter
    [fname] = export(('ruptures', 'csv'), calc.datastore.parent)
    assert os.path.basename(fname) == 'ruptures_rups.csv'

    # check the maximum_distance is different for MIE and EUR
    assert not hasattr(calc.oqparam, 'maximum_distance')


def test_export_gmf_data_csv():
    global last_job
    calc = base.run_calc(
        path('job.ini'), hazard_calculation_id='rups.hdf5')
    last_job = calc.datastore.calc_id
    fname, sig_eps_csv, _sitemesh = export(
        ('gmf_data', 'csv'), calc.datastore)
    # sigma_epsilon event IDs must match the stored ones, not be remapped
    sig_eps = calc.datastore['gmf_data/sigma_epsilon'][()]
    df = pandas.read_csv(sig_eps_csv, comment='#')
    ae(df['event_id'].to_numpy(), numpy.sort(sig_eps['eid']))
    gmf_df = pandas.read_csv(fname, comment='#')
    assert set(df['event_id']) <= set(gmf_df['event_id'])


def test_export_realizations_csv():
    global last_job
    calc = base.run_calc(
        path('job.ini'), hazard_calculation_id='rups.hdf5')
    last_job = calc.datastore.calc_id
    fnames = export(('realizations', 'csv'), calc.datastore)
    # one file per model, with the same columns as a single model
    assert len(fnames) == 2
    for model in ['EUR', 'MIE']:
        [fname] = [f for f in fnames
                   if os.path.basename(f).startswith(f'realizations_{model}')]
        df = pandas.read_csv(fname, comment='#')
        assert list(df.columns) == ['rlz_id', 'branch_path', 'weight']
        rlzs = calc.datastore[f'full_lt/{model}'].rlzs
        ae(df['rlz_id'].to_numpy(), numpy.arange(len(rlzs)))
        ae(df['branch_path'].to_numpy(), rlzs['branch_path'])


def test_view_rlz():
    # the realization is shown for each model of the parent datastore
    with read(RUP_HDF5) as dstore:
        arr = view('rlz:0', dstore)
    assert list(arr.dtype.names) == [
        'model', 'uncertainty_type', 'uvalue']
    for model in ['EUR', 'MIE']:
        assert (arr['model'] == model).sum() > 0, model


def test_view_logic_tree():
    # the logic tree views show the rows of each model of the parent
    with read(RUP_HDF5) as dstore:
        bsets = view('branchsets', dstore)
        branches = view('branches', dstore)
        sm_rlzs = view('sm_rlzs', dstore)
    assert 'model' in bsets.splitlines()[0]
    assert 'model' in sm_rlzs.splitlines()[0]
    for model in ['EUR', 'MIE']:
        assert ('| %s ' % model) in bsets
        assert ('| %s ' % model) in sm_rlzs
    ae(sorted(set(branches['model'])), ['EUR', 'MIE'])


def test_sites():  # 5 sites
    global last_job
    calc = base.run_calc(
        path('job_sites.ini'), hazard_calculation_id='rups.hdf5')
    ae(calc.sitecol.sids, [0, 1, 2, 3, 4])
    # FIXME: the custom_site_id is not working yet
    # ae(calc.sitecol.custom_site_id,
    #    numpy.array([b'A', b'B', b'C', b'D', b'E']))
    last_job = calc.datastore.calc_id
    df = calc.datastore.read_df('gmf_data', 'sid')
    assert len(df) == 68
    assert df.index.max() < 5


def test_site_model():  # 5 sites
    global last_job
    calc = base.run_calc(
        path('job_sm.ini'), hazard_calculation_id='rups.hdf5')
    ae(calc.sitecol.sids, [0, 1, 2, 3, 4])
    last_job = calc.datastore.calc_id
    df = calc.datastore.read_df('gmf_data', 'sid')
    assert len(df) == 65
    assert df.index.max() < 5
    rdf = calc.datastore.read_df('filtered_ruptures', 'id')
    assert len(rdf) == 15870
    edf = calc.datastore.read_df('relevant_events', 'id')
    assert len(edf) == 16590
    rel_rups = rdf[numpy.isin(rdf.index, edf.rup_id)]
    assert len(rel_rups) == len(rdf)

    op_df = calc.datastore.read_df('operations')
    ae(list(op_df.columns), ['calc_id', 'model', 'sample_ruptures',
                             'read_source_model', 'count_ruptures'])


def check_reduced(fname):
    # check the links between ruptures, events and geometries
    with hdf5.File(fname + '.bak') as orig, hdf5.File(fname) as red:
        nrup_orig = len(orig['ruptures'])
        rups = red['ruptures'][:]
        evs = red['events'][:]
        assert 0 < len(rups) < nrup_orig, (len(rups), nrup_orig)
        assert len(red['rupgeoms']) == len(rups)
        ae(rups['geom_id'], numpy.arange(len(rups)))
        assert len(evs) == rups['n_occ'].sum()
        for rec in rups:
            blk = evs[rec['e0']:rec['e0'] + rec['n_occ']]
            assert (blk['rup_id'] == rec['id']).all()


def teardown_module():
    with read(RUP_HDF5) as dstore:
        occ_df = dstore.read_df('occ_by_trt_smr')
    assert list(occ_df.columns) == ['trt_smr', 'n_occ', 'name']
    # reduce a copy, since RUP_HDF5 is still open in the datastores
    tmpdir = tempfile.mkdtemp()
    tmp = os.path.join(tmpdir, 'SES.hdf5')
    shutil.copy(RUP_HDF5, tmp)
    reduce_rupture_file(tmp, .1)  # sample the ruptures
    check_reduced(tmp)
    shutil.rmtree(tmpdir)
    if sys.platform != 'win32':
        os.remove(RUP_HDF5)
    if last_job:
        # make sure `read` works after rups.hdf5 has been removed
        read(last_job)
