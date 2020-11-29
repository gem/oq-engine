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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.gsim.sgobba_2020` implements
:class:`~openquake.hazardlib.gsim.sgobba_2020.SgobbaEtAl2020`
"""

import os
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from openquake.hazardlib.geo import Point, Polygon
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable

# From http://www.csgnetwork.com/degreelenllavcalc.html
LEN_1_DEG_LAT_AT_43pt5 = 111.10245
LEN_1_DEG_LON_AT_43pt5 = 80.87665

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sgobba_2020')


class SgobbaEtAl2020(GMPE):
    """
    Implements the GMM proposed by Sgobba et al. (2020).

    :param event_id:
        A string identifying an event amongst the ones comprised in the
        list available in the file `event.csv`
    :param directionality:
        A boolean
    :param cluster:
        If set to 'None' no cluster correction applied. If 0 the OQ Engine
        finds the corresponding cluster using the rupture epicentral
        location.  Otherwise, if an integer ID is provided, that
        corresponds to the cluster id (available cluster indexes are 1, 4
        and 5)
    """

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    }

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb
    REQUIRES_DISTANCES = {'rjb'}

    def __init__(self, event_id=None, directionality=False, cluster=None,
                 **kwargs):
        super().__init__(event_id=event_id,
                         directionality=directionality,
                         cluster=cluster,
                         **kwargs)
        self.event_id = event_id
        self.directionality = directionality
        self.cluster = cluster

        # Reading between-event std
        self.be = 0.0
        self.be_std = 0.0
        if event_id is not None:
            fname = os.path.join(DATA_FOLDER, 'event.csv')
            df = pd.read_csv(fname, sep=';', index_col="id",
                             dtype={'id': 'string'})
            self.be = df.loc[event_id]['Be']
            self.be_std = df.loc[event_id]['be_std']

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Eq.1 - page 2
        """

        # Get site indexes
        if self.cluster is not None or self.event_id is not None:

            # Load the coordinate of the grid
            fname = os.path.join(DATA_FOLDER, 'grid.csv')
            coo = np.fliplr(np.loadtxt(fname, delimiter=";"))

            # Create a spatial index
            kdt = cKDTree(coo)
            tmp = [[s.location.longitude, s.location.latitude] for s in sites]
            dsts, self.idxs = kdt.query(np.array(tmp))

        # Ergodic coeffs
        C = self.COEFFS[imt]

        # Get mean
        mean = (self._get_magnitude_term(C, rup.mag) +
                self._get_distance_term(C, rup.mag, dists) +
                self._get_site_correction(sites.vs30.shape) +
                self._get_cluster_correction(sites.vs30.shape, rup) +
                self.be)

        # To natural logarithm 
        mean = np.log(10.0**mean)

        # Get stds
        stds = []

        return mean, stds

    def _get_site_correction(self, shape):
        """
        Get cluster correction
        """
        correction = np.zeros_like(shape)

        # Cluster coefficients
        fname = os.path.join(DATA_FOLDER, "S_model.csv")
        data = np.loadtxt(fname, delimiter=",")

        # Compute the coefficients
        correction = np.zeros(shape)
        for idx in np.unique(self.idxs):
            tmp = data[int(idx)]
            correction[self.idxs == idx] = np.interp(0, self.PERIODS,
                                                     tmp[0:6])
        return correction

    def _get_cluster_correction(self, shape, rup):
        """
        Get cluster correction
        """
        correction = np.zeros_like(shape)
        if self.cluster is None:
            return correction
        elif self.cluster == 0:
            # TODO complete with udpated polygons
            midp = rup.surface.get_middle_point()
            cluid = self._get_cluster_region(midp)
            for key in self.REGIONS:
                tmp = np.reshape(np.array(self.REGIONS[key]), (-1, 2))
                import matplotlib.pyplot as plt
                plt.plot(tmp[:, 0], tmp[:, 1])
                plt.title(key)
                plt.show()
                # poly = Polygon([Point(p[0], p[1]) for p in tmp])
        else:

            # Cluster coefficients
            fname = 'P_model_cluster{:d}.csv'.format(self.cluster)
            fname = os.path.join(DATA_FOLDER, fname)
            data = np.loadtxt(fname, delimiter=",")

            # Compute the coefficients
            correction = np.zeros(shape)
            for idx in np.unique(self.idxs):
                tmp = data[int(idx)]
                correction[self.idxs == idx] = np.interp(0, self.PERIODS,
                                                         tmp[0:6])
            print('correction', correction)
        return correction

    def _get_magnitude_term(self, C, mag):
        """
        Eq.2 - page 3
        """
        if mag <= self.consts['Mh']:
            return C['b1']*(mag-self.consts['Mh'])
        else:
            return C['b2']*(mag-self.consts['Mh'])

    def _get_distance_term(self, C, mag, dists):
        """
        Eq.3 - page 3
        """
        term1 = C['c1']*(mag-C['mref']) + C['c2']
        tmp = np.sqrt(dists.rjb**2+self.consts['PseudoDepth']**2)
        term2 = np.log10(tmp/self.consts['Rref'])
        term3 = C['c3']*(tmp-self.consts['Rref'])
        return term1 * term2 + term3

    def _get_cluster_region(self, hypo):
        for key in self.REGIONS:
            pass

    PERIODS = np.array([0, 0.1, 0.2, 0.5, 1.0, 2.0])

    COEFFS = CoeffsTable(sa_damping=5., table="""\
     IMT       a      b1      b2      c1       c2         c3    mref    taue  phis2s  phis2sref  taul2l  phip2p    sig0   sig0d
     pga  2.9118  0.5450  0.1925  0.1809  -1.4588  -5.766e-3  3.8128  0.1527  0.2656     0.2011  0.0592  0.0970  0.2103  0.1585
    """)

    consts = {'Mh': 5.0,
              'Rref': 1.0,
              'PseudoDepth': 6.0}

    REGIONS = {'1': [13.37, 42.13, 14.94, 41.10, 15.23, 42.32, 13.26, 42.41,
                     13.03, 42.90, 14.81, 41.80],
               '4': [13.19, 42.36, 14.83, 41.17, 15.13, 42.38, 12.96, 42.86,
                     12.90, 43.06, 14.73, 41.85],
               '5': [13.37, 42.13, 14.94, 41.10, 15.23, 42.32, 13.26, 42.41,
                     13.03, 42.90, 14.81, 41.80]}
