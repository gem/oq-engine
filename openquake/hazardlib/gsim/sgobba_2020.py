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
import re
import copy
import numpy as np
import pandas as pd
from scipy.constants import g as gravity_acc
from scipy.spatial import cKDTree
from openquake.hazardlib.geo import Point, Polygon
from openquake.hazardlib import const
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

# From http://www.csgnetwork.com/degreelenllavcalc.html
LEN_1_DEG_LAT_AT_43pt5 = 111.10245
LEN_1_DEG_LON_AT_43pt5 = 80.87665

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sgobba_2020')

REGIONS = {'1': [[13.37, 42.13], [13.60, 42.24], [13.48, 42.51], [13.19, 42.36]],
           '4': [[13.26, 42.41], [13.43, 42.49], [13.27, 43.02], [12.96, 42.86]],
           '5': [[13.03, 42.90], [13.21, 42.99], [13.10, 43.13], [12.90, 43.06]]}


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
                 site=False, **kwargs):
        super().__init__(event_id=event_id,
                         directionality=directionality,
                         cluster=cluster,
                         **kwargs)
        self.event_id = event_id
        self.directionality = directionality
        self.cluster = cluster
        self.site = site

        # Reading between-event std
        self.be = 0.0
        self.be_std = 0.0

        if event_id is not None:
            fname = os.path.join(DATA_FOLDER, 'event.csv')
            df = pd.read_csv(fname, sep=';', index_col='id',
                             dtype={'id': 'string'})
            self.df = df
            assert event_id in df.index.values

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Eq.1 - page 2
        """

        # Get site indexes. They are used for the site correction and the
        # cluster (path) correction
        if self.cluster != 0 or self.event_id is not None:

            label = "dBe_{:s}".format(imt.__str__())
            self.be = self.df.loc[self.event_id][label]
            # TODO
            # self.be_std = self.df.loc[self.event_id]['be_std']

            # Load the coordinate of the grid
            fname = os.path.join(DATA_FOLDER, 'grid.csv')
            coo = np.fliplr(np.loadtxt(fname, delimiter=";"))

            # Create a spatial index
            kdt = cKDTree(coo)
            tmp = [[s.location.longitude, s.location.latitude] for s in sites]
            dsts, self.idxs = kdt.query(np.array(tmp))

        # Ergodic coeffs
        C = self.COEFFS[imt]

        # Site correction
        sc = 0
        if self.site:
            sc = self._get_site_correction(sites.vs30.shape, imt)

        # Get mean
        mean = (C['a'] + self._get_magnitude_term(C, rup.mag) +
                self._get_distance_term(C, rup.mag, dists) +
                sc +
                self._get_cluster_correction(C, sites, rup, imt) +
                self.be)

        # To natural logarithm and fraction of g
        mean = np.log(10.0**mean/(gravity_acc*100))

        # Get stds
        stds = []

        return mean, stds

    def _get_site_correction(self, shape, imt):
        """
        Get site correction
        """
        correction = np.zeros_like(shape)

        # Cluster coefficients
        fname = os.path.join(DATA_FOLDER, "S_model.csv")
        data = np.loadtxt(fname, delimiter=",")

        # Compute the coefficients
        correction = np.zeros(shape)
        per = 0
        if re.search('SA', imt.__str__()):
            per = imt.period
        for idx in np.unique(self.idxs):
            tmp = data[int(idx)]
            correction[self.idxs == idx] = np.interp(per, self.PERIODS,
                                                     tmp[0:6])
        return correction

    def _get_cluster_correction(self, C, sites, rup, imt):
        """
        Get cluster correction. The use can specify various options through
        the cluster parameter. The available options are:
        - self.cluster = None
            In this case the code finds the most appropriate correction using
            the rupture position
        - self.cluster = 0
            No cluster correction
        - self.cluser = 1 or 4 or 5
            The code uses the correction for the given cluster
        """
        shape = sites.vs30.shape
        correction = np.zeros_like(shape)
        cluster = copy.copy(self.cluster)

        # No cluster correction
        if cluster is None:
            cluster = 0
            midp = rup.surface.get_middle_point()
            mesh = Mesh(np.array([midp.longitude]), np.array([midp.latitude]))

            for key in self.REGIONS:
                coo = np.array(REGIONS[key])
                pnts = [Point(lo, la) for lo, la in zip(coo[:, 0], coo[:, 1])]
                poly = Polygon(pnts)
                within = poly.intersects(mesh)
                if all(within):
                    cluster = int(key)
                    break

        if cluster == 0:
            return correction
        else:
            # Cluster coefficients
            fname = 'P_model_cluster{:d}.csv'.format(cluster)
            fname = os.path.join(DATA_FOLDER, fname)
            data = np.loadtxt(fname, delimiter=",", skiprows=1)

            # Compute the coefficients
            correction = np.zeros(shape)
            per = 0
            if re.search('SA', imt.__str__()):
                per = imt.period

            # NOTE: Checked for a few cases that the correction coefficients
            #       are correct
            for idx in np.unique(self.idxs):
                tmp = data[int(idx)]
                correction[self.idxs == idx] = np.interp(per, self.PERIODS,
                                                         tmp[0:6])
            # Adding L2L correction
            label = "dL2L_cluster{:d}".format(cluster)
            correction += C[label]

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

    PERIODS = np.array([0, 0.2, 0.5, 1.0, 2.0])

    # PGA coefficients from the paper 
#    COEFFS = CoeffsTable(sa_damping=5., table="""\
#     IMT       a      b1      b2s      c1       c2         c3    mref    taue  phis2s  phis2sref  taul2l  phip2p    sig0   sig0d
#     pga  2.9118  0.5450  0.1925  0.1809  -1.4588  -5.766e-3  3.8128  0.1527  0.2656     0.2011  0.0592  0.0970  0.2103  0.1585
#    """)

    COEFFS = CoeffsTable(sa_damping=5., table="""\
IMT a           b1          b2          c1          c2           c3           mref        sigma        dL2L_cluster1 dL2L_cluster4 dL2L_cluster5 tau_ev
PGA 2.921783    0.549352523 0.195787601 0.182324349 -1.56833817  -0.002770723 3.812781674 0.373287155 -0.014400196 -0.014100668 -0.081491221 0.1547
0.2 3.233717346 0.718110436 0.330819512 0.101391376 -1.474990811 -0.002359447 3.520852986 0.375753297 -0.029531349 -0.024299575 -0.077976198 0.1423
0.5 3.160502172 0.838494387 0.466787812 0.10572309  -1.480563287  0.0         4.871941075 0.336027705  0.00929098  -0.009953723 -0.008281007 0.1181
1   2.582278462 0.859113118 0.519131261 0.146088352 -1.280191184  0.0         5.425551993 0.324958646  0.000737173 -0.001235782  0.000181351 0.1242
2   1.887921687 0.727248116 0.473629771 0.244695133 -1.198169527  0.0         5.268965089 0.316058351  5.61e-15    -1.18e-14     9.32e-15    0.1277
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
