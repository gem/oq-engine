# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
import json
from unittest import mock
import numpy
import pandas
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
from openquake.qa_tests_data import mosaic
from openquake.commonlib import logs
from openquake.calculators import base
from openquake.calculators.export import export
from openquake.engine.aelo import get_params_from

MOSAIC_DIR = os.path.dirname(mosaic.__file__)
aac = numpy.testing.assert_allclose

# values for the CCA model
SITES = ['far -90.071 16.60'.split(), 'close -85.071 10.606'.split()]
EXPECTED_asce7_16 = [
    [0.265314, 0.273735, 0.275943, 0.309681, 0.346075, 0.383423,
     0.486398, 0.519964, 0.568014, 0.60647, 0.650083, 0.650722,
     0.563917, 0.475211, 0.362233, 0.268729, 0.205666, 0.194352,
     0.207831, 0.194923, 0.149143],
    [0.708552, 0.766141, 0.819514,
     0.992218, 1.19921, 1.33306, 1.54593, 1.60616, 1.61089, 1.59131,
     1.51552, 1.40373, 1.13522, 0.942543, 0.702805, 0.523597,
     0.415245, 0.401764, 0.43762, 0.402472, 0.305589]]
EXPECTED_asce7_22 = [
    [0.265314, 0.29862, 0.301028, 0.337834, 0.377537, 0.41828,
     0.530616, 0.567234, 0.614497, 0.650135, 0.685131, 0.67509,
     0.562095, 0.456934, 0.342549, 0.250018, 0.185246, 0.169823,
     0.176241, 0.167114, 0.129257],
    [0.708552, 0.83579, 0.894015,
     1.08242, 1.30823, 1.45425, 1.68647, 1.75218, 1.74271,
     1.70589, 1.59723, 1.4563,
     1.13155, 0.906292, 0.664615, 0.487139, 0.374017, 0.351059,
     0.371102, 0.345053, 0.264844]]
ASCE07_16 = [
    '0.50000', '0.70537', '0.35257', '0.50000', '1.50000', '1.60616',
    '0.96048', '0.85274', '1.50000', 'Very High', '0.60000', '0.94254',
    '0.94621', '0.45569', '0.60000', 'Very High']
ASCE07_22 = [
    '0.50000', '0.70537', '0.35257', '0.50000', '1.50000', '1.35', '0.9',
    '1.75218', '0.96048', '0.93027', '1.50000', 'Very High', '0.60000',
    '0.60000', '0.40000', '0.90629', '0.94621', '0.43816', '0.60000',
    'Very High']
ASCE41_17 = [1.5, 1.28283, 1.28283, 1, 0.75094, 0.75094, 0.6,
             0.6, 0.7519, 0.4, 0.4, 0.42582]
ASCE41_23 = [1.5, 1.39946, 1.39946, 1, 0.81921, 0.81921, 0.6,
             0.6, 0.72299, 0.4, 0.4, 0.40944]


def test_PAC():
    # test with same name sources and semicolon convention, full enum
    job_ini = os.path.join(MOSAIC_DIR, 'PAC/in/job_vs30.ini')
    with logs.init(job_ini) as log:
        sites = log.get_oqparam().sites
        # site (160, -9.5), first level of PGA
        lon = sites[1][0]
        lat = sites[1][1]
        lon2 = sites[0][0]
        lat2 = sites[0][1]
        site = 'PAC first'
        dic = dict(sites='%s %s, %s %s' % (lon, lat, lon2, lat2), site=site,
                   vs30='760')
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()

        r0, r1 = calc.datastore['hcurves-rlzs'][0, :, 0, 0]  # 2 rlzs
        if rtgmpy:
            a7 = json.loads(calc.datastore['asce07'][0].decode('ascii'))
            aac([r0, r1, a7['PGA']], [0.038337, 0.041893, 0.83427],
                atol=1E-6)

        # site (160, -9.4), first level of PGA
        r0, r1 = calc.datastore['hcurves-rlzs'][1, :, 0, 0]  # 2 rlzs
        if rtgmpy:
            a7 = json.loads(calc.datastore['asce07'][1].decode('ascii'))
            aac([r0, r1, a7['PGA']], [0.038544, 0.041979, 0.7959],
                atol=1E-6)

            # check that there are not warnings about results
            if 'notifications' in calc.datastore:
                notifications = calc.datastore['notifications']
                warnings = notifications[notifications['level'] == b'warning']
                assert len(warnings) == 0, f'{list(notifications)=}'

            # check no plots created
            assert 'png/governing_mce.png' not in calc.datastore
            assert 'png/hcurves.png' not in calc.datastore
            assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_KOR():
    # another test with same name sources, no semicolon convention, sampling
    job_ini = os.path.join(MOSAIC_DIR, 'KOR/in/job_vs30.ini')
    dic = dict(sites='129 35.9', site='KOR-site', vs30='760')
    with logs.init(job_ini) as log:
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    if rtgmpy:
        s = calc.datastore['asce07'][0].decode('ascii')
        asce07 = json.loads(s)
        aac(asce07['PGA'], 1.60312, atol=5E-5)
        # check all plots created
        assert 'png/governing_mce.png' in calc.datastore
        assert 'png/hcurves.png' in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' in calc.datastore


