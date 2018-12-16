# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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

import numpy

from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib.correlation import JB2009CorrelationModel, \
                                            HM2018CorrelationModel
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo import Point

aaae = numpy.testing.assert_array_almost_equal


class JB2009CorrelationMatrixTestCase(unittest.TestCase):
    SITECOL = SiteCollection([Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -40.1), 1, 1, 1),
                              Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -39.9), 1, 1, 1)])

    def test_no_clustering(self):
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        imt = SA(period=0.1, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,          0.03823366, 1,          0.03823366],
                     [0.03823366, 1,          0.03823366, 0.00146181],
                     [1,          0.03823366, 1,          0.03823366],
                     [0.03823366, 0.00146181, 0.03823366, 1]])

        imt = SA(period=0.95, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,          0.26107857, 1,          0.26107857],
                     [0.26107857, 1,          0.26107857, 0.06816202],
                     [1,          0.26107857, 1,          0.26107857],
                     [0.26107857, 0.06816202, 0.26107857, 1]])

    def test_clustered(self):
        cormo = JB2009CorrelationModel(vs30_clustering=True)
        imt = SA(period=0.001, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,          0.44046654, 1,          0.44046654],
                     [0.44046654, 1,          0.44046654, 0.19401077],
                     [1,          0.44046654, 1,          0.44046654],
                     [0.44046654, 0.19401077, 0.44046654, 1]])

        imt = SA(period=0.5, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,          0.36612758, 1,          0.36612758],
                     [0.36612758, 1,          0.36612758, 0.1340494],
                     [1,          0.36612758, 1,          0.36612758],
                     [0.36612758, 0.1340494, 0.36612758, 1]])

    def test_period_one_and_above(self):
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        cormo2 = JB2009CorrelationModel(vs30_clustering=True)
        imt = SA(period=1.0, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,         0.2730787, 1,          0.2730787],
                     [0.2730787, 1,          0.2730787, 0.07457198],
                     [1,         0.2730787, 1,          0.2730787],
                     [0.2730787, 0.07457198, 0.2730787, 1]])
        corma2 = cormo2._get_correlation_matrix(self.SITECOL, imt)
        self.assertTrue((corma == corma2).all())

        imt = SA(period=10.0, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1,          0.56813402, 1,          0.56813402],
                     [0.56813402, 1,          0.56813402, 0.32277627],
                     [1,          0.56813402, 1,          0.56813402],
                     [0.56813402, 0.32277627, 0.56813402, 1]])
        corma2 = cormo2._get_correlation_matrix(self.SITECOL, imt)
        self.assertTrue((corma == corma2).all())

    def test_pga(self):
        sa = SA(period=1e-50, damping=5)
        pga = PGA()

        cormo = JB2009CorrelationModel(vs30_clustering=False)
        corma = cormo._get_correlation_matrix(self.SITECOL, sa)
        corma2 = cormo._get_correlation_matrix(self.SITECOL, pga)
        self.assertTrue((corma == corma2).all())

        cormo = JB2009CorrelationModel(vs30_clustering=True)
        corma = cormo._get_correlation_matrix(self.SITECOL, sa)
        corma2 = cormo._get_correlation_matrix(self.SITECOL, pga)
        self.assertTrue((corma == corma2).all())


class JB2009LowerTriangleCorrelationMatrixTestCase(unittest.TestCase):
    SITECOL = SiteCollection([Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -40.1), 1, 1, 1),
                              Site(Point(2, -39.9), 1, 1, 1)])

    def test(self):
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        lt = cormo.get_lower_triangle_correlation_matrix(self.SITECOL, PGA())
        aaae(lt, [[1.0,            0.0,            0.0],
                  [1.97514806e-02, 9.99804920e-01, 0.0],
                  [1.97514806e-02, 5.42206860e-20, 9.99804920e-01]])


