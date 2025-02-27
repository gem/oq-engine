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
import sys
import numpy
from numpy.testing import assert_almost_equal as aae
from openquake.qa_tests_data.scenario import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8,
    case_9, case_10, case_11, case_12, case_13, case_14, case_15, case_16,
    case_17, case_18, case_19, case_20, case_21, case_22, case_23, case_24,
    case_26, case_27, case_28, case_29, case_30, case_31, case_32, case_33,
    case_34, case_35)
from openquake.baselib import hdf5
from openquake.baselib.general import gettemp
from openquake.hazardlib import InvalidFile, nrml
from openquake.calculators import base, getters
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.views import text_table, view
from openquake.calculators.tests import CalculatorTestCase, ignore_gsd_fields


def count_close(gmf_value, gmvs_site_one, gmvs_site_two, delta=0.1):
    """
    Count the number of pairs of gmf values
    within the specified range.
    See https://bugs.launchpad.net/openquake/+bug/1097646
    attached Scenario Hazard script.
    """
    lower_bound = gmf_value - delta / 2.
    upper_bound = gmf_value + delta / 2.
    return sum((lower_bound <= v1 <= upper_bound) and
               (lower_bound <= v2 <= upper_bound)
               for v1, v2 in zip(gmvs_site_one, gmvs_site_two))