def test_CCA():
    # RTGM under and over the deterministic limit for the CCA model
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    for (site, lon, lat), expected in zip(SITES, EXPECTED_asce7_16):
        dic = dict(sites='%s %s' % (lon, lat), site=site, vs30='760')
        with logs.init(job_ini) as log:
            log.params.update(get_params_from(
                dic, MOSAIC_DIR, exclude=['USA']))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        if rtgmpy:
            [fname] = export(('rtgm', 'csv'), calc.datastore)
            df = pandas.read_csv(fname, skiprows=1)
            aac(df.RTGM, expected, atol=1.5E-4)

    if rtgmpy:
        # check asce07 exporter
        [fname] = export(('asce07', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        for got, exp in zip(df.value.to_numpy(), ASCE07_16):
            try:
                aac(float(got), float(exp), rtol=1E-2)
            except ValueError:
                numpy.testing.assert_equal(got, exp)

        # check asce41 exporter
        [fname] = export(('asce41', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        aac(df.value, ASCE41_17, atol=1.5E-4)

        # test no close ruptures
        dic = dict(sites='%s %s' % (-83.37, 15.15), site='wayfar', vs30='760')
        with logs.init(job_ini) as log:
            params = get_params_from(dic, MOSAIC_DIR, exclude=['USA'])
            params['maximum_distance'] = '300'
            log.params.update(params)
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        # check that the warning announces zero hazard
        notifications = calc.datastore['notifications']
        warnings = notifications[notifications['level'] == b'warning']
        assert len(warnings) == 1, f'{list(notifications)=}'
        assert warnings[0]['name'].decode('utf8') == 'zero_hazard'

        # check no plots created
        assert 'png/governing_mce.png' not in calc.datastore
        assert 'png/hcurves.png' not in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_CCA_asce7_22():
    # RTGM under and over the deterministic limit for the CCA model
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    for (site, lon, lat), expected in zip(SITES, EXPECTED_asce7_22):
        dic = dict(sites='%s %s' % (lon, lat), site=site, vs30='760',
                   asce_version='ASCE7-22')
        with logs.init(job_ini) as log:
            log.params.update(get_params_from(
                dic, MOSAIC_DIR, exclude=['USA']))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        if rtgmpy:
            [fname] = export(('rtgm', 'csv'), calc.datastore)
            df = pandas.read_csv(fname, skiprows=1)
            aac(df.RTGM, expected, atol=1.5E-4)

    if rtgmpy:
        # check asce07 exporter
        [fname] = export(('asce07', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        for got, exp in zip(df.value.to_numpy(), ASCE07_22):
            try:
                aac(float(got), float(exp), rtol=1E-2)
            except ValueError:
                numpy.testing.assert_equal(got, exp)

        # check asce41 exporter
        [fname] = export(('asce41', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        aac(df.value, ASCE41_23, atol=1.5E-4)


def test_WAF():
    # test of site with very low hazard
    job_ini = os.path.join(MOSAIC_DIR, 'WAF/in/job_vs30.ini')
    dic = dict(sites='7.5 9', site='WAF-site', vs30='760')
    with logs.init(job_ini) as log:
        params = get_params_from(dic, MOSAIC_DIR, exclude=['USA'])
        log.params.update(params)
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    if rtgmpy:
        # check that warning indicates zero hazard
        notifications = calc.datastore['notifications']
        warnings = notifications[notifications['level'] == b'warning']
        assert len(warnings) == 1, f'{list(notifications)=}'
        assert warnings[0]['name'].decode('utf8') == 'zero_hazard'

        # check no plots created
        assert 'png/governing_mce.png' not in calc.datastore
        assert 'png/hcurves.png' not in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore

        # test of site with very low hazard, but high enough to compute ASCE
        job_ini = os.path.join(MOSAIC_DIR, 'WAF/in/job_vs30.ini')
        dic = dict(sites='2.4 6.6', site='WAF-site', vs30='760')
        with logs.init(job_ini) as log:
            params = get_params_from(dic, MOSAIC_DIR, exclude=['USA'])
            params['maximum_distance'] = '300'
            log.params.update(params)
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()

        # check that warning indicates very low hazard
        notifications = calc.datastore['notifications']
        warnings = notifications[notifications['level'] == b'warning']
        assert len(warnings) == 1, f'{list(notifications)=}'
        assert warnings[0]['name'].decode('utf8') == 'below_min'

        # check that 2 of 3 plots have been created
        assert 'png/hcurves.png' in calc.datastore
        assert 'png/governing_mce.png' in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_JPN():
    # test with mutex sources
    job_ini = os.path.join(MOSAIC_DIR, 'JPN/in/job_vs30.ini')
    expected = os.path.join(MOSAIC_DIR, 'JPN/in/expected/uhs.csv')
    dic = dict(sites='139 36', site='JPN-site', vs30='530 760 1080')
    with logs.init(job_ini) as log:
        params = get_params_from(dic, MOSAIC_DIR, exclude=['USA'])
        params['maximum_distance'] = '300'
        log.params.update(params)
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()

    size = calc.oqparam.imtls.size  # size of the hazard curves
    assert size == 525  # 21 IMT * 25 levels

    M = len(calc.oqparam.imtls)  # set in job file
    assert M == 21

    P = len(calc.oqparam.poes)  # [0.02, 0.05, 0.1, 0.2, 0.5]
    assert P == 5

    # check export hcurves and uhs
    with mock.patch.dict(os.environ, {'OQ_APPLICATION_MODE': 'AELO'}):
        [hcurves_fname] = export(('hcurves', 'csv'), calc.datastore)
        [uhs_fname] = export(('uhs', 'csv'), calc.datastore)

    df1 = pandas.read_csv(hcurves_fname, skiprows=1)
    df2 = pandas.read_csv(uhs_fname, skiprows=1, index_col='period')
    assert len(df1) == size
    assert len(df2) == M
    expected_uhs = pandas.read_csv(expected, index_col='period')
    expected_uhs.columns = ["poe-0.02", "poe-0.05", "poe-0.1", "poe-0.2",
                            "poe-0.5"]
    for col in expected_uhs.columns:
        aac(df2[col], expected_uhs[col], atol=1E-5)

    if rtgmpy:
        # check all plots created
        assert 'png/governing_mce.png' in calc.datastore, 'governing'
        assert 'png/hcurves.png' in calc.datastore, 'hcurves'
        assert 'png/disagg_by_src-All-IMTs.png' in calc.datastore, 'disagg'


def test_MFK():
    # multifault sources with kendra-splitting in Central East Asia;
    # not testing the numbers, but preventing implementation errors like
    # the one discussed in https://github.com/gem/oq-engine/pull/10434
    job_ini = os.path.join(MOSAIC_DIR, 'Projects/AELO/aeloy3/py/Run_Jobs/'
                           'CEA/site10/job_dos_vs30_760_small.ini')
    with (mock.patch.dict(os.environ, {'OQ_DISTRIBUTE': 'no'}),
          mock.patch('openquake.hazardlib.source.multi_fault.BLOCKSIZE', 5),
          logs.init(job_ini) as log):
        base.calculators(log.get_oqparam(), log.calc_id).run()


# TODO: add cases checking warning low_hazard and info only_prob_mce
