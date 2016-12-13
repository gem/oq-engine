# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

from __future__ import division
import unittest
import os.path
import shutil
import tempfile
import numpy

from openquake.risklib import scientific, riskmodels
from openquake.commonlib import writers, tests

aaae = numpy.testing.assert_array_almost_equal
F32 = numpy.float32


class NormalizeTestCase(unittest.TestCase):

    def test_normalize_all_trivial(self):
        poes = numpy.linspace(1, 0, 11)
        losses = numpy.zeros(11)
        curves = [[losses, poes], [losses, poes / 2]]
        exp_losses, (poes1, poes2) = scientific.normalize_curves_eb(curves)

        numpy.testing.assert_allclose(exp_losses, losses)
        numpy.testing.assert_allclose(poes1, poes)
        numpy.testing.assert_allclose(poes2, poes / 2)

    def test_normalize_one_trivial(self):
        trivial = [numpy.zeros(6), numpy.linspace(1, 0, 6)]
        curve = [numpy.linspace(0., 1., 6), numpy.linspace(1., 0., 6)]
        with numpy.errstate(invalid='ignore', divide='ignore'):
            exp_losses, (poes1, poes2) = scientific.normalize_curves_eb(
                [trivial, curve])

        numpy.testing.assert_allclose(exp_losses, curve[0])
        numpy.testing.assert_allclose(poes1, [0, 0., 0., 0., 0., 0.])
        numpy.testing.assert_allclose(poes2, curve[1])


def asset(ref, value, deductibles=None,
          insurance_limits=None,
          retrofitteds=None):
    return riskmodels.Asset(
        ref, 'taxonomy', 1, (0, 0), dict(structural=value),
        1, deductibles, insurance_limits, retrofitteds)


# return a matrix N x 2 x R with n=2, R=5
def loss_curves(assets, ratios, seed):
    numpy.random.seed(seed)
    lcs = []
    for asset in assets:
        poes = sorted(numpy.random.rand(5), reverse=True)
        losses = sorted(ratios * asset.value('structural'))
        lcs.append((losses, poes))
    return numpy.array(lcs)


class StatsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assets = [asset('a1', 101), asset('a2', 151), asset('a3', 91),
                  asset('a4', 81)]
        asset_refs = [a.id for a in assets]
        outputs = []
        weights = [0.3, 0.7]
        ratios = numpy.array([.10, .14, .17, .20, .21])
        cls.curve_resolution = len(ratios)
        for i, w in enumerate(weights):
            lc = loss_curves(assets, ratios, i)
            out = scientific.Output(
                asset_refs, 'structural', weight=w,
                loss_curves=lc, insured_curves=None,
                average_losses=[.1, .12, .13, .9], average_insured_losses=None)
            outputs.append(out)
        cls.builder = scientific.StatsBuilder(
            [0.1, 0.9], [0.35, 0.24, 0.13], scientific.normalize_curves_eb)
        cls.stats = cls.builder.build(outputs)

    # TODO: add a test for insured curves and maps
    def test_get_stat_curves_maps(self):
        tempdir = tempfile.mkdtemp()
        curves, maps = self.builder._get_curves_maps(
            self.stats, self.curve_resolution)
        # expecting arrays of shape (Q1, N) with Q1=3, N=4
        actual = os.path.join(tempdir, 'expected_loss_curves.csv')
        writers.write_csv(actual, curves, fmt='%05.2f')

        tests.check_equal(__file__, 'expected_loss_curves.csv', actual)

        actual = os.path.join(tempdir, 'expected_loss_maps.csv')
        writers.write_csv(actual, maps, fmt='%05.2f')
        tests.check_equal(__file__, 'expected_loss_maps.csv', actual)

        # remove only if the test pass
        shutil.rmtree(tempdir)

    def test_build_agg_curve_stats(self):
        R = 2
        I = 1
        rlzs = [{'weight': 0.5}] * R
        dt = numpy.dtype([('losses', (F32, 20)), ('poes', (F32, 20)),
                          ('avg', F32)])
        loss_curve_dt = numpy.dtype([('contents', dt)])
        array = numpy.zeros((R, I), loss_curve_dt)
        ac = array['contents']
        ac['losses'][0] = [
            0.0, 24.29524, 48.59048, 72.88572, 97.18096, 121.4762, 145.77144,
            170.06668, 194.36192, 218.65717, 242.9524, 267.24765, 291.54288,
            315.8381, 340.13336, 364.4286, 388.72385, 413.01907, 437.31433,
            461.60956]
        ac['poes'][0] = [
            0.7274682, 0.7134952, 0.6671289, 0.5725851, 0.5725851, 0.5034147,
            0.39346933, 0.36237186, 0.2591818, 0.2591818, 0.2591818, 0.2591818,
            0.139292, 0.139292, 0.09516257, 0.09516257, 0.048770547,
            0.048770547, 0.048770547, 0.0]
        ac['avg'][0] = 140.93018
        ac['losses'][1] = [
            0.0, 28.269579, 56.539158, 84.80874, 113.078316, 141.3479,
            169.61748, 197.88705, 226.15663, 254.42621, 282.6958, 310.96536,
            339.23495, 367.50455, 395.7741, 424.0437, 452.31326, 480.58286,
            508.85242, 537.122]
        ac['poes'][1] = [
            0.7134952, 0.7134952, 0.63212055, 0.5276334, 0.4779542,
            0.36237186, 0.32967997, 0.2591818, 0.2591818, 0.2591818,
            0.139292, 0.09516257, 0.09516257, 0.09516257, 0.048770547,
            0.048770547, 0.048770547, 0.048770547, 0.048770547, 0.0]
        ac['avg'][1] = 136.99948
        dstore = {'agg_curve-rlzs': array, 'realizations': rlzs}

        # build the stats
        acs = self.builder.build_agg_curve_stats(
            loss_curve_dt, dstore)['contents']

        # 0=mean, 1=quantile-0.1 and 2=quantile-0.9
        aaae(acs['avg'], [138.96482849, 136.9994812, 140.14404297])

        # check the losses are always the same for all stats
        aaae(acs['losses'][0], acs['losses'][1])
        aaae(acs['losses'][1], acs['losses'][2])

        # check the mean poes
        mean_poes = [0.720482, 0.709703, 0.634159, 0.550109, 0.502639,
                     0.38793, 0.346313, 0.259182, 0.259182, 0.259182,
                     0.161121, 0.117227, 0.095978, 0.092226, 0.048771,
                     0.048771, 0.033716, 0.024385, 0.024385, 0.]
        aaae(acs['poes'][0], mean_poes)

        # manual computation
        losses, all_poes = scientific.normalize_curves_eb(
            [(rec['losses'], rec['poes']) for rec in ac[:, 0]])
        stats = scientific.SimpleStats(
            rlzs, [0.1, 0.9]).compute('agg_curve', dstore).T
        import pdb; pdb.set_trace()
