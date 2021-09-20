
import os
import numpy as np
import unittest

from openquake.hazardlib import const
from openquake.hazardlib.imt import SA
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.projects.acme_2019 import AlAtikSigmaModel
from openquake.hazardlib.gsim.yenier_atkinson_2015 import get_sof_adjustment


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'projects')


class AlAtikSigmaModelTest(unittest.TestCase):

    def test01(self):
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='BindiEtAl2014Rjb',
                               kappa_file=filename,
                               kappa_val='high')
        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        rup.rjb = np.array([1., 10., 30., 70.])
        rup.vs30 = sites.vs30
        imt = SA(0.1)
        stdt = [const.StdDev.TOTAL]
        mean_expected, stds_expected = gmm.get_mean_and_stddevs(
            sites, rup, rup, imt, stdt)

    def test02(self):
        # checks if gmpe is always being evaluated at vs30=760
        # see HID 2.6.2
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='YenierAtkinson2015ACME2019',
                               kappa_file=filename,
                               kappa_val='high')
        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        rup.rjb = np.array([1., 10., 30., 70.])
        rup.rrup = np.array([1., 10., 30., 70.])
        rup.vs30 = sites.vs30
        imt = SA(0.1)
        stdt = [const.StdDev.TOTAL]
        mean_760, _ = gmm.get_mean_and_stddevs(sites, rup, rup, imt, stdt)

        sites2 = Dummy.get_site_collection(4, vs30=1500.)
        rup.vs30 = sites2.vs30
        mean_1500, _ = gmm.get_mean_and_stddevs(sites2, rup, rup, imt, stdt)

        self.assertAlmostEqual(mean_760[-1], mean_1500[-1], 4)


class GetSoFTestCase(unittest.TestCase):
    MSG = 'Wrong style-of-faulting coefficient'

    def test_short_period(self):
        # Normal
        rake = -90
        period = 0.01
        expected = 0.8401
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 1.0612
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 0.8843
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)

    def test_long_period(self):
        # Normal
        rake = -90
        period = 2.0
        expected = 0.9775
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 0.9882
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 1.0289
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
