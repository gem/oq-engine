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

CDIR = os.path.dirname(__file__)
# Verification Tables
DATA_FOLDER = os.path.join(CDIR, 'data', 'SEA20')
# Residuals
DATA_FOLDER2 = os.path.join(CDIR, '..', '..', 'gsim', 'sgobba_2020')


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


def get_epicenters(df):
    epicenters = df[['lon_epi', 'lat_epi']].to_numpy()
    return np.unique(epicenters, axis=0)


def chk(gmm, tags, ctx, subset_df, what):
    imts = [PGA(), SA(period=0.2), SA(period=0.50251256281407),
            SA(period=1.0), SA(period=2.0)]
    stdt = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
            const.StdDev.INTRA_EVENT]
    # Compute and check results for the NON ergodic model
    for i, imt in enumerate(imts):
        tag = tags[i]
        mean, stddevs = gmm.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        if what == "sig":  # checking the Total stddev
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = stddevs[0]  # in ln
        elif what == "tau":  # checking tau
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = stddevs[1]  # in ln
        elif what == "phi":  # checking phi
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
    for lon, lat in epicenters:
        idx = np.where((df['lat_epi'] == lat) & (df['lon_epi'] == lon))
        subset_df = df.loc[idx]
        flag_b = subset_df['flag_bedrock']
        if sum(flag_b) > 0:
            bedrock = [0, 1]
        else:
            bedrock = [0]
        for i in bedrock:
            idx = np.where((df['lat_epi'] == lat) &
                           (df['lon_epi'] == lon) &
                           (df['flag_bedrock'] == i))
            subset_df = df.loc[idx]
            idx2 = np.where((df2['Ev_lat'] == lat) & (df2['Ev_lon'] == lon))[0]
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
        for lon, lat in get_epicenters(df):
            idx = (df['lat_epi'] == lat) & (df['lon_epi'] == lon)
            subset_df = df.loc[idx]
            ctx = get_ctx(subset_df)
            tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
            chk(SgobbaEtAl2020(cluster=0), tags, ctx, subset_df, what="mea")

    def test_NON_ERGODIC(self):
        fname = 'ValidationTable_MEAN_NERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, what="mea")

    def test_WHATtot(self):
        fname = 'ValidationTable_STD_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, what="sig")

    def test_tau(self):
        fname = 'ValidationTable_STD_tau.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, what="tau")

    def test_phi(self):
        fname = 'ValidationTable_STD_phi.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, ctx, subset_df in gen_data(df):
            chk(gmm, tags, ctx, subset_df, what="phi")
