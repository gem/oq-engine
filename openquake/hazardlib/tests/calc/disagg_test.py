# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os.path
import numpy
import pytest

from openquake.baselib.general import pprod
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.calc import disagg, filters
from openquake.hazardlib import nrml, read_input, valid
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.gsim.campbell_2003 import Campbell2003
from openquake.hazardlib.geo import Point
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.gsim.bradley_2013 import Bradley2013
from openquake.hazardlib import sourceconverter

DATA_PATH = os.path.dirname(__file__)
aac = numpy.testing.assert_allclose


class BuildDisaggDataTestCase(unittest.TestCase):

    def test_disagg_by_mag(self):
        fname = os.path.join(DATA_PATH, 'data', 'ssm.xml')
        converter = sourceconverter.SourceConverter(50., 1., 10, 0.1, 10)
        groups = to_python(fname, converter)
        sources = []
        for g in groups:
            sources += g.sources
        site = Site(Point(172.63, -43.53), vs30=250, vs30measured=False,
                    z1pt0=330)
        imt = SA(3.0)
        iml = 0.25612220
        gsim_by_trt = {"Active Shallow Crust": Bradley2013()}
        truncation_level = 3.0
        n_epsilons = 1
        mag_bin_width = 0.1
        dist_bin_width = 100.
        coord_bin_width = 100.
        # Compute the disaggregation matrix
        edges, mtx = disagg.disaggregation(sources, site, imt, iml,
                                           gsim_by_trt, truncation_level,
                                           n_epsilons, mag_bin_width,
                                           dist_bin_width, coord_bin_width)
        by_mag = valid.mag_pmf(mtx[:, :, :, :, :, 0])
        self.assertEqual(by_mag.shape, (31,))


class DigitizeLonsTestCase(unittest.TestCase):

    def setUp(self):
        # First test
        self.lons1 = numpy.array([179.2, 179.6, 179.8, -179.9, -179.7, -179.1])
        self.bins1 = numpy.array([179.0, 179.5, 180.0, -179.5, -179])
        # Second test
        self.lons2 = numpy.array([90.0, 90.3, 90.5, 90.7, 91.3])
        self.bins2 = numpy.array([90.0, 90.5, 91.0, 91.5])

    def test1(self):
        idx = disagg._digitize_lons(self.lons1, self.bins1)
        expected = numpy.array([0, 1, 1, 2, 2, 3], dtype=int)
        numpy.testing.assert_equal(idx, expected)

    def test2(self):
        idx = disagg._digitize_lons(self.lons2, self.bins2)
        expected = numpy.array([0, 0, 1, 1, 2], dtype=int)
        numpy.testing.assert_equal(idx, expected)


class DisaggregateTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # reading two multifault sources and a site
        d = os.path.dirname(os.path.dirname(__file__))
        source_model = os.path.join(d, 'source_model/multi-point-source.xml')
        [cls.sources] = nrml.to_python(source_model, SourceConverter(
            investigation_time=50., rupture_mesh_spacing=2.))
        cls.site = Site(Point(0.1, 0.1), 800, z1pt0=100., z2pt5=1.)
        cls.imt = PGA()
        cls.iml = 0.1
        cls.truncation_level = 1.
        cls.trt = 'Stable Continental Crust'
        gsim = Campbell2003()
        cls.gsims = {cls.trt: gsim}
        mags = cls.sources[0].get_mags()
        maxdist = filters.IntegrationDistance.new('200.')
        oq = unittest.mock.Mock(truncation_level=cls.truncation_level,
                                investigation_time=50.,
                                imtls={'PGA': [cls.iml]},
                                rlz_index=[0, 1],
                                poes=[None],
                                num_epsilon_bins=3,
                                mag_bin_width=.075,
                                distance_bin_width=10,
                                coordinate_bin_width=100,
                                maximum_distance=maxdist,
                                mags_by_trt={cls.trt: mags},
                                disagg_bin_edges={})
        sitecol = SiteCollection([cls.site])
        cls.bin_edges, _ = disagg.get_edges_shapedic(oq, sitecol)
        cls.cmaker = ContextMaker(cls.trt, {gsim: [0]}, oq)
        cls.sources[0].grp_id = 0
        cls.cmaker.grp_id = 0
        cls.cmaker.poes = [.001]

    def test_minimum_distance(self):
        # a test sensitive to gsim.minimum_distance
        bin_edges, matrix = disagg.disaggregation(
            self.sources, self.site, self.imt, self.iml, self.gsims,
            self.truncation_level, n_epsilons=3,
            mag_bin_width=3, dist_bin_width=4, coord_bin_width=2.4)
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        aaae = numpy.testing.assert_array_almost_equal
        aaae(mag_bins, [3, 6, 9])
        aaae(dist_bins, [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52,
                         56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104,
                         108, 112])
        aaae(lon_bins[0], [-0.904195, 1.104195])
        aaae(lat_bins[0], [-0.904194, 1.104194])
        aaae(eps_bins, [-1, -0.3333333, 0.3333333, 1])
        self.assertEqual(trt_bins, [self.trt])
        aaae(matrix.shape, (2, 28, 1, 1, 3, 1))
        aaae(matrix.sum(), 6.14179818e-11)

    def test_disaggregator(self):
        dis = disagg.Disaggregator([self.sources[0]], self.site, self.cmaker,
                                   self.bin_edges)
        imldic = {'PGA': .01}
        mat3 = dis.disagg_mag_dist_eps(imldic, [1.])[..., 0]
        bymag = pprod(disagg.to_probs(mat3), axis=(1, 2))
        aac(bymag, [0.9873275537163634,
                    0.9580616631998118,
                    0.8081509254139463])

    def test_with_bins(self):

        bine = {'mag': numpy.arange(3, 9+0.01, 3),
                'dist': numpy.array([0, 5, 10, 20, 40, 80, 160]),
                'eps': numpy.array([-3, -1, 0, 1, 3])}

        _, matrix = disagg.disaggregation(
            self.sources, self.site, self.imt, self.iml, self.gsims,
            self.truncation_level, coord_bin_width=2.4, bin_edges=bine)

        aaae = numpy.testing.assert_array_almost_equal
        aaae(matrix.sum(), 6.14179818e-11)

        
class PMFExtractorsTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.aae = numpy.testing.assert_almost_equal

        # test matrix is not normalized, but that's fine for test
        self.matrix = numpy.array(
            [  # magnitude
                [  # distance
                    [  # longitude
                        [  # latitude
                            [  # epsilon
                                0.10, 0.11, 0.12],
                            [
                                0.00, 0.10, 0.20]],
                        [
                            [
                                0.74, 0.20, 0.95],
                            [
                                0.52, 0.49, 0.21]]],
                    [
                        [
                            [
                                0.16, 0.61, 0.53],
                            [
                                0.95, 0.34, 0.31]],
                        [
                            [
                                0.5, 0.61, 0.7],
                            [
                                0.40, 0.84, 0.24]]]],
                [
                    [
                        [
                            [
                                0.40, 0.32, 0.06],
                            [
                                0.47, 0.93, 0.70]],
                        [
                            [
                                0.03, 0.94, 0.12],
                            [
                                0.93, 0.13, 0.23]]],
                    [
                        [
                            [
                                0.11, 0.85, 0.85],
                            [
                                0.67, 0.84, 0.41]],
                        [
                            [
                                0.39, 0.88, 0.20],
                            [
                                0.14, 0.61, 0.67]]]]])

    def test_mag(self):
        pmf = valid.mag_pmf(self.matrix)
        self.aae(pmf, [1.0, 1.0])

    def test_dist(self):
        pmf = valid.dist_pmf(self.matrix)
        self.aae(pmf, [1.0, 1.0])

    def test_trt(self):
        pmf = valid.trt_pmf(self.matrix[None])
        # NB: self.matrix.shape -> (2, 2, 2, 2, 3)
        # self.matrix[None].shape -> (1, 2, 2, 2, 2, 3)
        self.aae(pmf, [1.0])

    def test_mag_dist(self):
        pmf = valid.mag_dist_pmf(self.matrix)
        self.aae(pmf, [[0.9989792, 0.999985], [0.9999897, 0.999996]])

    def test_mag_dist_eps(self):
        pmf = valid.mag_dist_eps_pmf(self.matrix)
        self.aae(pmf, [[[0.88768, 0.673192, 0.972192],
                        [0.9874, 0.98393824, 0.9260596]],
                       [[0.9784078, 0.99751528, 0.8089168],
                        [0.84592498, 0.9988768, 0.976636]]])

    def test_lon_Lat(self):
        pmf = valid.lon_lat_pmf(self.matrix)
        self.aae(pmf, [[0.9991665, 0.9999943],
                       [0.9999982, 0.9999268]])

    def test_mag_lon_lat(self):
        pmf = valid.mag_lon_lat_pmf(self.matrix)
        self.aae(pmf, [[[0.89146822, 0.9836056],
                        [0.9993916, 0.98589012]],
                       [[0.99232001, 0.99965328],
                        [0.99700079, 0.99480979]]])

    def test_mean(self):
        # for doc purposes: the mean of PMFs is not the PMF of the mean
        numpy.random.seed(42)
        matrix = numpy.random.random(self.matrix.shape)
        pmf1 = valid.mag_pmf(self.matrix)
        pmf2 = valid.mag_pmf(matrix)
        mean = (matrix + self.matrix) / 2
        numpy.testing.assert_allclose(
            (pmf1 + pmf2) / 2, [1, 1])
        numpy.testing.assert_allclose(
            valid.mag_pmf(mean), [0.99999944, 0.99999999])


@pytest.mark.parametrize('job_ini', ['job_sampling.ini', 'job.ini'])
def test_single_source(job_ini):
    job_ini = os.path.join(DATA_PATH, 'data', 'disagg', job_ini)
    inp = read_input(job_ini)
    oq = inp.oq
    edges_shapedic = disagg.get_edges_shapedic(oq, inp.sitecol)
    srcid, std4D, rates4D, rates2D = disagg.disagg_source(
        inp.groups, inp.sitecol, inp.full_lt, edges_shapedic,
        oq, {'PGA': .1})
    # rates5D has shape (Ma, D, E, M, P), rates2D shape (M, L1)
    print(srcid)
    print(rates4D.sum(axis=(1, 2)))
    print(rates2D)
