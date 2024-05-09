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


SITES = ['far -90.071 16.60'.split(), 'close -85.071 10.606'.split()]
EXPECTED = [[0.30846, 0.63827, 0.727454], [0.73277, 1.76939, 1.22298]]
ASCE07 = ['0.50000', '0.75315', '0.34598', '0.50000', '1.50000', '1.76943',
          '0.95838', '0.80949', '1.50000', 'Very High', '0.60000', '1.22296',
          '0.95015', '0.48815', '0.60000', 'Very High']
ASCE41 = [1.5, 1.4308, 1.4308, 1.0, 0.83393, 0.83393, 0.6, 0.6, 0.98649, 0.4,
          0.4, 0.56995]


def test_PAC():
    # test with same name sources and semicolon convention, full enum
    job_ini = os.path.join(MOSAIC_DIR, 'PAC/in/job.ini')
    with logs.init(job_ini) as log:
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()

    # site (160, -9.5), first level of PGA
    r0, r1 = calc.datastore['hcurves-rlzs'][0, :, 0, 0]  # 2 rlzs
    if rtgmpy:
        a7 = json.loads(calc.datastore['asce07'][0].decode('ascii'))
        aac([r0, r1, a7['PGA']], [0.03272511, 0.040312827, 0.83427], atol=1E-6)

    # site (160, -9.4), first level of PGA
    r0, r1 = calc.datastore['hcurves-rlzs'][1, :, 0, 0]  # 2 rlzs
    if rtgmpy:
        a7 = json.loads(calc.datastore['asce07'][1].decode('ascii'))
        aac([r0, r1, a7['PGA']], [0.032720476, 0.040302116, 0.7959], atol=1E-6)

        # check that there are not warnings about results
        warnings = [s.decode('utf8') for s in calc.datastore['warnings']]
        assert sum([len(w) for w in warnings]) == 0

        # check all plots created
        assert 'png/governing_mce.png' not in calc.datastore
        assert 'png/hcurves.png' not in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_KOR():
    # another test with same name sources, no semicolon convention, sampling
    job_ini = os.path.join(MOSAIC_DIR, 'KOR/in/job_vs30.ini')
    dic = dict(sites='128.8 35', site='KOR-site', vs30='760')
    with logs.init(job_ini) as log:
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    if rtgmpy:
        s = calc.datastore['asce07'][0].decode('ascii')
        asce07 = json.loads(s)
        aac(asce07['PGA'], 0.618, atol=5E-5)

        # check all plots created
        assert 'png/governing_mce.png' in calc.datastore
        assert 'png/hcurves.png' in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' in calc.datastore


def test_CCA():
    # RTGM under and over the deterministic limit for the CCA model
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    for (site, lon, lat), expected in zip(SITES, EXPECTED):
        dic = dict(sites='%s %s' % (lon, lat), site=site, vs30='760')
        with logs.init(job_ini) as log:
            log.params.update(get_params_from(
                dic, MOSAIC_DIR, exclude=['USA']))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        if rtgmpy:
            [fname] = export(('rtgm', 'csv'), calc.datastore)
            df = pandas.read_csv(fname, skiprows=1)
            aac(df.RTGM, expected, atol=5E-5)

    if rtgmpy:
        # check asce07 exporter
        [fname] = export(('asce07', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        for got, exp in zip(df.value.to_numpy(), ASCE07):
            try:
                aac(float(got), float(exp), rtol=1E-2)
            except ValueError:
                numpy.testing.assert_equal(got, exp)

        # check asce41 exporter
        [fname] = export(('asce41', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        aac(df.value, ASCE41, atol=5E-5)

        # test no close ruptures
        dic = dict(sites='%s %s' % (-83.37, 15.15), site='wayfar', vs30='760')
        with logs.init(job_ini) as log:
                log.params.update(get_params_from(
                    dic, MOSAIC_DIR, exclude=['USA']))
                calc = base.calculators(log.get_oqparam(), log.calc_id)
                calc.run()
        # check that the warning announces no close ruptures
        warnings = [s.decode('utf8') for s in calc.datastore['warnings']]
        assert len(warnings) == 1
        assert warnings[0].startswith('Zero hazard')

        # check no plots created
        assert 'png/governing_mce.png' not in calc.datastore
        assert 'png/hcurves.png' not in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_WAF():
    # test of site with very low hazard
    job_ini = os.path.join(MOSAIC_DIR, 'WAF/in/job_vs30.ini')
    dic = dict(sites='9 9', site='WAF-site', vs30='760')
    with logs.init(job_ini) as log:
        log.params.update(get_params_from(
            dic, MOSAIC_DIR, exclude=['USA']))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    if rtgmpy:
        # check that warning indicates very low hazard
        warnings = [s.decode('utf8') for s in calc.datastore['warnings']]
        assert len(warnings) == 1
        assert warnings[0].startswith('Very low')

        # check no plots created
        assert 'png/governing_mce.png' not in calc.datastore
        assert 'png/hcurves.png' not in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore

        # test of site with very low hazard, but high enough to compute ASCE
        job_ini = os.path.join(MOSAIC_DIR, 'WAF/in/job_vs30.ini')
        dic = dict(sites='10.93 5.65', site='WAF-site', vs30='760')
        with logs.init(job_ini) as log:
            log.params.update(get_params_from(
                dic, MOSAIC_DIR, exclude=['USA']))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        # check that warning indicates very low hazard
        warnings = [s.decode('utf8') for s in calc.datastore['warnings']]
        assert len(warnings) == 1
        assert warnings[0].startswith('The MCE')

        # check that 2/3 plots created
        assert 'png/governing_mce.png' in calc.datastore
        assert 'png/hcurves.png' in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' not in calc.datastore


def test_JPN():
    # test with mutex sources
    job_ini = os.path.join(MOSAIC_DIR, 'JPN/in/job_vs30.ini')
    dic = dict(sites='139 36', site='JPN-site', vs30='760')
    with logs.init(job_ini) as log:
        log.params.update(get_params_from(
            dic, MOSAIC_DIR, exclude=['USA']))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()

    if rtgmpy:
        # check all plots created
        assert 'png/governing_mce.png' in calc.datastore
        assert 'png/hcurves.png' in calc.datastore
        assert 'png/disagg_by_src-All-IMTs.png' in calc.datastore