class ScenarioTestCase(CalculatorTestCase):

    def frequencies(self, case, fst_value, snd_value):
        self.execute(case.__file__, 'job.ini')
        df = self.calc.datastore.read_df('gmf_data', 'sid')
        gmvs0 = df.loc[0]['PGA'].to_numpy()
        gmvs1 = df.loc[1]['PGA'].to_numpy()
        realizations = float(self.calc.oqparam.number_of_ground_motion_fields)
        gmvs_within_range_fst = count_close(fst_value, gmvs0, gmvs1)
        gmvs_within_range_snd = count_close(snd_value, gmvs0, gmvs1)
        return (gmvs_within_range_fst / realizations,
                gmvs_within_range_snd / realizations)

    def medians(self, case):
        self.execute(case.__file__, 'job.ini')
        df = self.calc.datastore.read_df('gmf_data', 'sid')
        median = {imt: [] for imt in self.calc.oqparam.imtls}
        for imt in self.calc.oqparam.imtls:
            for sid in self.calc.sitecol.sids:
                gmvs = df.loc[sid][imt].to_numpy()
                median[imt].append(numpy.median(gmvs))
        return median

    def test_case_1(self):
        # 2 out of 3 sites filtered out by maximum_distance=5.0
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'BooreAtkinson2008_gmf.csv', out['gmf_data', 'csv'][0])

    def test_case_2(self):
        medians = self.medians(case_2)['PGA']
        aae(medians, [0.37412136, 0.19021782, 0.1365383], decimal=2)

    def test_case_2_bis(self):
        # consider 2 different error situations

        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_2.__file__, 'job.ini', gsim='')
        self.assertIn('Missing gsim or gsim_logic_tree_file',
                      str(ctx.exception))

        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_2.__file__, 'job_wrong.ini')
        self.assertIn('missing gsim or gsim_logic_tree_file',
                      str(ctx.exception))

    def test_case_3(self):
        medians_dict = self.medians(case_3)
        medians_pga = medians_dict['PGA']
        medians_sa = medians_dict['SA(0.1)']
        aae(medians_pga, [0.48155582, 0.21123045, 0.14484586], decimal=2)
        aae(medians_sa, [0.92, 0.41, 0.27], decimal=2)

    def test_case_4(self):
        medians = self.medians(case_4)['PGA']
        aae(medians, [0.41615372, 0.22797466, 0.1936226], decimal=2)

    def test_case_5(self):
        f1, f2 = self.frequencies(case_5, 0.5, 1.0)
        aae(f1, 0.03, decimal=2)
        aae(f2, 0.003, decimal=3)

    def test_case_6(self):
        f1, f2 = self.frequencies(case_6, 0.5, 1.0)
        aae(f1, 0.05, decimal=2)
        aae(f2, 0.0077, decimal=3)

    def test_case_7(self):
        f1, f2 = self.frequencies(case_7, 0.5, 1.0)
        aae(f1, 0.02, decimal=2)
        aae(f2, 0.002, decimal=3)

    def test_case_8(self):
        # test for a GMPE requiring hypocentral depth, since it was
        # broken: https://bugs.launchpad.net/oq-engine/+bug/1334524
        # I am not really checking anything, only that it runs
        f1, f2 = self.frequencies(case_8, 0.5, 1.0)
        self.assertAlmostEqual(f1, 0)
        self.assertAlmostEqual(f2, 0)

    def test_case_9(self):
        # test for minimum_distance
        out = self.run_calc(case_9.__file__, 'job.ini', exports='csv')
        f = out['gmf_data', 'csv'][0]
        self.assertEqualFiles('gmf.csv', f)

        # test the realizations export
        [f] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('realizations.csv', f)

    def test_case_10(self):
        # test importing an exposure with automatic gridding
        self.run_calc(case_10.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['sitecol']), 66)

    def test_case_11(self):
        # importing exposure + site model with duplicate sites
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_11.__file__, 'job.ini')
        self.assertIn('duplicate sites', str(ctx.exception))

    def test_case_12(self):
        # test for DowrickRhoades2005Asc IPE with MMI
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        gmf_data, sig_eps, _sitemesh = out['gmf_data', 'csv']
        self.assertEqualFiles('gmf.csv', gmf_data)
        self.assertEqualFiles('sig_eps.csv', sig_eps)

    def test_case_13(self):
        # multi-rupture scenario with 2 ruptures, 10 rlzs, 10 gmfs, 100 sites
        self.run_calc(case_13.__file__, 'job.ini')
        gmf_df = self.calc.datastore.read_df('gmf_data')
        counts_by_eid = gmf_df[['eid', 'sid']].groupby('eid').count()
        self.assertEqual(len(counts_by_eid), 200)  # there are 2x10x10 events
        # the first rupture touches 6 sites, the second 4 sites, so
        # there are 600+400 = 1000 GMVs
        self.assertEqual(4*(counts_by_eid.sid == 4).sum(), 400)
        self.assertEqual(6*(counts_by_eid.sid == 6).sum(), 600)

        # check the branches
        tbl = text_table(view('branches', self.calc.datastore))
        self.assertEqualFiles('expected/branches.org', gettemp(tbl))

    def test_case_14(self):
        # Swiss GMPEs with amplfactor
        self.run_calc(case_14.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['gmf_data/eid']), 1000)

    def test_case_15(self):
        # choosing invalid GMPE
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_15.__file__, 'job.ini')
        self.assertIn("([AtkinsonBoore2006Modified2011], PGA, "
                      "CorrelationButNoInterIntraStdDevs)", str(ctx.exception))

    def test_case_16(self):
        # check exposures with exposureFields
        self.run_calc(case_16.__file__, 'job.ini')
        assetcol = self.calc.datastore['assetcol']
        self.assertEqual(len(assetcol), 2372)
        self.assertEqual(
            sorted(assetcol.array.dtype.names),
            ['ID_1', 'ID_2', 'NAME_1', 'NAME_2', 'OCCUPANCY', 'id',
             'ideductible', 'lat', 'lon', 'occupants_avg', 'occupants_night',
             'ordinal', 'site_id', 'taxonomy', 'value-area', 'value-contents',
             'value-nonstructural', 'value-number', 'value-structural'])

    def test_case_17(self):
        # CSV exposure in latin1
        self.run_calc(case_17.__file__, 'job.ini')
        rows = [row.decode('utf8').split(',')
                for row in self.calc.datastore['agg_keys'][:]]
        header = self.calc.oqparam.aggregate_by
        tbl = text_table(rows, header=header, ext='org')
        self.assertEqualFiles('agg_keys.org', gettemp(tbl))

    def test_case_18(self):
        # 1 rupture with KiteSurfaces, number_of_ground_motion_fields=10
        self.run_calc(case_18.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['rupgeoms']), 10)

    def test_case_19(self):
        # reading CSV ruptures with missing TRTs
        self.run_calc(case_19.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['rupgeoms']), 1)

    def test_case_20(self):
        # epsilon_tau
        self.run_calc(case_20.__file__, 'job.ini')
        old = self.calc.datastore.read_df('gmf_data/sigma_epsilon', 'eid')
        self.run_calc(case_20.__file__, 'job.ini',
                      gsim_logic_tree_file='epsilon_tau.xml')
        aae(old.sig_inter_PGA.unique(), 0.3501)
        aae(old.eps_inter_PGA.mean(), 0.027470892)
        # `set_between_epsilon` sets `sig_inter` to zero
        new = self.calc.datastore.read_df('gmf_data/sigma_epsilon', 'eid')
        aae(new.sig_inter_PGA.unique(), 0)
        aae(new.eps_inter_PGA.mean(), 0.027470892)

    def test_case_21_stations(self):
        # conditioned gmfs
        self.run_calc(case_21.__file__, 'job.ini', concurrent_tasks='0')
        fname, _, _ = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('gmf-data.csv', fname)

        # check that stations are discarded when extracting avg_gmf
        aw = extract(self.calc.datastore, 'avg_gmf?imt=PGA')
        self.assertEqual(len(aw.PGA), 571)

    def test_case_21_different_columns_stations(self):
        # conditioned gmfs
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_21.__file__, 'job_different_columns.ini',
                          concurrent_tasks='0')
        self.assertIn("Fields {'custom_site_id'} present in",
                      str(ctx.exception))
        self.assertIn("were not found in", str(ctx.exception))

    def test_case_22(self):
        # check that exported GMFs are importable
        self.run_calc(case_22.__file__, 'job.ini')
        df0 = self.calc.datastore.read_df('gmf_data')
        gmfs, _, sites = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('gmf-data.csv', gmfs)
        self.assertEqualFiles('sitemesh.csv', sites)
        self.run_calc(case_22.__file__, 'job_from_csv.ini')
        ds = self.calc.datastore

        # check the 4 sites and 4x10 GMVs were imported correctly
        self.assertEqual(len(ds['sitecol']), 4)
        self.assertEqual(len(ds['gmf_data/sid']), 40)
        df1 = self.calc.datastore.read_df('gmf_data')
        for gmv in 'PGA SA(0.3) SA(0.6) SA(1.0)'.split():
            for g1, g2 in zip(df0[gmv], df1[gmv]):
                assert abs(g1-g2) < 5E-6, (gmv, g1, g2)

    def test_case_22_bis(self):
        # check that exported GMFs are importable, with custom_site_id
        # and a filtered site collection
        self.run_calc(case_22.__file__, 'job_bis.ini')
        df0 = self.calc.datastore.read_df('gmf_data')
        gmfs, _, sites = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('gmfdata.csv', gmfs)
        self.assertEqualFiles('sitemodel.csv', sites)
        self.run_calc(case_22.__file__, 'job_from_csv.ini',
                      gmfs_file='gmfdata.csv', sites_csv='sitemodel.csv')
        self.assertEqual(str(self.calc.sitecol),
                         '<SiteCollection with 1/1 sites>')
        ds = self.calc.datastore
        # check the 4 of 5 sites and 4x10 GMVs were imported correctly
        self.assertEqual(len(ds['sitecol']), 1)
        self.assertEqual(len(ds['gmf_data/sid']), 10)
        df1 = self.calc.datastore.read_df('gmf_data')
        for gmv in 'PGA SA(0.3) SA(0.6) SA(1.0)'.split():
            for g0, g1 in zip(df0[gmv], df1[gmv]):
                assert abs(g0-g1) < 6E-6, (gmv, g0, g1)

    def test_case_23(self):
        # check exposure with duplicates
        with self.assertRaises(nrml.DuplicatedID):
            self.run_calc(case_23.__file__, 'job.ini')

    def test_case_24_stations(self):
        # conditioned GMFs with AbrahamsonEtAl2014 (ry0)
        self.run_calc(case_24.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f,
                              ignore_gsd_fields, delta=1E-5)

    def test_case_24_station_with_zero_im_value_stations(self):
        # conditioned GMFs with AbrahamsonEtAl2014 (ry0)
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_24.__file__,
                          'job_station_with_zero_im_value.ini')
        self.assertIn(
            'Please remove station data with zero intensity value from',
            str(ctx.exception))
        self.assertIn(
            'stationlist_seismic_zero_im_value.csv',
            str(ctx.exception))

    def test_case_26_stations(self):
        # conditioned GMFs with extreme_gmv
        self.run_calc(case_26.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        if sys.platform != 'darwin':
            self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_27(self):
        # TodorovicSilva2022NonParametric
        self.run_calc(case_27.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_28(self):
        # rupture_dict without msr
        self.run_calc(case_28.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        if sys.platform != 'darwin':
            self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)
        rup = getters.get_ebruptures(self.calc.datastore)[0].rupture
        mesh = rup.surface.mesh
        aae(mesh.lons, [0., 0., 0., 0.])
        aae(mesh.lats, [-0.1296836,  0.1296836, -0.1296836,  0.1296836])

        # rupture_dict with msr
        self.run_calc(case_28.__file__, 'job2.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf2.csv', f, delta=1E-5)
        rup = getters.get_ebruptures(self.calc.datastore)[0].rupture
        mesh = rup.surface.mesh
        aae(mesh.lons, [0., 0., 0., 0.])
        aae(mesh.lats, [-0.07377,  0.07377, -0.07377,  0.07377])

    def test_case_29(self):
        # conditioned GMFs all stations filtered
        self.run_calc(case_29.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        if sys.platform != 'darwin':
            self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_30(self):
        # ManeaEtAl2021 with site parameter f0
        self.run_calc(case_30.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        if sys.platform != 'darwin':
            self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_31(self):
        # reading a multisurface mesh with non-homogeneous sizes
        self.run_calc(case_31.__file__, 'job.ini')

    def test_case_32(self):
        # CanadaSHM6 GMPEs with ModifiableGMPE
        self.run_calc(case_32.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_33(self):
        # merge gmfs and events
        self.run_calc(case_33.__file__, 'job1.ini')
        ds1 = self.calc.datastore
        self.assertEqual(len(ds1['sitecol']), 45)
        self.assertEqual(len(ds1['gmf_data/sid']), 45)

        self.run_calc(case_33.__file__, 'job2.ini')
        ds2 = self.calc.datastore
        self.assertEqual(len(ds2['sitecol']), 27)
        self.assertEqual(len(ds2['gmf_data/sid']), 27)

        oq = ds1['oqparam']
        oq.number_of_logic_tree_samples = 1
        oq.inputs['gmfs'] = [ds1.filename, ds2.filename]
        fname = gettemp(suffix='.hdf5')
        with hdf5.File(fname, 'w') as h5:
            base.import_gmfs_hdf5(h5, oq)
        with hdf5.File(fname, 'r') as ds:
            sids = ds['sitecol'].sids
            g_sids = ds['gmf_data/sid'][:]
            assert 'ruptures' not in ds
        aae(sids, numpy.unique(g_sids))
        self.assertEqual(len(g_sids), 45+2)

        # no GMFs, merge ruptures and events
        oq.ground_motion_fields = False
        fnames = [ds1.filename, ds2.filename]
        fname = gettemp(suffix='.hdf5')
        with hdf5.File(fname, 'w') as h5:
            base.import_ruptures_hdf5(h5, fnames)
        geoms = []
        with hdf5.File(fname, 'r') as ds:
            evs = ds['events'][:]
            rups = ds['ruptures'][:]
            geoms.extend(ds['rupgeoms'][:])
        aae(rups['e0'], [0, 1])
        aae(rups['geom_id'], [0, 1])
        self.assertEqual(len(rups), 2)
        self.assertEqual(len(geoms), 2)
        aae(evs['id'], [0, 1])
        aae(evs['rup_id'], [0, 1])
        aae(evs['rlz_id'], [0, 0])

    def test_case_34(self):
        # NZNSHM2022 gsims
        self.run_calc(case_34.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)

    def test_case_35(self):
        # GMPETable with local file
        self.run_calc(case_35.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f, delta=1E-5)
        fname = os.path.join(os.path.dirname(case_35.__file__),
                             'Wcrust_med_rhypo.hdf5')
        try:
            # check that even by removing the .hdf5 table
            # the GMPETable can be instantiated, since
            # GsimLogicTree.__from__hdf5__ reads from the attributes
            os.rename(fname, fname + '.bak')
            gsim_lt = self.calc.datastore['full_lt'].gsim_lt
            print(gsim_lt)
        finally:
            os.rename(fname + '.bak', fname)
