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
from openquake.hazardlib import contexts
from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib.gsim.sgobba_2020 import SgobbaEtAl2020

CDIR = os.path.dirname(__file__)
# Verification Tables
DATA_FOLDER = os.path.join(CDIR, 'data', 'SEA20')
# Residuals
DATA_FOLDER2 = os.path.join(CDIR, '..', '..', 'gsim', 'sgobba_2020')

IMTS = ['PGA', 'SA(0.2)', 'SA(0.50251256281407)', 'SA(1.0)', 'SA(2.0']


def get_epicenters(df):
    epicenters = df[['lon_epi', 'lat_epi']].to_numpy()
    return np.unique(epicenters, axis=0)


def chk(gmm, tags, subset_df, what):
    cmaker = contexts.simple_cmaker([gmm], IMTS)
    ctx = new_ctx(cmaker, len(subset_df),
                  lons=subset_df.lon_sites.to_numpy(),
                  lats=subset_df.lat_sites.to_numpy())
    ctx.vs30 = 800.
    ctx.rjb = ctx.rrup = subset_df.dist_jb
    ctx.mag = subset_df.rup_mag
    ctx.hypo_lon = subset_df.lon_epi
    ctx.hypo_lat = subset_df.lat_epi
    mea, sig, tau, phi = cmaker.get_mean_stds([ctx])

    # Compute and check results for the NON ergodic model
    for m, imt in enumerate(IMTS):
        tag = tags[m]
        if what == "sig":  # checking the Total stddev
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = sig[0, m]  # in ln
        elif what == "tau":  # checking tau
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = tau[0, m]  # in ln
        elif what == "phi":  # checking phi
            expected = np.log(10.0**subset_df[tag].to_numpy())
            # in VerifTable are in log10
            computed = phi[0, m]  # in ln
        else:  # checking the mean
            expected = subset_df[tag].to_numpy()  # Verif Table in g unit
            computed = np.exp(mea[0, m])  # in OQ are computed in g Units in ln
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
            print('event_id: %s' % ev_id)
            print('flag_bedrock: %s' % i)
            gmm = SgobbaEtAl2020(event_id=ev_id, site=True, bedrock=i > 0)
            yield gmm, subset_df


class Sgobba2020Test(unittest.TestCase):

    def test_ERGODIC(self):
        fname = 'ValidationTable_MEAN_ERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        for lon, lat in get_epicenters(df):
            idx = (df['lat_epi'] == lat) & (df['lon_epi'] == lon)
            subset_df = df.loc[idx]
            tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
            chk(SgobbaEtAl2020(cluster=0), tags, subset_df, what="mea")

    def test_NON_ERGODIC(self):
        fname = 'ValidationTable_MEAN_NERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
        for gmm, subset_df in gen_data(df):
            chk(gmm, tags, subset_df, what="mea")

    def test_sigmatot(self):
        fname = 'ValidationTable_STD_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, subset_df in gen_data(df):
            chk(gmm, tags, subset_df, what="sig")

    def test_tau(self):
        fname = 'ValidationTable_STD_tau.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, subset_df in gen_data(df):
            chk(gmm, tags, subset_df, what="tau")

    def test_phi(self):
        fname = 'ValidationTable_STD_phi.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
        for gmm, subset_df in gen_data(df):
            chk(gmm, tags, subset_df, what="phi")
