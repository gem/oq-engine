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
def loss_curves(assets, baselosses, seed):
    numpy.random.seed(seed)
    lcs = []
    for asset in assets:
        poes = sorted(numpy.random.rand(5), reverse=True)
        losses = sorted(baselosses * asset.value('structural') + seed)
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
        baselosses = numpy.array([.10, .14, .17, .20, .21])
        for i, w in enumerate(weights):
            lc = loss_curves(assets, baselosses, i)
            out = scientific.Output(
                asset_refs, 'structural', weight=w,
                loss_curves=lc, insured_curves=None,
                average_losses=[.1, .12, .13, .9], average_insured_losses=None)
            outputs.append(out)
        cls.builder = scientific.StatsBuilder(
            quantiles=[0.1, 0.9],
            conditional_loss_poes=[0.35, 0.24, 0.13],
            poes_disagg=[], curve_resolution=len(baselosses))
        cls.stats = cls.builder.build(outputs)

    # TODO: add a test for insured curves and maps
    def test_get_stat_curves_maps(self):
        tempdir = tempfile.mkdtemp()
        curves, maps = self.builder.get_curves_maps(self.stats)
        # expecting arrays of shape (Q1, N) with Q1=3, N=4
        actual = os.path.join(tempdir, 'expected_loss_curves.csv')
        writers.write_csv(actual, curves, fmt='%05.2f')

        tests.check_equal(__file__, 'expected_loss_curves.csv', actual)

        actual = os.path.join(tempdir, 'expected_loss_maps.csv')
        writers.write_csv(actual, maps, fmt='%05.2f')
        tests.check_equal(__file__, 'expected_loss_maps.csv', actual)

        # remove only if the test pass
        shutil.rmtree(tempdir)
