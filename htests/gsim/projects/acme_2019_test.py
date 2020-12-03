
import os
import numpy as np
import unittest

from openquake.hazardlib import const
from openquake.hazardlib.imt import SA
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.projects.acme_2019 import AlAtikSigmaModel
from openquake.hazardlib.gsim.projects.acme_2019 import get_sof_adjustment


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'projects')


class AlAtikSigmaModelTest(unittest.TestCase):

    def test01(self):
        filename = os.path.join(DATA_PATH, 'kappa.txt')
        gmm = AlAtikSigmaModel(gmpe_name='BindiEtAl2014Rjb',
                               kappa_file=filename,
                               kappa_val='high')
        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.rjb = np.array([1., 10., 30., 70.])
        imt = SA(0.1)
        stdt = [const.StdDev.TOTAL]
        mean_expected, stds_expected = gmm.get_mean_and_stddevs(sites, rup,
                                                                dists, imt,
                                                                stdt)


class GetSoFTestCase(unittest.TestCase):
    MSG = 'Wrong style-of-faulting coefficient'

    def test_short_period(self):
        # Normal
        rake = -90
        period = 0.01
        expected = 0.8136
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 1.0277
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 0.8564
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)

    def test_long_period(self):
        # Normal
        rake = -90
        period = 2.0
        expected = 0.9832
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # Reverse
        rake = 90
        expected = 0.9940
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
        # SS
        rake = 0
        expected = 1.0350
        computed = get_sof_adjustment(rake, SA(period))
        self.assertAlmostEqual(computed, expected, 4, msg=self.MSG)