class JB2009ApplyCorrelationTestCase(unittest.TestCase):
    SITECOL = SiteCollection([Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -40.1), 1, 1, 1),
                              Site(Point(2, -39.9), 1, 1, 1)])

    def test(self):
        numpy.random.seed(13)
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        intra_residuals_sampled = numpy.random.normal(size=(3, 100000))
        intra_residuals_correlated = cormo.apply_correlation(
            self.SITECOL, PGA(), intra_residuals_sampled
        )
        inferred_corrcoef = numpy.corrcoef(intra_residuals_correlated)
        mean = intra_residuals_correlated.mean()
        std = intra_residuals_correlated.std()
        self.assertAlmostEqual(mean, 0, delta=0.002)
        self.assertAlmostEqual(std, 1, delta=0.002)

        actual_corrcoef = cormo._get_correlation_matrix(self.SITECOL, PGA())
        numpy.testing.assert_almost_equal(inferred_corrcoef, actual_corrcoef,
                                          decimal=2)


class HM2018CorrelationMatrixTestCase(unittest.TestCase):
    SITECOL = SiteCollection([Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -40.1), 1, 1, 1),
                              Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -39.9), 1, 1, 1)])

    def test_correlation_no_uncertainty(self):
        cormo = HM2018CorrelationModel(uncertainty_multiplier=0)

        imt = SA(period=0.1, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL,imt)
        aaae(corma, [[1.0000000,    0.3981537,    1.0000000,    0.3981537,],
                     [0.3981537,    1.0000000,    0.3981537,    0.2596809,],
                     [1.0000000,    0.3981537,    1.0000000,    0.3981537,],
                     [0.3981537,    0.2596809,    0.3981537,    1.0000000,]])

        imt = SA(period=0.5, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1.0000000,    0.3809173,    1.0000000,    0.3809173,],
                     [0.3809173,    1.0000000,    0.3809173,    0.2433886,],
                     [1.0000000,    0.3809173,    1.0000000,    0.3809173,],
                     [0.3809173,    0.2433886,    0.3809173,    1.0000000,]])

        imt = SA(period=1, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1.0000000,    0.3906193,    1.0000000,    0.3906193,],
                     [0.3906193,    1.0000000,    0.3906193,    0.2525181,],
                     [1.0000000,    0.3906193,    1.0000000,    0.3906193,],
                     [0.3906193,    0.2525181,    0.3906193,    1.0000000,]])

        imt = SA(period=2, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1.0000000,    0.4011851,    1.0000000,    0.4011851,],
                     [0.4011851,    1.0000000,    0.4011851,    0.2625807,],
                     [1.0000000,    0.4011851,    1.0000000,    0.4011851,],
                     [0.4011851,    0.2625807,    0.4011851,    1.0000000,]])

        imt = SA(period=4, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1.0000000,    0.3522765,    1.0000000,    0.3522765,],
                     [0.3522765,    1.0000000,    0.3522765,    0.2170695,],
                     [1.0000000,    0.3522765,    1.0000000,    0.3522765,],
                     [0.3522765,    0.2170695,    0.3522765,    1.0000000,]])

        imt = SA(period=6, damping=5)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(corma, [[1.0000000,    0.3159779,    1.0000000,    0.3159779,],
                     [0.3159779,    1.0000000,    0.3159779,    0.1851206,],
                     [1.0000000,    0.3159779,    1.0000000,    0.3159779,],
                     [0.3159779,    0.1851206,    0.3159779,    1.0000000,]])

    def test_correlation_small_uncertainty(self):
        imt = SA(period=1.5, damping=5)

        cormo = HM2018CorrelationModel(uncertainty_multiplier=0)
        corma = cormo._get_correlation_matrix(self.SITECOL, imt)

        cormo2 = HM2018CorrelationModel(uncertainty_multiplier=1E-30)
        corma2 = cormo2._get_correlation_matrix(self.SITECOL, imt)
        self.assertTrue((corma == corma2).all())

    def test_pga_no_uncertainty(self):
        sa = SA(period=1e-50, damping=5)
        pga = PGA()

        cormo = HM2018CorrelationModel(uncertainty_multiplier=0)
        
        corma = cormo._get_correlation_matrix(self.SITECOL, sa)
        corma2 = cormo._get_correlation_matrix(self.SITECOL, pga)
        self.assertTrue((corma == corma2).all())

    def test_correlation_with_uncertainty(self):
        Nsim = 100000
        cormo = HM2018CorrelationModel(uncertainty_multiplier=1)
        imt = SA(period=3, damping=5)
        
        corma_3d = numpy.zeros((len(self.SITECOL), len(self.SITECOL), Nsim))

        # For each simulation, construct a new correlation matrix
        for isim in range(0, Nsim):
            corma_3d[0:, 0:, isim] = \
                cormo._get_correlation_matrix(self.SITECOL, imt)

        # Mean and Coefficient of Variation (COV) of correlation matrix
        MEANcorMa = corma_3d.mean(2)
        COVcorma = numpy.divide(corma_3d.std(2), MEANcorMa)

        aaae(MEANcorMa,[[1.0000000,    0.3766436,    1.0000000,    0.3766436,],
                     [0.3766436,    1.0000000,    0.3766436,    0.2534904,],
                     [1.0000000,    0.3766436,    1.0000000,    0.3766436,],
                     [0.3766436,    0.2534904,    0.3766436,    1.00000,]], 2)

        aaae(COVcorma,[[0.0000000,    0.4102512,    0.0000000,    0.4102512,],
                     [0.4102512,    0.0000000,    0.4102512,    0.5636907,],
                     [0.0000000,    0.4102512,    0.0000000,    0.4102512,],
                     [0.4102512,    0.5636907,    0.4102512,    0.00000,]], 2)


