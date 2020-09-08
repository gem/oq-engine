# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
import numpy as np
import unittest
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, MMI
from openquake.hazardlib.gsim.base import registry
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE


class ModifiableGMPETest(unittest.TestCase):

    def setUp(self):
        # Set parameters
        self.sites = Dummy.get_site_collection(4, vs30=760.)
        self.rup = Dummy.get_rupture(mag=6.0)
        self.dists = DistancesContext()
        self.dists.rrup = np.array([1., 10., 30., 70.])
        self.dists.rjb = np.array([1., 10., 30., 70.])
        self.imt = PGA()

    def test_set_between_epsilon_raises_error(self):
        """ Check that error is raised for GMPEs with only total std """

        stds_types = [const.StdDev.TOTAL]
        gmm = ModifiableGMPE(gmpe={'Campbell2003': {}},
                             set_between_epsilon={'epsilon_tau': 0.5})
        with self.assertRaises(ValueError):
            _, _ = gmm.get_mean_and_stddevs(self.sites, self.rup, self.dists,
                                            self.imt, stds_types)

    def test_get_mean_std(self):
        """ Check calculation of mean and stds """

        stds_types = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                      const.StdDev.INTRA_EVENT]

        gmpe_name = 'AkkarEtAlRjb2014'
        gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                             set_between_epsilon={'epsilon_tau': 0.5})
        mean, stds = gmm.get_mean_and_stddevs(self.sites, self.rup, self.dists,
                                              self.imt, stds_types)

        gmpe = registry[gmpe_name]()
        emean, estds = gmpe.get_mean_and_stddevs(self.sites, self.rup,
                                                 self.dists,
                                                 self.imt, stds_types)
        idx = stds_types.index(const.StdDev.INTER_EVENT)
        exp_mean = emean + estds[idx] * 0.5

        # Check the computed mean + between event variability
        np.testing.assert_almost_equal(mean, exp_mean)

        # Check that the total std now corresponds to the within event
        # standard deviation
        np.testing.assert_almost_equal(stds[0], estds[2])


class ModifiableGMPETestSwissAmpl(unittest.TestCase):

    def setUp(self):
        # Set parameters
        self.sites = Dummy.get_site_collection(4, amplfactor=[-1.0, 1.5,
                                                           0.00, -1.99])
        self.rup = Dummy.get_rupture(mag=6.0, hypo_depth=10)
        self.dists = DistancesContext()
        self.dists.rhypo = np.array([1., 10., 30., 70.])
        self.dists.repi = np.array([1., 10., 30., 70.])
        self.imt = MMI()

    def test_get_mean_std(self):
        """ Check calculation of amplified mean"""

        for gmpe_name in ['ECOS2009', 'BindiEtAl2011RepiFixedH',
                          'BaumontEtAl2018High2210IAVGDC30n7',
                          'FaccioliCauzzi2006']:

            stds_types = [const.StdDev.TOTAL]
            gmm = ModifiableGMPE(gmpe={gmpe_name: {}},
                                 apply_swiss_amplification={})
            mean, stds = gmm.get_mean_and_stddevs(self.sites, self.rup,
                                                  self.dists, self.imt,
                                                  stds_types)

            gmpe = registry[gmpe_name]()
            emean, estds = gmpe.get_mean_and_stddevs(self.sites, self.rup,
                                                     self.dists,
                                                     self.imt, stds_types)

            exp_mean = emean + np.array([-1.00, 1.50, 0, -1.99])

            # Check the computed mean + amplification
            np.testing.assert_almost_equal(mean, exp_mean)
