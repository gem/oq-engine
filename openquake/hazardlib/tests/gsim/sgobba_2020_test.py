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
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.geo import Point
# from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.sgobba_2020 import SgobbaEtAl2020
from openquake.hazardlib.contexts import DistancesContext

# folder Verif Tables
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'SEA20')
# folder Residuals
DATA_FOLDER2 = os.path.join(os.path.dirname('../../'), 'gsim', 'sgobba_2020')


class Sgobba2020Test(unittest.TestCase):

    def test_ERGODIC(self):
        # Read dataframe with information
        fname = 'ValidationTable_MEAN_ERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        # Check number of events
        epicenters = []
        for idx, row in df.iterrows():
            x = Point(row.lon_epi, row.lat_epi)
            if x not in epicenters:
                epicenters.append(x)
        # For each event check Validation
        for i in range(len(epicenters)):
            LON = epicenters[i].x
            LAT = epicenters[i].y
            idx = np.where((df['lat_epi'] == LAT) & (df['lon_epi'] == LON))
            subset_df = df.loc[idx]
            # Get parameters
            locs = []
            rjb = []
            for idx, row in subset_df.iterrows():
                locs.append(Point(row.lon_sites, row.lat_sites))
                rjb.append(row.dist_jb)
            # Create the sites
            sites = Dummy.get_site_collection(len(rjb), vs30=800., location=locs)
            # Create distance and rupture contexts
            rup = Dummy.get_rupture(mag=row.rup_mag, ev_lat=row.lat_epi, ev_lon=row.lon_epi)
            dists = DistancesContext()
            dists.rjb = np.array(rjb)
            # Instantiate the GMM
            gmmref = SgobbaEtAl2020(cluster=0)
            # Computes results for the non-ergodic model
            periods = [PGA(), SA(period=0.2), SA(period=0.50251256281407), SA(period=1.0), SA(period=2.0)]
            tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
            stdt = [const.StdDev.TOTAL]
            # Compute and check results for the ergodic model
            for i in range(len(periods)):
                imt = periods[i]
                tag = tags[i]
                mr, stdr = gmmref.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
                expected_ref = subset_df[tag].to_numpy()  # Verif Table in g unit
                computed_ref = np.exp(mr)  # in OQ are computed in g Units in ln
                np.testing.assert_allclose(computed_ref, expected_ref, rtol=1e-5)

    def test_NON_ERGODIC(self):

        # Read dataframe with information
        fname = 'ValidationTable_MEAN_NERG_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        # Read dataframe with information
        fname2 = 'event.csv'
        df2 = pd.read_csv(os.path.join(DATA_FOLDER2, fname2), dtype={'id': str})
        # Check number of events
        epicenters = []
        for idx, row in df.iterrows():
            x = Point(row.lon_epi, row.lat_epi)
            if x not in epicenters:
                epicenters.append(x)
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
                idx = np.where((df['lat_epi'] == LAT) & (df['lon_epi'] == LON) & (df['flag_bedrock'] == i))
                subset_df = df.loc[idx]
                try:
                    idx2 = np.where((df2['Ev_lat'] == LAT) & (df2['Ev_lon'] == LON))[0][0]
                    ev_id = df2['id'][idx2]
                except:
                    ev_id = None
                print('event_id: '+str(ev_id))
                print('flag_bedrock: '+str(i))
                # Get parameters
                locs = []
                rjb = []
                bedrock = False
                for idx, row in subset_df.iterrows():
                    locs.append(Point(row.lon_sites, row.lat_sites))
                    rjb.append(row.dist_jb)
                    if row.flag_bedrock == 1:
                        bedrock = True
                # Create the sites
                sites = Dummy.get_site_collection(len(rjb), vs30=800., location=locs)
                # bed_flag = Dummy.get_site_collection(len(rjb), flag=bedrock)
                # Create distance and rupture contexts
                rup = Dummy.get_rupture(mag=row.rup_mag, ev_lat=row.lat_epi, ev_lon=row.lon_epi)
                dists = DistancesContext()
                dists.rjb = np.array(rjb)
                # Instantiate the GMM
                if i == 0:
                    gmm = SgobbaEtAl2020(event_id=ev_id, site=sites, bedrock=False)  # cluster=None because cluster has to be automatically detected
                else:
                    gmm = SgobbaEtAl2020(event_id=ev_id, site=sites, bedrock=True)
                # Computes results for the non-ergodic model
                periods = [PGA(), SA(period=0.2), SA(period=0.50251256281407), SA(period=1.0), SA(period=2.0)]
                tags = ['gmm_PGA', 'gmm_SA02', 'gmm_SA05', 'gmm_SA10', 'gmm_SA20']
                stdt = [const.StdDev.TOTAL]
                # Compute and check results for the NON ergodic model
                for i in range(len(periods)):
                    imt = periods[i]
                    tag = tags[i]
                    mean, stdr = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
                    expected = subset_df[tag].to_numpy()  # Verif Table in g unit
                    computed = np.exp(mean)  # in OQ are computed in g Units in ln
                    np.testing.assert_allclose(computed, expected, rtol=1e-5)

    def test_SIGMA(self):

        # Read dataframe with information
        fname = 'ValidationTable_STD_full.csv'
        df = pd.read_csv(os.path.join(DATA_FOLDER, fname))
        # Read dataframe with information
        fname2 = 'event.csv'
        df2 = pd.read_csv(os.path.join(DATA_FOLDER2, fname2), dtype={'id': str})
        # Check number of events
        epicenters = []
        for idx, row in df.iterrows():
            x = Point(row.lon_epi, row.lat_epi)
            if x not in epicenters:
                epicenters.append(x)
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
                idx = np.where((df['lat_epi'] == LAT) & (df['lon_epi'] == LON) & (df['flag_bedrock'] == i))
                subset_df = df.loc[idx]
                try:
                    idx2 = np.where((df2['Ev_lat'] == LAT) & (df2['Ev_lon'] == LON))[0][0]
                    ev_id = df2['id'][idx2]
                except:
                    ev_id = None
                print('event_id: '+str(ev_id))
                print('flag_bedrock: '+str(i))
                # Get parameters
                locs = []
                rjb = []
                bedrock = False
                for idx, row in subset_df.iterrows():
                    locs.append(Point(row.lon_sites, row.lat_sites))
                    rjb.append(row.dist_jb)
                    if row.flag_bedrock == 1:
                        bedrock = True
                # Create the sites
                sites = Dummy.get_site_collection(len(rjb), vs30=800., location=locs)
                # bed_flag = Dummy.get_site_collection(len(rjb), flag=bedrock)
                # Create distance and rupture contexts
                rup = Dummy.get_rupture(mag=row.rup_mag, ev_lat=row.lat_epi, ev_lon=row.lon_epi)
                dists = DistancesContext()
                dists.rjb = np.array(rjb)
                # Instantiate the GMM
                if i == 0:
                    gmm = SgobbaEtAl2020(event_id=ev_id, site=sites, bedrock=False)  # cluster=None because cluster has to be automatically detected
                else:
                    gmm = SgobbaEtAl2020(event_id=ev_id, site=sites, bedrock=True)
                # Computes results for the non-ergodic model
                periods = [PGA(), SA(period=0.2), SA(period=0.50251256281407), SA(period=1.0), SA(period=2.0)]
                tags = ['PGA', 'SA02', 'SA05', 'SA10', 'SA20']
                stdt = [const.StdDev.TOTAL]
                # Compute and check results for the NON ergodic model
                for i in range(len(periods)):
                    imt = periods[i]
                    tag = tags[i]
                    mean, stdr = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
                    expected = np.log(10.0**subset_df[tag].to_numpy())  # in VerifTable are in log10
                    computed = stdr  # in ln
                    np.testing.assert_allclose(computed, expected, rtol=1e-5)
# THE END!