class HM2018ApplyCorrelationTestCase(unittest.TestCase):
    SITECOL = SiteCollection([Site(Point(2, -40), 1, 1, 1),
                              Site(Point(2, -40.1), 1, 1, 1),
                              Site(Point(2, -39.95), 1, 1, 1)])

    def test_no_uncertainty(self):
        numpy.random.seed(1)
        Nsim = 100000
        imt = SA(period=2.0, damping=5)
        stddev_intra = numpy.array([0.5, 0.6, 0.7])
        cormo = HM2018CorrelationModel(uncertainty_multiplier=0)

        intra_residuals_sampled = numpy.random.multivariate_normal(
            numpy.zeros(3), numpy.diag(stddev_intra ** 2), Nsim).\
            transpose(1, 0)

        intra_residuals_correlated = cormo.apply_correlation(
            self.SITECOL, imt, intra_residuals_sampled, stddev_intra)

        inferred_corrcoef = numpy.corrcoef(intra_residuals_correlated)
        mean = intra_residuals_correlated.mean(1)
        std = intra_residuals_correlated.std(1)

        aaae(numpy.squeeze(numpy.asarray(mean)), numpy.zeros(3), 2)
        aaae(numpy.squeeze(numpy.asarray(std)), stddev_intra, 2)

        actual_corrcoef = cormo._get_correlation_matrix(self.SITECOL, imt)
        aaae(inferred_corrcoef, actual_corrcoef, 2)

    def test_with_uncertainty(self):
        numpy.random.seed(1)
        Nsim = 100000
        imt = SA(period=3.0, damping=5)
        stddev_intra = numpy.array([0.3, 0.6, 0.9])
        cormo = HM2018CorrelationModel(uncertainty_multiplier=1)

        intra_residuals_sampled = numpy.random.multivariate_normal(
            numpy.zeros(3), numpy.diag(stddev_intra ** 2), Nsim).\
            transpose(1, 0)

        intra_residuals_correlated = cormo.apply_correlation(
            self.SITECOL, imt, intra_residuals_sampled, stddev_intra)

        inferred_corrcoef = numpy.corrcoef(intra_residuals_correlated)
        mean = intra_residuals_correlated.mean(1)
        std = intra_residuals_correlated.std(1)

        aaae(numpy.squeeze(numpy.asarray(mean)), numpy.zeros(3), 2)
        aaae(numpy.squeeze(numpy.asarray(std)), stddev_intra, 2)
        aaae(inferred_corrcoef,
             [[1.        , 0.3807, 0.5066],
              [0.3807, 1.        , 0.3075],
              [0.5066, 0.3075, 1.        ]], 2)
