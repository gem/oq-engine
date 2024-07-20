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

REGIONS = {
    '1': [[13.37, 42.13], [13.60, 42.24], [13.48, 42.51], [13.19, 42.36]],
    '4': [[13.26, 42.41], [13.43, 42.49], [13.27, 43.02], [12.96, 42.86]],
    '5': [[13.03, 42.90], [13.21, 42.99], [13.10, 43.13], [12.90, 43.06]]}

CONSTS = {'Mh': 5.0,
          'Rref': 1.0,
          'PseudoDepth': 6.0}


def _get_cluster_correction(dat, C, ctx, imt):
    """
    Get cluster correction. The use can specify various options through
    the cluster parameter. The available options are:
    - cluster = None
        In this case the code finds the most appropriate correction using
        the rupture position
    - cluster = 0
        No cluster correction
    - cluser = 1 or 4 or 5
        The code uses the correction for the given cluster
    """
    cluster = dat.cluster
    shape = ctx.sids.shape
    correction = np.zeros_like(shape)
    # st.dev.
    tau_L2L = np.zeros(shape)
    Bp_model = np.zeros(shape)
    phi_P2P = np.zeros(shape)

    # No cluster correction
    if cluster == 0:
        tau_L2L = C['tau_L2L']
        phi_P2P = C['phi_P2P']
        return correction, tau_L2L, Bp_model, phi_P2P
    # the code finds the most appropriate correction
    if cluster is None:
        mesh = Mesh(np.array([ctx.hypo_lon]), np.array([ctx.hypo_lat]))
        # midp = ctx.surface.get_middle_point()
        # mesh = Mesh(np.array([midp.longitude]),np.array([midp.latitude]))

        for key in REGIONS:
            coo = np.array(REGIONS[key])
            pnts = [Point(lo, la) for lo, la in zip(coo[:, 0], coo[:, 1])]
            poly = Polygon(pnts)
            within = poly.intersects(mesh)
            if within.all():
                cluster = int(key)
                break
    # if OUT clusters do not apply corrections
    if cluster is None:
        tau_L2L = C['tau_L2L']
        phi_P2P = C['phi_P2P']
        return correction, tau_L2L, Bp_model, phi_P2P
    else:
        # if IN clusters apply corrections
        # Cluster coefficients
        fname = 'P_model_cluster{:d}.csv'.format(cluster)
        fname = os.path.join(DATA_FOLDER, fname)
        data = np.loadtxt(fname, delimiter=",", skiprows=1)
        # for st.dev.
        fname2 = 'beta_dP2P_cluster{:d}.csv'.format(cluster)
        fname2 = os.path.join(DATA_FOLDER, fname2)
        data2 = np.loadtxt(fname2, delimiter=",", skiprows=1)
        # Compute the coefficients
        correction = np.zeros(shape)
        per = imt.period
        for idx in np.unique(dat.idxs):
            tmp = data[int(idx)]
            correction[dat.idxs == idx] = np.interp(
                per, dat.PERIODS, tmp[0:5])
        # Adding L2L correction
        label = "dL2L_cluster{:d}".format(cluster)
        correction += C[label]
        # compute st.dev.
        for idx in np.unique(dat.idxs):
            tmp2 = data2[int(idx)]
            Bp_model[dat.idxs == idx] = np.interp(per, dat.PERIODS, tmp2[0:5])
        return correction, tau_L2L, Bp_model, phi_P2P


def _get_distance_term(C, mag, ctx):
    """
    Eq.3 - page 3
    """
    term1 = C['c1'] * (mag - C['mref']) + C['c2']
    tmp = np.sqrt(ctx.rjb**2 + CONSTS['PseudoDepth']**2)
    term2 = np.log10(tmp / CONSTS['Rref'])
    term3 = C['c3'] * (tmp - CONSTS['Rref'])
    return term1 * term2 + term3


def _get_magnitude_term(C, mag):
    """
    Eq.2 - page 3
    """
    return np.where(mag <= CONSTS['Mh'],
                    C['b1'] * (mag - CONSTS['Mh']),
                    C['b2'] * (mag - CONSTS['Mh']))


def _get_site_correction(data, shape, imt):
    """
    Get site correction
    """
    correction = np.zeros_like(shape)
    # Compute the coefficients
    correction = np.zeros(shape)
    # stand.dev.
    Bs_model = np.zeros(shape)
    phi_S2Sref = np.zeros(shape)
    per = imt.period
    for idx in np.unique(data.idxs):
        tmp = data.Smodel[int(idx)]
        correction[data.idxs == idx] = np.interp(
            per, data.PERIODS, tmp[0:5])
        tmp2 = data.betaS2S[int(idx)]
        Bs_model[data.idxs == idx] = np.interp(
            per, data.PERIODS, tmp2[0:5])
    return correction, Bs_model, phi_S2Sref


class Data(object):
    """Helper class"""
    def __init__(self, smodel, cluster, periods, betaS2S, idxs):
        self.Smodel = smodel
        self.cluster = copy.copy(cluster)
        self.PERIODS = periods
        self.betaS2S = betaS2S
        self.idxs = idxs


