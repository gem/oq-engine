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

import os
import unittest
import numpy as np
import pandas as pd
from openquake.hazardlib import const, contexts
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.geo import Point
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.sgobba_2020 import SgobbaEtAl2020

# folder Verif Tables
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'SEA20')
# folder Residuals
DATA_FOLDER2 = os.path.join(
    os.path.dirname(__file__), '..', '..', 'gsim', 'sgobba_2020')


def get_ctx(subset_df):
    locs = []
    rjb = []
    for idx, row in subset_df.iterrows():
        locs.append(Point(row.lon_sites, row.lat_sites))
        rjb.append(row.dist_jb)
    sites = Dummy.get_site_collection(len(rjb), vs30=800., location=locs)
    rup = Dummy.get_rupture(
        mag=row.rup_mag, hypo_lat=row.lat_epi, hypo_lon=row.lon_epi)
    rup.rjb = rup.rrup = np.array(rjb)
    return contexts.full_context(sites, rup)


# legacy horrible implementation
def get_epicenters(df):
    epicenters = []
    for idx, row in df.iterrows():
        x = Point(row.lon_epi, row.lat_epi)
        if x not in epicenters:
            epicenters.append(x)
    return epicenters


def chk(gmm, tags, ctx, subset_df, sigma):
    periods = [PGA(), SA(period=0.2), SA(period=0.50251256281407),
               SA(period=1.0), SA(period=2.0)]
    stdt = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
            const.StdDev.INTRA_EVENT]
    # Compute and check results for the NON ergodic model
    for i in range(len(periods)):
        imt = periods[i]
        tag = tags[i]
        mean, stddevs = gmm.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        if sigma == "1":  # checking the Total stddev
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = stddevs[0]  # in ln
        elif sigma == "2":  # checking tau
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = stddevs[1]  # in ln
        elif sigma == "3":  # checking phi
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = stddevs[2]  # in ln
        else:  # checking the mean
            expected = subset_df[tag].to_numpy()  # Verif Table in g unit
            computed = np.exp(mean)  # in OQ are computed in g Units in ln
        np.testing.assert_allclose(computed, expected, rtol=1e-5)


def gen_data(df):
    df2 = pd.read_csv(os.path.join(DATA_FOLDER2, 'event.csv'),
                      dtype={'id': str})
    epicenters = get_epicenters(df)

    # For each event check Validation
    for i in range(len(epicenters)):
        LON = epicenters[i].x
        LAT = epicenters[i].y
        idx = np.where((df['lat_epi'] == LAT) & (df['lon_epi'] == LON))
        subset_df = df.loc[idx]
        flag_b = subset_df['flag_bedrock']
        if sum(flag_b) > 0:
            bedrock = [0, 1]
        else:
            bedrock = [0]
        for i in bedrock:
            idx = np.where((df['lat_epi'] == LAT) &
                           (df['lon_epi'] == LON) &
                           (df['flag_bedrock'] == i))
            subset_df = df.loc[idx]
            idx2 = np.where((df2['Ev_lat'] == LAT) & (df2['Ev_lon'] == LON))[0]
            if len(idx2) > 0:
                idx2 = idx2[0]
                ev_id = df2['id'][idx2]
            else:
                ev_id = None
            print('event_id: '+str(ev_id))
            print('flag_bedrock: '+str(i))
            ctx = get_ctx(subset_df)
            gmm = SgobbaEtAl2020(event_id=ev_id, site=True, bedrock=i > 0)
            yield gmm, ctx, subset_df


class Sgobba2020Test(unittest.TestCase):

    def test_ERGODIC(self):
        fname = 'ValidationTable_MEAN_ERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        epicenters = get_epicenters(df)
        for epi in epicenters:
            idx = (df['lat_epi'] == epi.y) & (df['lon_epi'] == epi.x)
            subset_df = df.loc[idx]
            ctx = get_ctx(subset_df)
            tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
            chk(SgobbaEtAl2020(cluster=0), tags, ctx, subset_df, sigma="0")

    def test_NON_ERGODIC(self):
        fname = 'ValidationTable_MEAN_NERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, sigma="0")

    def test_SIGMAtot(self):
        fname = 'ValidationTable_STD_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, sigma="1")

    def test_tau(self):
        fname = 'ValidationTable_STD_tau.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, sigma="2")

    def test_phi(self):
        fname = 'ValidationTable_STD_phi.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, sigma="3")
