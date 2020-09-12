# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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

"""
Module exports :class:`SungAbrahamson2020`
"""

import os
import h5py
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.bayless_abrahamson_2018 import \
        BaylessAbrahamson2018


class SungAbrahamson2020(BaylessAbrahamson2018):
    """
    Implements the Sung and Abrahamson (2020) model for France based on the
    Bayliss and Abrahamson (2018) GMM.
    """

    #: Supported standard deviation types
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    def _get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        # Get the necessary set of coefficients
        C = self.COEFFS[imt]
        mean = (self._magnitude_scaling(C, rup) +
                self._path_scaling(C, rup, dists) +
                self._ztor_scaling(C, rup) +
                self._site_response(C, sites.vs30, imt))

        # Get standard deviations
        stddevs = self._get_stddevs(C, rup, stddev_types, sites.vs30)
        return mean, stddevs

    def _magnitude_scaling(self, C, rup):
        """ Compute the magnitude scaling term """
        t1 = C['c1']
        t2 = C['c2'] * (rup.mag - 6.)
        tmp = np.log(1.0 + np.exp(C['cn']*(C['cM']-rup.mag)))
        t3 = C['c3'] * tmp
        #t3 = (C['c2'] - C['c3'])/C['cn'] * tmp
        return t1 + t2 + t3

    def _site_response(self, C, vs30, imt):
        """ Compute the site response term """
        # Linear term
        tmp = np.minimum(vs30, 1000.)
        fsl = C['c8'] * np.log(tmp / 1000.)
        return fsl

    def _get_stddevs(self, C, rup, stddev_types, vs30):
        """
        Compute the standard deviations
        """
        # Collect the requested stds
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma = C['tot']
                stddevs.append(np.ones_like(vs30) * sigma)
            elif stddev_type == const.StdDev.INTRA_EVENT:
                sigma = C['phi']
                stddevs.append(np.ones_like(vs30) * sigma)
            elif stddev_type == const.StdDev.INTER_EVENT:
                sigma = C['tau']
                stddevs.append(np.ones_like(vs30) * sigma)
        return stddevs


    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot   tau   phi   site_sd record_sd
f_1.0 -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 1.025 0.6   0.805 0.569 0.523
f_5.0 -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.94  0.439 0.78  0.509 0.53
""")


class SungAbrahamson2020NonErgodic(SungAbrahamson2020):
    """
    Modification of Sung and Abrahamson (2020) with non ergodic adjustments.
    """

    REQUIRES_DISTANCES = {'rrup', 'closest_pnts'}

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.adjustment_file = kwargs.get("adjustment_file", None)
        self.rlz_id = kwargs.get("rlz_id", "mean")
        msg = 'Adjustment file not found'
        assert os.path.exists(self.adjustment_file), msg

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # Original coefficients
        C = self.COEFFS[imt]

        # Results of the ergodic model
        mean, stddevs = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)

        # Checking that we use only one site (for the time being)
        try:
            assert len(sites.sites) == 1
        except:
            assert len(sites) == 1

        # Read info from the hdf5 file
        fcoeff = h5py.File(self.adjustment_file, 'r')
        dat = fcoeff['init'][:]
        fcoeff.close()

        # Find the closest node of the mesh to the rupture
        ste = dists.closest_pnts[0]
        lonn = 'xxx'
        idx = np.argmin(((dat[lonn] - ste[0])**2 +
                         (dat['lat'] - ste[1])**2)**0.5)

        # Add the non-ergodic anelastic term
        if self.rlz_id == 'mean':
            mean += dat['mea'][idx]
        else:
            mean += dat['rlz'][idx][self.rlz_id]

        if (abs(dat[lonn][idx] - ste[0]) > 0.22 or
                abs(dat['lat'][idx] - ste[1]) > 0.22):
            print('   Point mesh:', dat[lonn][idx], dat['lat'][idx])
            print('Point rupture:', ste[0], ste[1])
            print('      Diff lo:', abs(dat[lonn][idx] - ste[0]))
            print('      Diff la:', abs(dat['lat'][idx] - ste[1]))
            raise ValueError('')

        return mean, stddevs

    # The Coefficients used here are the same of the ergodic model BUT the
    # standard deviations which are based on information Karen sent on
    # Sept 4th.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot      tau
f_1.0 -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 0.868 0.476
f_5.0 -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.746 0.337
""")