# NB: the implementation here is HORRIBLE performance-wise,
# because it is using KDTree and pandas!
class SgobbaEtAl2020(GMPE):
    """
    Implements the GMM proposed by Sgobba et al. (2020).
    Warning:
    This GMM is not meant for national models where it would be too slow,
    it is meant for scenario calculations.

    :param event_id:
        A string identifying an event amongst the ones comprised in the
        list available in the file `event.csv`
    :param directionality:
        A boolean
    :param cluster:
        If set to 'None', the OQ Engine finds the corresponding cluster
        using the rupture epicentral location.
        If cluster=0, no cluster correction applied.
        Otherwise, if an integer ID is provided, that
        corresponds to the cluster id (available cluster indexes are 1, 4
        and 5), the corresponding correction id applied.
    """
    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are lon and lat
    REQUIRES_SITES_PARAMETERS = {'lon', 'lat'}

    #: Required rupture parameters is magnitude, hypo_lat, hypo_lon
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_lon', 'hypo_lat'}

    #: Required distance measure is Rjb
    REQUIRES_DISTANCES = {'rjb'}

    PERIODS = np.array([0, 0.2, 0.50251256281407, 1.0, 2.0])

    def __init__(self, event_id=None, directionality=False, cluster=None,
                 site=False, bedrock=False):
        self.event_id = event_id
        self.directionality = directionality
        self.cluster = cluster
        self.site = site
        self.bedrock = bedrock
        # Get site indexes. They are used for the site correction and the
        # cluster (path) correction
        # Load the coordinate of the grid
        fname = os.path.join(DATA_FOLDER, 'grid.csv')
        coo = np.fliplr(np.loadtxt(fname, delimiter=";"))
        self.kdt = cKDTree(coo)

        # Load the table with the between event coefficients
        if event_id is not None:
            self.event_id = event_id
            fname = os.path.join(DATA_FOLDER, 'event.csv')
            # Create dataframe with events
            df = pd.read_csv(fname, dtype={'id': str})
            df.set_index('id', inplace=True)
            self.df = df
            assert event_id in df.index.values
        # Site coefficients
        fname = os.path.join(DATA_FOLDER, "S_model.csv")
        self.Smodel = np.loadtxt(fname, delimiter=",", skiprows=1)
        fname = os.path.join(DATA_FOLDER, "beta_dS2S.csv")
        self.betaS2S = np.loadtxt(fname, delimiter=",", skiprows=1)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Eq.1 - page 2
        """
        for m, imt in enumerate(imts):
            # Ergodic coeffs
            C = self.COEFFS[imt]
            # between-event
            if self.event_id is not None:
                label = "dBe_{:s}".format(str(imt))
                self.be = self.df.loc[self.event_id][label]
                self.be_std = 0.0
            else:
                self.be_std = C['tau_ev']
                self.be = 0.0
            # Site correction
            points = np.array([ctx.lon, ctx.lat]).T  # shape (N, 2)
            _dsts, idxs = self.kdt.query(points)
            dat = Data(self.Smodel, self.cluster, self.PERIODS,
                       self.betaS2S, idxs)
            sc = 0
            phi_S2Sref = C['phi_S2S_ref']
            Bs_model = np.zeros(ctx.sids.shape)
            if self.site and self.bedrock is False:
                sc, Bs_model, phi_S2Sref = _get_site_correction(
                    dat, ctx.sids.shape, imt)

            cc, tau_L2L, Bp_model, phi_P2P = _get_cluster_correction(
                dat, C, ctx, imt)
            # Get mean
            mean[m] = (C['a'] + _get_magnitude_term(C, ctx.mag) +
                       _get_distance_term(C, ctx.mag, ctx) +
                       sc + cc + self.be)
            # To natural logarithm and fraction of g
            mean[m] = np.log(10.0**mean[m] / (gravity_acc*100))
            # Get stds
            std = np.sqrt(C['sigma_0'] ** 2 + self.be_std ** 2 + tau_L2L ** 2 +
                          Bs_model + phi_S2Sref ** 2 + Bp_model + phi_P2P ** 2)
            sig[m] = np.log(10.0 ** std)
            tau[m] = np.log(10.0 ** self.be_std)
            phi[m] = np.log(10.0 ** np.sqrt((std ** 2 - self.be_std ** 2)))

    COEFFS = CoeffsTable(sa_damping=5., table="""\
    IMT                a                   b1                  b2                   c1                   c2                    c3                     mref               tau_ev              tau_L2L               phi_S2S_ref   phi_S2S              phi_P2P             sigma_0            dL2L_cluster1          dL2L_cluster4         dL2L_cluster5
    pga               2.92178299969904    0.549352522898805   0.195787600661646    0.182324348626393    -1.56833817017883     -0.00277072348000775   3.81278167434967   0.148487352282019   0.0244729216674648    0.2011        0.249446934633114    0.129067143622624   0.194457660872416  -0.0144001959308384    -0.0141006684390188   -0.0814912207894038
    0.2               3.23371734550753    0.718110435825521   0.330819511910566    0.101391376086178    -1.47499081134392     -0.00235944669544279   3.52085298608413   0.142257128473462   0.0142903160948886    0.2049        0.25356556670542     0.108002263739343   0.211634711188527  -0.0295313493684611    -0.0242995747709838   -0.0779761977475732
    0.50251256281407  3.16050217205595    0.838494386998919   0.466787811642044    0.105723089676       -1.48056328666322      0                     4.87194107479204   0.118125529818761   0.0131546256192079    0.1419        0.230442366433058    0.0959080118602377  0.191012833298469   0.00929098048437728   -0.00995372305434456  -0.00828100722167989
    1                 2.58227846237728    0.85911311807545    0.519131261495525    0.146088352194266    -1.28019118368202      0                     5.42555199253122   0.124229747688977   2.39299038437967e-08  0.1153        0.212408309867869    0.118568732468557   0.176037658051544   0.000737173026444824  -0.00123578210338215   0.000181351036566464
    2                 1.88792168738756    0.727248116061721   0.47362977053987     0.244695132922949    -1.19816952711971      0                     5.26896508895249   0.127711124129548   8.69064652723658e-09  0.1078        0.189154038588083    0.119572905421336   0.183045950697286   5.60984632803441e-15  -1.18288330352055e-14  9.31778101896791e-15
    """)
